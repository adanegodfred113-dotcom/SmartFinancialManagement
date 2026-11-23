import calendar
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from utils import (
    COLORS, budget_status, current_month, month_options, month_range,
    previous_months,
)
class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.month_var = tk.StringVar(value=current_month())
        self.card_vars = {}
        self.build_header()
        self.build_cards()
        self.build_alerts()  # packed before the charts so it is never squeezed out
        self.build_charts()
    def build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Overview", style="Heading.TLabel").pack(side="left")
        box = ttk.Combobox(
            header, textvariable=self.month_var, values=month_options(),
            width=10, state="readonly",
        )
        box.pack(side="right")
        ttk.Label(header, text="Month:").pack(side="right", padx=(0, 6))
        box.bind("<<ComboboxSelected>>", lambda event: self.refresh())
    def build_cards(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=12)
        cards = (
            ("income", "Income", "Income.CardValue.TLabel"),
            ("expense", "Expenses", "Expense.CardValue.TLabel"),
            ("balance", "Net balance", "CardValue.TLabel"),
            ("rate", "Savings rate", "CardValue.TLabel"),
        )
        for index, (key, title, value_style) in enumerate(cards):
            row.columnconfigure(index, weight=1, uniform="cards")
            card = ttk.Frame(row, style="Card.TFrame", padding=14)
            left_gap = 0 if index == 0 else 10
            card.grid(row=0, column=index, sticky="nsew", padx=(left_gap, 0))
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
            var = tk.StringVar(value="-")
            ttk.Label(card, textvariable=var, style=value_style).pack(
                anchor="w", pady=(4, 0)
            )
            self.card_vars[key] = var
    def build_charts(self):
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1, uniform="charts")
        area.columnconfigure(1, weight=1, uniform="charts")
        self.pie_fig = Figure(figsize=(4.8, 3.0), dpi=100)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=area)
        self.pie_canvas.get_tk_widget().grid(
            row=0, column=0, sticky="nsew", padx=(0, 6)
        )
        self.bar_fig = Figure(figsize=(4.8, 3.0), dpi=100)
        self.bar_canvas = FigureCanvasTkAgg(self.bar_fig, master=area)
        self.bar_canvas.get_tk_widget().grid(
            row=0, column=1, sticky="nsew", padx=(6, 0)
        )
    def build_alerts(self):
        box = ttk.LabelFrame(self, text="Budget alerts", padding=8)
        box.pack(side="bottom", fill="x", pady=(10, 0))
        self.alert_label = ttk.Label(box, text="", justify="left")
        self.alert_label.pack(anchor="w")
    def refresh(self):
        month = self.month_var.get()
        start, end = month_range(month)
        income, expense = self.app.db.totals(start, end)
        balance = income - expense
        self.card_vars["income"].set(self.app.money(income))
        self.card_vars["expense"].set(self.app.money(expense))
        self.card_vars["balance"].set(self.app.money(balance))
        rate = f"{balance / income * 100:.0f}%" if income else "n/a"
        self.card_vars["rate"].set(rate)
        self.draw_pie(start, end)
        self.draw_bars(month)
        self.update_alerts(start, end)
    def draw_pie(self, start, end):
        data = self.app.db.spending_by_category(start, end)
        self.pie_fig.clear()
        ax = self.pie_fig.add_subplot(111)
        ax.set_title("Spending by category")
        if not data:
            ax.text(0.5, 0.5, "No spending recorded", ha="center", va="center",
                    color=COLORS["muted"])
            ax.axis("off")
        else:
            if len(data) > 6:  # keep the chart readable: top 6 plus the rest
                rest = sum(total for _, total in data[6:])
                data = data[:6] + [("Everything else", rest)]
            ax.pie(
                [total / 100 for _, total in data],
                labels=[name for name, _ in data],
                autopct="%1.0f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={"width": 0.45, "edgecolor": "white"},
            )
        self.pie_fig.tight_layout()
        self.pie_canvas.draw_idle()
    def draw_bars(self, month):
        months = previous_months(month, 6)
        rows = self.app.db.monthly_totals(months)
        labels = [calendar.month_abbr[int(m[5:7])] for m in months]
        positions = list(range(len(months)))
        width = 0.38
        self.bar_fig.clear()
        ax = self.bar_fig.add_subplot(111)
        ax.bar([p - width / 2 for p in positions], [r[1] / 100 for r in rows],
               width, label="Income", color=COLORS["income"])
        ax.bar([p + width / 2 for p in positions], [r[2] / 100 for r in rows],
               width, label="Expenses", color=COLORS["expense"])
        ax.set_xticks(positions)
        ax.set_xticklabels(labels)
        ax.set_title("Income and expenses, last 6 months")
        ax.legend(frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        self.bar_fig.tight_layout()
        self.bar_canvas.draw_idle()
    def update_alerts(self, start, end):
        budgets = self.app.db.budgets()
        spent = dict(self.app.db.spending_by_category(start, end))
        lines = []
        for category, limit in budgets.items():
            used = spent.get(category, 0)
            status = budget_status(used, limit)
            if status == "Over":
                over = self.app.money(used - limit)
                lines.append(f"Over budget: {category} by {over}")
            elif status == "Warn":
                percent = f"{used / limit:.0%}"
                lines.append(f"Close to the limit: {category} ({percent} used)")
        if not budgets:
            text = "No budgets set yet. Add some in the Budgets tab."
        else:
            text = "\n".join(lines) or "All budgets are on track."
        self.alert_label.config(text=text)
