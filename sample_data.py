import random
from datetime import date
from utils import current_month, previous_months
# category, description, lowest and highest amount (pesewas), times per month
EXPENSES = [
    ("Food", "Lunch", 1500, 4500, 9),
    ("Food", "Groceries", 6000, 15000, 2),
    ("Transport", "Trotro fare", 300, 1200, 10),
    ("Airtime & Data", "Data bundle", 2000, 5000, 2),
    ("Utilities", "Electricity credit", 3000, 8000, 1),
    ("Entertainment", "Movies and outings", 3000, 9000, 2),
    ("Shopping", "Clothes", 6000, 20000, 1),
    ("Health", "Pharmacy", 2000, 7000, 1),
]
# monthly limits in pesewas
BUDGETS = {
    "Food": 70000,
    "Transport": 15000,
    "Airtime & Data": 10000,
    "Entertainment": 10000,
    "Shopping": 20000,
}
def load(db):
    """Add four months of believable example data."""
    rng = random.Random(42)  # a fixed seed gives the same data every time
    this_month = current_month()
    rows = []
    for month in previous_months(this_month, 4):
        # In the current month do not create transactions in the future
        last_day = date.today().day if month == this_month else 28
        rows.append((f"{month}-01", "income", "Allowance",
                     rng.randrange(90000, 110000, 5000), "Monthly allowance"))
        if rng.random() < 0.6:
            day = rng.randint(1, last_day)
            rows.append((f"{month}-{day:02d}", "income", "Freelance",
                         rng.randrange(15000, 40000, 500), "Flyer design"))
        for category, note, low, high, times in EXPENSES:
            for _ in range(times):
                day = rng.randint(1, last_day)
                amount = rng.randrange(low, high, 50)
                rows.append((f"{month}-{day:02d}", "expense", category, amount, note))
    db.add_many(rows)
    for category, limit in BUDGETS.items():
        db.set_budget(category, limit)
