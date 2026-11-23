import calendar
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
DATE_FORMAT = "%Y-%m-%d"
COLORS = {
    "bg": "#F4F6F8",
    "card": "#FFFFFF",
    "income": "#2E7D32",
    "expense": "#C62828",
    "accent": "#1565C0",
    "muted": "#666666",
}
def today_str():
    return date.today().strftime(DATE_FORMAT)
def current_month():
    """The current month as text, for example '2026-11'."""
    return today_str()[:7]
def previous_months(month, count):
    """The `count` months ending at `month`, oldest first."""
    year, number = int(month[:4]), int(month[5:7])
    months = []
    for _ in range(count):
        months.append(f"{year}-{number:02d}")
        number -= 1
        if number == 0:
            year, number = year - 1, 12
    return months[::-1]
def month_options(count=24):
    """Months for the dropdown boxes, newest first."""
    return previous_months(current_month(), count)[::-1]
def month_range(month):
    """'2026-11' -> ('2026-11-01', '2026-11-30')"""
    year, number = int(month[:4]), int(month[5:7])
    last_day = calendar.monthrange(year, number)[1]
    return f"{month}-01", f"{month}-{last_day:02d}"
def check_date(text):
    """Return the date as 'YYYY-MM-DD', or raise ValueError with a clear message."""
    try:
        return datetime.strptime(text.strip(), DATE_FORMAT).strftime(DATE_FORMAT)
    except ValueError:
        raise ValueError("Dates must look like 2026-11-15 (year-month-day).") from None
def to_minor(text):
    """Turn '45.50' into 4550 (pesewas). Money is stored as whole numbers."""
    try:
        value = Decimal(text.replace(",", "").strip())
    except InvalidOperation:
        raise ValueError("Amount must be a number, for example 45.50.") from None
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
def format_money(amount, currency):
    """Turn 123456 into 'GHS 1,234.56'."""
    sign = "-" if amount < 0 else ""
    return f"{sign}{currency} {abs(amount) / 100:,.2f}"
def budget_status(used, limit):
    """Name of the progress bar style to use: Good, Warn or Over."""
    ratio = used / limit
    if ratio > 1:
        return "Over"
    if ratio >= 0.8:
        return "Warn"
    return "Good"
