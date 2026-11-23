import tkinter as tk
from tkinter import messagebox, ttk
from utils import (
    COLORS, budget_status, current_month, month_options, month_range, to_minor,
)
class BudgetsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.month_var = tk.StringVar(value=current_month())
        self.cat_var = tk.StringVar()
        self.limit_var = tk.StringVar()
        self.total_var = tk.StringVar()
        self.build_header()
        # The progress bars are created fresh every time in refresh()
        self.rows_frame = ttk.Frame(self)
        self.rows_frame.pack(fill="both", expand=True, pady=12)
        self.build_form()
    def build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Monthly budgets", style="Heading.TLabel").pack(
            side="left"
        )
        box = ttk.Combobox(
            header, textvariable=self.month_var, values=month_options(),
            width=10, state="readonly",
        )
        box.pack(side="right")
        ttk.Label(header, text="Month:").pack(side="right", padx=(0, 6))
        box.bind("<<ComboboxSelected>>", lambda event: self.refresh())
        ttk.Label(self, textvariable=self.total_var).pack(anchor="w", pady=(6, 0))
    def build_form(self):
        box = ttk.LabelFrame(self, text="Set a monthly budget", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Category").grid(row=0, column=0, sticky="w")
        self.cat_box = ttk.Combobox(
            box, textvariable=self.cat_var, width=22, state="readonly"
        )
        self.cat_box.grid(row=1, column=0, padx=(0, 14))
        ttk.Label(box, text="Monthly limit").grid(row=0, column=1, sticky="w")
        ttk.Entry(box, textvariable=self.limit_var, width=14).grid(
            row=1, column=1, padx=(0, 14)
        )
        ttk.Button(box, text="Save budget", command=self.save_budget).grid(
            row=1, column=2, padx=(0, 6)
        )
        ttk.Button(box, text="Remove budget", command=self.remove_budget).grid(
            row=1, column=3
        )
        ttk.Label(
            box,
            text="Saving a budget for a category that already has one replaces it.",
            foreground=COLORS["muted"],
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
    def refresh(self):
        db = self.app.db
        names = db.category_names("expense")
        self.cat_box["values"] = names
        if self.cat_var.get() not in names:
            self.cat_var.set(names[0] if names else "")
        start, end = month_range(self.month_var.get())
        spent = dict(db.spending_by_category(start, end))
        budgets = db.budgets()
        # Remove the old rows, then draw one row per budget
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
        if not budgets:
            ttk.Label(
                self.rows_frame,
                text="No budgets yet. Pick a category below and set a monthly limit.",
            ).pack(anchor="w")
        total_limit = total_used = 0
        for index, (category, limit) in enumerate(budgets.items()):
            used = spent.get(category, 0)
            self.add_row(index, category, used, limit)
            total_limit += limit
            total_used += used
        if budgets:
            self.total_var.set(
                f"Budgeted {self.app.money(total_limit)}     "
                f"Spent {self.app.money(total_used)}     "
                f"Remaining {self.app.money(total_limit - total_used)}"
            )
        else:
            self.total_var.set("")
    def add_row(self, index, category, used, limit):
        status = budget_status(used, limit)
        percent = used / limit * 100
        ttk.Label(self.rows_frame, text=category, width=18).grid(
            row=index, column=0, sticky="w", pady=7
        )
        ttk.Progressbar(
            self.rows_frame, maximum=100, value=min(percent, 100),
            style=f"{status}.Horizontal.TProgressbar",
        ).grid(row=index, column=1, sticky="ew", padx=12)
        text = f"{self.app.money(used)} of {self.app.money(limit)}  ({percent:.0f}%)"
        if used > limit:
            text += f"  over by {self.app.money(used - limit)}"
        ttk.Label(self.rows_frame, text=text).grid(row=index, column=2, sticky="w")
        self.rows_frame.columnconfigure(1, weight=1)
    def save_budget(self):
        category = self.cat_var.get()
        if not category:
            messagebox.showwarning("Budget", "Choose a category.")
            return
        try:
            limit = to_minor(self.limit_var.get())
        except ValueError as error:
            messagebox.showwarning("Budget", str(error))
            return
        self.app.db.set_budget(category, limit)
        self.limit_var.set("")
        self.app.set_status(f"Budget saved for {category}.")
        self.app.data_changed()
    def remove_budget(self):
        category = self.cat_var.get()
        if category in self.app.db.budgets():
            self.app.db.remove_budget(category)
            self.app.set_status(f"Budget removed for {category}.")
            self.app.data_changed()
        else:
            messagebox.showinfo("Budget", f"{category} has no budget to remove.")
