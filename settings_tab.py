import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sample_data
from utils import today_str
class SettingsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.currency_var = tk.StringVar(value=app.currency)
        self.lists = {}     # category kind -> its Listbox
        self.new_vars = {}  # category kind -> text typed in its "add" box
        self.build_currency()
        self.build_categories()
        self.build_data_tools()
    def build_currency(self):
        box = ttk.LabelFrame(self, text="Currency", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Code or symbol shown next to amounts:").pack(side="left")
        ttk.Entry(box, textvariable=self.currency_var, width=8).pack(
            side="left", padx=8
        )
        ttk.Button(box, text="Save", command=self.save_currency).pack(side="left")
    def build_categories(self):
        holder = ttk.Frame(self)
        holder.pack(fill="both", expand=True, pady=10)
        holder.rowconfigure(0, weight=1)
        for column, kind in enumerate(("expense", "income")):
            holder.columnconfigure(column, weight=1, uniform="categories")
            title = f"{kind.capitalize()} categories"
            box = ttk.LabelFrame(holder, text=title, padding=10)
            left_gap = 0 if column == 0 else 10
            box.grid(row=0, column=column, sticky="nsew", padx=(left_gap, 0))
            listbox = tk.Listbox(box, height=8, exportselection=False)
            listbox.pack(fill="both", expand=True)
            row = ttk.Frame(box)
            row.pack(fill="x", pady=(8, 0))
            var = tk.StringVar()
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            # k=kind remembers the right kind for each button (see the notes)
            ttk.Button(
                row, text="Add", command=lambda k=kind: self.add_category(k)
            ).pack(side="left", padx=6)
            ttk.Button(
                row, text="Delete selected",
                command=lambda k=kind: self.delete_category(k),
            ).pack(side="left")
            self.lists[kind] = listbox
            self.new_vars[kind] = var
    def build_data_tools(self):
        box = ttk.LabelFrame(self, text="Your data", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text=f"Everything is stored in: {self.app.db.path}").pack(
            anchor="w"
        )
        buttons = ttk.Frame(box)
        buttons.pack(anchor="w", pady=(8, 0))
        ttk.Button(buttons, text="Back up database...", command=self.backup).pack(
            side="left"
        )
        ttk.Button(buttons, text="Load sample data", command=self.load_sample).pack(
            side="left", padx=8
        )
        ttk.Button(
            buttons, text="Delete all transactions", command=self.clear_all
        ).pack(side="left")
    def refresh(self):
        for kind, listbox in self.lists.items():
            listbox.delete(0, "end")
            for name in self.app.db.category_names(kind):
                listbox.insert("end", name)
    def save_currency(self):
        value = self.currency_var.get().strip()
        if not value:
            messagebox.showwarning("Currency", "Type a code such as GHS or USD.")
            return
        self.app.currency = value
        self.app.db.set_setting("currency", value)
        self.app.set_status(f"Currency changed to {value}.")
        self.app.data_changed()
    def add_category(self, kind):
        name = self.new_vars[kind].get().strip()
        if not name:
            return
        if self.app.db.add_category(name, kind):
            self.new_vars[kind].set("")
            self.app.data_changed()
        else:
            messagebox.showinfo(
                "Already there", f"{name} is already an {kind} category."
            )
    def delete_category(self, kind):
        selected = self.lists[kind].curselection()
        if not selected:
            messagebox.showinfo("Nothing selected", "Select a category first.")
            return
        name = self.lists[kind].get(selected[0])
        message = (
            f"Delete '{name}'?\n\nOld transactions keep their category name. "
            "A budget for this category is removed."
        )
        if messagebox.askyesno("Delete category", message):
            self.app.db.delete_category(name, kind)
            self.app.data_changed()
    def backup(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            initialfile=f"finance_backup_{today_str()}.db",
            filetypes=[("Database files", "*.db")],
        )
        if path:
            self.app.db.backup_to(path)
            messagebox.showinfo("Backup complete", f"A copy was saved to:\n{path}")
    def load_sample(self):
        message = (
            "Add four months of example transactions and budgets so you can "
            "try the charts?\n\nRemove them later with 'Delete all transactions'."
        )
        if messagebox.askyesno("Load sample data", message):
            sample_data.load(self.app.db)
            self.app.set_status("Sample data loaded.")
            self.app.data_changed()
    def clear_all(self):
        message = (
            "This permanently deletes EVERY transaction. Budgets and categories "
            "are kept.\n\nContinue?"
        )
        if messagebox.askyesno("Delete all transactions", message, icon="warning"):
            self.app.db.clear_transactions()
            self.app.set_status("All transactions deleted.")
            self.app.data_changed()
