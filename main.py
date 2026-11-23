import tkinter as tk
from pathlib import Path
from tkinter import ttk
from budgets import BudgetsTab
from dashboard import DashboardTab
from database import Database
from reports import ReportsTab
from settings_tab import SettingsTab
from transactions import TransactionsTab
from utils import COLORS, format_money
DB_FILE = Path(__file__).with_name("finance.db")
# The order of this list is the order of the tabs
TABS = [
    ("Dashboard", DashboardTab),
    ("Transactions", TransactionsTab),
    ("Budgets", BudgetsTab),
    ("Reports", ReportsTab),
    ("Settings", SettingsTab),
]
class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.db = Database(DB_FILE)
        self.currency = self.db.get_setting("currency", "GHS")
        root.title("Smart Personal Finance Manager")
        root.geometry("1150x740")
        root.minsize(1000, 640)
        self.setup_styles()
        # The status bar is packed first so it always stays at the bottom
        self.status_var = tk.StringVar(value=f"Data file: {DB_FILE}")
        ttk.Label(root, textvariable=self.status_var, padding=(12, 4)).pack(
            side="bottom", fill="x"
        )
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.tabs = []
        for name, tab_class in TABS:
            tab = tab_class(self.notebook, self)
            self.notebook.add(tab, text=f"  {name}  ")
            self.tabs.append(tab)
        self.notebook.bind(
            "<<NotebookTabChanged>>", lambda event: self.refresh_current()
        )
        self.refresh_current()
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        bg, card = COLORS["bg"], COLORS["card"]
        for name in ("TFrame", "TLabel", "TLabelframe", "TNotebook", "TRadiobutton"):
            style.configure(name, background=bg)
        style.configure(
            "TLabelframe.Label", background=bg, font=("Segoe UI", 10, "bold")
        )
        style.configure("TNotebook.Tab", padding=(14, 7), font=("Segoe UI", 10))
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 15, "bold"))
        # Dashboard cards
        style.configure("Card.TFrame", background=card, relief="solid", borderwidth=1)
        style.configure(
            "CardTitle.TLabel", background=card, foreground=COLORS["muted"]
        )
        style.configure(
            "CardValue.TLabel", background=card, font=("Segoe UI", 18, "bold")
        )
        style.configure("Income.CardValue.TLabel", foreground=COLORS["income"])
        style.configure("Expense.CardValue.TLabel", foreground=COLORS["expense"])
        # Budget progress bars: green, orange and red
        levels = (("Good", "#2E7D32"), ("Warn", "#EF6C00"), ("Over", "#C62828"))
        for name, color in levels:
            style.configure(
                f"{name}.Horizontal.TProgressbar",
                background=color, troughcolor="#DDDDDD", thickness=18,
            )
        self.root.configure(background=bg)
    def money(self, amount):
        """Format an amount (in pesewas) with the chosen currency."""
        return format_money(amount, self.currency)
    def set_status(self, text):
        self.status_var.set(text)
    def data_changed(self):
        """Call this after saving anything. Only the visible tab is redrawn;
        the other tabs refresh themselves when you click on them."""
        self.refresh_current()
    def refresh_current(self):
        current = self.notebook.select()
        if current:  # empty while no tabs have been added yet
            self.root.nametowidget(current).refresh()
if __name__ == "__main__":
    root = tk.Tk()
    FinanceApp(root)
    root.mainloop()
