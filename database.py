import sqlite3
from pathlib import Path
from utils import month_range
DEFAULT_CATEGORIES = {
    "expense": [
        "Food", "Transport", "Airtime & Data", "Rent", "Utilities",
        "School Fees", "Health", "Entertainment", "Shopping", "Other",
    ],
    "income": ["Allowance", "Salary", "Freelance", "Gift", "Other"],
}
class Database:
    """All the SQL lives in this class. The rest of the app never writes SQL."""
    def __init__(self, path):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.seed_categories()
    def create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE,
                kind TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
                UNIQUE (name, kind)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT NOT NULL,
                kind     TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
                category TEXT NOT NULL,
                amount   INTEGER NOT NULL CHECK (amount > 0),
                note     TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS budgets (
                category     TEXT PRIMARY KEY,
                limit_amount INTEGER NOT NULL CHECK (limit_amount > 0)
            );
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date
                ON transactions (date);
            """
        )
        self.conn.commit()
    def seed_categories(self):
        """Fill the category list the very first time the app runs."""
        count = self.conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if count:
            return
        rows = [
            (name, kind)
            for kind, names in DEFAULT_CATEGORIES.items()
            for name in names
        ]
        self.conn.executemany(
            "INSERT INTO categories (name, kind) VALUES (?, ?)", rows
        )
        self.conn.commit()
    # ---------- settings ----------
    def get_setting(self, key, default=""):
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else default
    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()
    # ---------- categories ----------
    def category_names(self, kind):
        rows = self.conn.execute(
            "SELECT name FROM categories WHERE kind=? ORDER BY name", (kind,)
        ).fetchall()
        return [row["name"] for row in rows]
    def all_category_names(self):
        rows = self.conn.execute(
            "SELECT DISTINCT name FROM categories ORDER BY name"
        ).fetchall()
        return [row["name"] for row in rows]
    def add_category(self, name, kind):
        """Returns False when that category already exists."""
        try:
            self.conn.execute(
                "INSERT INTO categories (name, kind) VALUES (?, ?)", (name, kind)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    def delete_category(self, name, kind):
        self.conn.execute(
            "DELETE FROM categories WHERE name=? AND kind=?", (name, kind)
        )
        if kind == "expense":
            self.conn.execute("DELETE FROM budgets WHERE category=?", (name,))
        self.conn.commit()
    # ---------- transactions ----------
    def add_transaction(self, date, kind, category, amount, note=""):
        cur = self.conn.execute(
            "INSERT INTO transactions (date, kind, category, amount, note)"
            " VALUES (?, ?, ?, ?, ?)",
            (date, kind, category, amount, note),
        )
        self.conn.commit()
        return cur.lastrowid
    def add_many(self, rows):
        """Insert many (date, kind, category, amount, note) tuples at once."""
        self.conn.executemany(
            "INSERT INTO transactions (date, kind, category, amount, note)"
            " VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        self.conn.commit()
    def update_transaction(self, tx_id, date, kind, category, amount, note=""):
        self.conn.execute(
            "UPDATE transactions SET date=?, kind=?, category=?, amount=?,"
            " note=? WHERE id=?",
            (date, kind, category, amount, note, tx_id),
        )
        self.conn.commit()
    def delete_transaction(self, tx_id):
        self.conn.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
        self.conn.commit()
    def clear_transactions(self):
        self.conn.execute("DELETE FROM transactions")
        self.conn.commit()
    def get_transaction(self, tx_id):
        return self.conn.execute(
            "SELECT * FROM transactions WHERE id=?", (tx_id,)
        ).fetchone()
    def find_transactions(
        self, start=None, end=None, kind=None, category=None, text=""
    ):
        """Every argument is optional. Only the ones you give are used."""
        conditions, params = [], []
        if start:
            conditions.append("date >= ?")
            params.append(start)
        if end:
            conditions.append("date <= ?")
            params.append(end)
        if kind:
            conditions.append("kind = ?")
            params.append(kind)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if text:
            conditions.append("(note LIKE ? OR category LIKE ?)")
            params += [f"%{text}%", f"%{text}%"]
        where = " AND ".join(conditions) or "1=1"
        return self.conn.execute(
            f"SELECT * FROM transactions WHERE {where} ORDER BY date DESC, id DESC",
            params,
        ).fetchall()
    # ---------- totals for the dashboard and reports ----------
    def totals(self, start, end):
        """Returns (income, expense) between two dates, in pesewas."""
        row = self.conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN kind='income' THEN amount END), 0) AS income,
                COALESCE(SUM(CASE WHEN kind='expense' THEN amount END), 0) AS expense
            FROM transactions
            WHERE date BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
        return row["income"], row["expense"]
    def spending_by_category(self, start, end):
        """Returns [(category, total), ...] with the biggest total first."""
        rows = self.conn.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE kind = 'expense' AND date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (start, end),
        ).fetchall()
        return [(row["category"], row["total"]) for row in rows]
    def monthly_totals(self, months):
        """Returns [(month, income, expense), ...] for a list of 'YYYY-MM'."""
        result = []
        for month in months:
            income, expense = self.totals(*month_range(month))
            result.append((month, income, expense))
        return result
    # ---------- budgets ----------
    def set_budget(self, category, limit_amount):
        self.conn.execute(
            "INSERT OR REPLACE INTO budgets (category, limit_amount) VALUES (?, ?)",
            (category, limit_amount),
        )
        self.conn.commit()
    def remove_budget(self, category):
        self.conn.execute("DELETE FROM budgets WHERE category=?", (category,))
        self.conn.commit()
    def budgets(self):
        """Returns {category: monthly limit in pesewas}."""
        rows = self.conn.execute(
            "SELECT category, limit_amount FROM budgets ORDER BY category"
        ).fetchall()
        return {row["category"]: row["limit_amount"] for row in rows}
    # ---------- backup ----------
    def backup_to(self, destination):
        """Save a safe copy of the whole database to another file."""
        target = sqlite3.connect(destination)
        with target:
            self.conn.backup(target)
        target.close()
