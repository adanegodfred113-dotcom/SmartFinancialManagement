import tkinter as tk
from tkinter import messagebox, ttk
from utils import (
    COLORS, check_date, current_month, month_options, month_range, to_minor,
    today_str,
)
class TransactionsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.current_id = None  # id of the transaction loaded in the form
        # Variables for the filter bar
        self.month_var = tk.StringVar(value=current_month())
        self.type_var = tk.StringVar(value="All")
        self.filter_cat_var = tk.StringVar(value="All")
        self.search_var = tk.StringVar()
        self.summary_var = tk.StringVar()
        # Variables for the form at the bottom
        self.date_var = tk.StringVar(value=today_str())
        self.kind_var = tk.StringVar(value="expense")
        self.cat_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.note_var = tk.StringVar()
        self.build_filters()
        self.build_table()
        self.build_form()
    def build_filters(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x")
        ttk.Label(bar, text="Month").pack(side="left")
        month_box = ttk.Combobox(
            bar, textvariable=self.month_var, values=["All"] + month_options(),
            width=10, state="readonly",
        )
        month_box.pack(side="left", padx=(5, 14))
        ttk.Label(bar, text="Type").pack(side="left")
        type_box = ttk.Combobox(
            bar, textvariable=self.type_var, values=["All", "Income", "Expense"],
            width=9, state="readonly",
        )
        type_box.pack(side="left", padx=(5, 14))
        ttk.Label(bar, text="Category").pack(side="left")
        self.filter_cat_box = ttk.Combobox(
            bar, textvariable=self.filter_cat_var, width=16, state="readonly"
        )
        self.filter_cat_box.pack(side="left", padx=(5, 14))
        ttk.Label(bar, text="Search").pack(side="left")
        ttk.Entry(bar, textvariable=self.search_var, width=22).pack(
            side="left", padx=5
        )
        for box in (month_box, type_box, self.filter_cat_box):
            box.bind("<<ComboboxSelected>>", lambda event: self.refresh())
        self.search_var.trace_add("write", lambda *args: self.refresh())
        ttk.Label(
            self, textvariable=self.summary_var, font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(10, 0))
    def build_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, pady=8)
        columns = ("date", "kind", "category", "note", "amount")
        self.tree = ttk.Treeview(
            frame, columns=columns, show="headings", selectmode="browse"
        )
        for name, label, width, anchor in (
            ("date", "Date", 100, "w"),
            ("kind", "Type", 80, "w"),
            ("category", "Category", 150, "w"),
            ("note", "Description", 340, "w"),
            ("amount", "Amount", 140, "e"),
        ):
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, anchor=anchor)
        # Income rows are drawn in green and expense rows in red
        self.tree.tag_configure("income", foreground=COLORS["income"])
        self.tree.tag_configure("expense", foreground=COLORS["expense"])
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
    def build_form(self):
        box = ttk.LabelFrame(self, text="Transaction details", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.date_var, width=14).grid(
            row=1, column=0, sticky="w", padx=(0, 14)
        )
        ttk.Label(box, text="Type").grid(row=0, column=1, sticky="w")
        kinds = ttk.Frame(box)
        kinds.grid(row=1, column=1, sticky="w", padx=(0, 14))
        for text, value in (("Expense", "expense"), ("Income", "income")):
            ttk.Radiobutton(
                kinds, text=text, value=value, variable=self.kind_var,
                command=self.update_form_categories,
            ).pack(side="left", padx=(0, 8))
        ttk.Label(box, text="Category").grid(row=0, column=2, sticky="w")
        self.cat_box = ttk.Combobox(
            box, textvariable=self.cat_var, width=18, state="readonly"
        )
        self.cat_box.grid(row=1, column=2, sticky="w", padx=(0, 14))
        ttk.Label(box, text="Amount").grid(row=0, column=3, sticky="w")
        ttk.Entry(box, textvariable=self.amount_var, width=14).grid(
            row=1, column=3, sticky="w", padx=(0, 14)
        )
        ttk.Label(box, text="Description (optional)").grid(
            row=0, column=4, sticky="w"
        )
        ttk.Entry(box, textvariable=self.note_var).grid(row=1, column=4, sticky="ew")
        box.columnconfigure(4, weight=1)
        buttons = ttk.Frame(box)
        buttons.grid(row=2, column=0, columnspan=5, sticky="w", pady=(10, 0))
        ttk.Button(buttons, text="Add", command=self.add_transaction).pack(
            side="left"
        )
        ttk.Button(buttons, text="Save changes", command=self.save_changes).pack(
            side="left", padx=6
        )
        ttk.Button(buttons, text="Delete", command=self.delete_selected).pack(
            side="left"
        )
        ttk.Button(buttons, text="Clear form", command=self.clear_form).pack(
            side="left", padx=6
        )
    def update_form_categories(self):
        """Show the categories that belong to the chosen type."""
        names = self.app.db.category_names(self.kind_var.get())
        self.cat_box["values"] = names
        if self.cat_var.get() not in names:
            self.cat_var.set(names[0] if names else "")
    def read_form(self):
        """Check the form. Returns the values to save, or None if something is wrong."""
        try:
            date_text = check_date(self.date_var.get())
            amount = to_minor(self.amount_var.get())
        except ValueError as error:
            messagebox.showwarning("Please check the form", str(error))
            return None
        if not self.cat_var.get():
            messagebox.showwarning("Please check the form", "Choose a category.")
            return None
        note = self.note_var.get().strip()
        return date_text, self.kind_var.get(), self.cat_var.get(), amount, note
    def add_transaction(self):
        values = self.read_form()
        if values is None:
            return
        self.app.db.add_transaction(*values)
        self.finish("Transaction added.")
    def save_changes(self):
        if self.current_id is None:
            messagebox.showinfo(
                "Nothing selected", "Click a transaction in the table first."
            )
            return
        values = self.read_form()
        if values is None:
            return
        self.app.db.update_transaction(self.current_id, *values)
        self.finish("Transaction updated.")
    def delete_selected(self):
        if self.current_id is None:
            messagebox.showinfo(
                "Nothing selected", "Click a transaction in the table first."
            )
            return
        if messagebox.askyesno("Delete", "Delete this transaction permanently?"):
            self.app.db.delete_transaction(self.current_id)
            self.finish("Transaction deleted.")
    def finish(self, message):
        """Everything that happens after a successful add, update or delete."""
        self.clear_form()
        self.app.set_status(message)
        self.app.data_changed()
    def clear_form(self):
        self.current_id = None
        self.tree.selection_remove(*self.tree.selection())
        self.date_var.set(today_str())
        self.amount_var.set("")
        self.note_var.set("")
    def on_select(self, event):
        """Load the clicked transaction into the form so it can be edited."""
        selected = self.tree.selection()
        if not selected:
            return
        row = self.app.db.get_transaction(int(selected[0]))
        if row is None:
            return
        self.current_id = row["id"]
        self.date_var.set(row["date"])
        self.kind_var.set(row["kind"])
        self.update_form_categories()
        self.cat_var.set(row["category"])
        self.amount_var.set(f"{row['amount'] / 100:.2f}")
        self.note_var.set(row["note"])
    def refresh(self):
        db = self.app.db
        # Category dropdowns can change in Settings, so rebuild them every time
        names = ["All"] + db.all_category_names()
        self.filter_cat_box["values"] = names
        if self.filter_cat_var.get() not in names:
            self.filter_cat_var.set("All")
        self.update_form_categories()
        # Translate the filter boxes into arguments for the database
        month = self.month_var.get()
        start, end = (None, None) if month == "All" else month_range(month)
        kind = self.type_var.get().lower()
        category = self.filter_cat_var.get()
        rows = db.find_transactions(
            start,
            end,
            None if kind == "all" else kind,
            None if category == "All" else category,
            self.search_var.get().strip(),
        )
        self.tree.delete(*self.tree.get_children())
        income = expense = 0
        for row in rows:
            if row["kind"] == "income":
                income += row["amount"]
            else:
                expense += row["amount"]
            self.tree.insert(
                "", "end", iid=str(row["id"]), tags=(row["kind"],),
                values=(
                    row["date"], row["kind"].capitalize(), row["category"],
                    row["note"], self.app.money(row["amount"]),
                ),
            )
        self.summary_var.set(
            f"{len(rows)} transactions     Income {self.app.money(income)}"
            f"     Expenses {self.app.money(expense)}"
            f"     Net {self.app.money(income - expense)}"
        )
