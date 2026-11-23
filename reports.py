import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from utils import (
    COLORS, check_date, current_month, format_money, month_range,
    previous_months, today_str,
)
def build_report(db, start, end, currency):
    """Turn the numbers for a date range into a readable text report."""
    def money(amount):
        return format_money(amount, currency)
    income, expense = db.totals(start, end)
    net = income - expense
    rate = f"{net / income * 100:.1f}%" if income else "n/a"
    rows = db.find_transactions(start, end)
    lines = [
        f"Report: {start} to {end}",
        "=" * 46,
        f"{'Income':<16}{money(income):>30}",
        f"{'Expenses':<16}{money(expense):>30}",
        f"{'Net balance':<16}{money(net):>30}",
        f"{'Savings rate':<16}{rate:>30}",
        f"{'Transactions':<16}{len(rows):>30}",
        "",
        "Spending by category",
        "-" * 46,
    ]
    spending = db.spending_by_category(start, end)
    for category, total in spending:
        share = total / expense * 100
        lines.append(f"{category:<20}{money(total):>18}{share:>7.1f}%")
    if not spending:
        lines.append("No expenses in this period.")
    lines += ["", "Five largest expenses", "-" * 46]
    expenses = [row for row in rows if row["kind"] == "expense"]
    biggest = sorted(expenses, key=lambda row: row["amount"], reverse=True)[:5]
    for row in biggest:
        label = (row["note"] or row["category"])[:20]
        lines.append(f"{row['date']}  {label:<20}{money(row['amount']):>14}")
    if not expenses:
        lines.append("None.")
    return "\n".join(lines)
class ReportsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.period = None  # (start, end) of the report that is on screen
        start, end = month_range(current_month())
        self.start_var = tk.StringVar(value=start)
        self.end_var = tk.StringVar(value=end)
        self.build_controls()
        self.build_export_bar()  # packed before the body so it stays at the bottom
        self.build_body()
    def build_controls(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x")
        ttk.Label(bar, text="From").pack(side="left")
        ttk.Entry(bar, textvariable=self.start_var, width=12).pack(
            side="left", padx=(5, 12)
        )
        ttk.Label(bar, text="To").pack(side="left")
        ttk.Entry(bar, textvariable=self.end_var, width=12).pack(
            side="left", padx=(5, 12)
        )
        ttk.Button(bar, text="Generate", command=self.generate).pack(side="left")
        ttk.Button(
            bar, text="This month", command=lambda: self.quick("month")
        ).pack(side="left", padx=(20, 4))
        ttk.Button(
            bar, text="Last month", command=lambda: self.quick("last")
        ).pack(side="left", padx=4)
        ttk.Button(
            bar, text="This year", command=lambda: self.quick("year")
        ).pack(side="left", padx=4)
    def build_export_bar(self):
        bar = ttk.Frame(self)
        bar.pack(side="bottom", fill="x")
        ttk.Button(
            bar, text="Export transactions to CSV", command=self.export_csv
        ).pack(side="left")
        ttk.Button(bar, text="Save chart as image", command=self.save_chart).pack(
            side="left", padx=8
        )
    def build_body(self):
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, pady=10)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self.text = tk.Text(
            body, width=50, wrap="none", font=("Consolas", 10), state="disabled",
            relief="solid", borderwidth=1, padx=10, pady=10,
        )
        self.text.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=body)
        self.canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew")
    def quick(self, period):
        """Fill in the dates for a ready-made period and build the report."""
        this_month = current_month()
        if period == "month":
            start, end = month_range(this_month)
        elif period == "last":
            start, end = month_range(previous_months(this_month, 2)[0])
        else:
            year = today_str()[:4]
            start, end = f"{year}-01-01", f"{year}-12-31"
        self.start_var.set(start)
        self.end_var.set(end)
        self.generate()
    def refresh(self):
        self.generate(quiet=True)
    def generate(self, quiet=False):
        try:
            start = check_date(self.start_var.get())
            end = check_date(self.end_var.get())
            if start > end:
                raise ValueError("The start date must not be after the end date.")
        except ValueError as error:
            if not quiet:
                messagebox.showwarning("Check the dates", str(error))
            return
        self.period = (start, end)
        report = build_report(self.app.db, start, end, self.app.currency)
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", report)
        self.text.config(state="disabled")
        self.draw_chart(start, end)
    def draw_chart(self, start, end):
        data = self.app.db.spending_by_category(start, end)
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_title("Spending by category")
        if data:
            names = [name for name, _ in data][::-1]  # biggest bar on top
            values = [total / 100 for _, total in data][::-1]
            ax.barh(names, values, color=COLORS["accent"])
            ax.set_xlabel(f"Amount ({self.app.currency})")
            ax.spines[["top", "right"]].set_visible(False)
        else:
            ax.text(0.5, 0.5, "No spending in this period", ha="center",
                    va="center", color=COLORS["muted"])
            ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw_idle()
    def export_csv(self):
        if self.period is None:
            return
        start, end = self.period
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"transactions_{start}_to_{end}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        rows = self.app.db.find_transactions(start, end)
        rows = sorted(rows, key=lambda row: (row["date"], row["id"]))
        # utf-8-sig lets Excel read the file correctly
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["Date", "Type", "Category", "Description",
                 f"Amount ({self.app.currency})"]
            )
            for row in rows:
                writer.writerow([
                    row["date"], row["kind"], row["category"], row["note"],
                    f"{row['amount'] / 100:.2f}",
                ])
        messagebox.showinfo("Exported", f"{len(rows)} transactions saved to:\n{path}")
    def save_chart(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile="spending_chart.png",
            filetypes=[("PNG image", "*.png")],
        )
        if path:
            self.fig.savefig(path, dpi=150)
            messagebox.showinfo("Saved", f"The chart was saved to:\n{path}")
