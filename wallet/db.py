"""SQLite storage layer. All data lives in ~/.digital_wallet/wallet.db"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from .utils import add_months, parse_date

DATA_DIR = Path.home() / ".digital_wallet"
DB_PATH = DATA_DIR / "wallet.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    base_currency TEXT DEFAULT 'MAD',
    theme_mode TEXT DEFAULT 'light',
    theme_accent TEXT DEFAULT 'blue',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    UNIQUE (user_id, code),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('expense','income','savings')),
    icon TEXT DEFAULT '🧾',
    color TEXT DEFAULT '#64748B',
    UNIQUE (user_id, name, type),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE (user_id, name),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    target_amount REAL DEFAULT 0,
    deadline TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('expense','income','savings')),
    amount REAL NOT NULL,
    orig_amount REAL,
    orig_currency TEXT,
    category_id INTEGER,
    project_id INTEGER,
    description TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions (user_id, date);
CREATE TABLE IF NOT EXISTS transaction_tags (
    transaction_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (transaction_id, tag_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS recurrent_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('expense','income','savings')),
    amount REAL NOT NULL,
    category_id INTEGER,
    project_id INTEGER,
    description TEXT DEFAULT '',
    frequency TEXT NOT NULL CHECK (frequency IN ('daily','weekly','monthly','yearly')),
    next_date TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""

DEFAULT_CURRENCIES = [
    ("MAD", "Moroccan Dirham", "DH"), ("USD", "US Dollar", "$"),
    ("EUR", "Euro", "€"), ("GBP", "British Pound", "£"),
    ("CHF", "Swiss Franc", "CHF"), ("CAD", "Canadian Dollar", "C$"),
    ("AUD", "Australian Dollar", "A$"), ("JPY", "Japanese Yen", "¥"),
    ("CNY", "Chinese Yuan", "CN¥"), ("AED", "UAE Dirham", "AED"),
    ("SAR", "Saudi Riyal", "SAR"), ("EGP", "Egyptian Pound", "E£"),
    ("DZD", "Algerian Dinar", "DA"), ("TND", "Tunisian Dinar", "DT"),
]

DEFAULT_CATEGORIES = [
    ("Food & Dining", "expense", "🍔", "#F97316"),
    ("Transport", "expense", "🚌", "#0EA5E9"),
    ("Housing & Rent", "expense", "🏠", "#8B5CF6"),
    ("Groceries", "expense", "🛒", "#22C55E"),
    ("Shopping", "expense", "🛍️", "#EC4899"),
    ("Health", "expense", "💊", "#EF4444"),
    ("Entertainment", "expense", "🎬", "#A855F7"),
    ("Bills & Utilities", "expense", "💡", "#EAB308"),
    ("Education", "expense", "📚", "#3B82F6"),
    ("Travel", "expense", "✈️", "#14B8A6"),
    ("Other", "expense", "🧾", "#94A3B8"),
    ("Salary", "income", "💼", "#22C55E"),
    ("Freelance", "income", "💻", "#3B82F6"),
    ("Investments", "income", "📈", "#0D9488"),
    ("Gifts", "income", "🎁", "#F472B6"),
    ("Other", "income", "🧾", "#94A3B8"),
    ("General Savings", "savings", "🏦", "#0EA5E9"),
    ("Emergency Fund", "savings", "🚨", "#EF4444"),
    ("Goal Saving", "savings", "🎯", "#8B5CF6"),
]

_conn = None


def conn():
    global _conn
    if _conn is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def init_db():
    conn().executescript(SCHEMA)


def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


# ------------------------------------------------------------------ users
def create_user(username, pw_hash, salt, display_name, base_currency):
    c = conn()
    cur = c.execute(
        "INSERT INTO users (username, password_hash, salt, display_name, base_currency)"
        " VALUES (?,?,?,?,?)", (username, pw_hash, salt, display_name, base_currency))
    uid = cur.lastrowid
    c.executemany("INSERT INTO currencies (user_id, code, name, symbol) VALUES (?,?,?,?)",
                  [(uid, code, name, sym) for code, name, sym in DEFAULT_CURRENCIES])
    c.executemany("INSERT INTO categories (user_id, name, type, icon, color) VALUES (?,?,?,?,?)",
                  [(uid, n, t, i, col) for n, t, i, col in DEFAULT_CATEGORIES])
    c.commit()
    return uid


def get_user_by_username(username):
    r = conn().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(r) if r else None


def get_user_by_id(uid):
    r = conn().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    return dict(r) if r else None


_USER_FIELDS = {"display_name", "base_currency", "theme_mode", "theme_accent",
                "password_hash", "salt"}


def update_user(uid, **fields):
    fields = {k: v for k, v in fields.items() if k in _USER_FIELDS and v is not None}
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    conn().execute(f"UPDATE users SET {sets} WHERE id=?", (*fields.values(), uid))
    conn().commit()


# ------------------------------------------------------------- currencies
def list_currencies(uid):
    return _rows(conn().execute("SELECT * FROM currencies WHERE user_id=? ORDER BY code", (uid,)))


def get_currency(uid, code):
    r = conn().execute("SELECT * FROM currencies WHERE user_id=? AND code=?", (uid, code)).fetchone()
    return dict(r) if r else None


def add_currency(uid, code, name, symbol):
    conn().execute("INSERT INTO currencies (user_id, code, name, symbol) VALUES (?,?,?,?)",
                   (uid, code, name, symbol))
    conn().commit()


def update_currency(uid, cid, code, name, symbol):
    conn().execute("UPDATE currencies SET code=?, name=?, symbol=? WHERE id=? AND user_id=?",
                   (code, name, symbol, cid, uid))
    conn().commit()


def delete_currency(uid, cid):
    conn().execute("DELETE FROM currencies WHERE id=? AND user_id=?", (cid, uid))
    conn().commit()


# ------------------------------------------------------------- categories
def list_categories(uid, ctype=None):
    q, args = "SELECT * FROM categories WHERE user_id=?", [uid]
    if ctype:
        q += " AND type=?"
        args.append(ctype)
    return _rows(conn().execute(q + " ORDER BY type, name", args))


def add_category(uid, name, ctype, icon, color):
    cur = conn().execute(
        "INSERT INTO categories (user_id,name,type,icon,color) VALUES (?,?,?,?,?)",
        (uid, name, ctype, icon, color))
    conn().commit()
    return cur.lastrowid


def update_category(uid, cid, name, ctype, icon, color):
    conn().execute("UPDATE categories SET name=?, type=?, icon=?, color=? WHERE id=? AND user_id=?",
                   (name, ctype, icon, color, cid, uid))
    conn().commit()


def delete_category(uid, cid):
    conn().execute("DELETE FROM categories WHERE id=? AND user_id=?", (cid, uid))
    conn().commit()


# ------------------------------------------------------------------- tags
def list_tags(uid):
    return _rows(conn().execute("SELECT * FROM tags WHERE user_id=? ORDER BY name", (uid,)))


def add_tag(uid, name):
    try:
        cur = conn().execute("INSERT INTO tags (user_id, name) VALUES (?,?)", (uid, name))
        conn().commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def delete_tag(uid, tid):
    conn().execute("DELETE FROM tags WHERE id=? AND user_id=?", (tid, uid))
    conn().commit()


# ----------------------------------------------------------- transactions
def add_tx(uid, date_str, ttype, amount, category_id, project_id, description, notes,
           orig_amount=None, orig_currency=None):
    cur = conn().execute(
        "INSERT INTO transactions (user_id, date, type, amount, orig_amount, orig_currency,"
        " category_id, project_id, description, notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (uid, date_str, ttype, amount, orig_amount, orig_currency, category_id,
         project_id, description, notes))
    conn().commit()
    return cur.lastrowid


def update_tx(uid, tid, date_str, ttype, amount, category_id, project_id, description,
              notes, orig_amount, orig_currency):
    conn().execute(
        "UPDATE transactions SET date=?, type=?, amount=?, orig_amount=?, orig_currency=?,"
        " category_id=?, project_id=?, description=?, notes=? WHERE id=? AND user_id=?",
        (date_str, ttype, amount, orig_amount, orig_currency, category_id, project_id,
         description, notes, tid, uid))
    conn().commit()


def delete_tx(uid, tid):
    conn().execute("DELETE FROM transactions WHERE id=? AND user_id=?", (tid, uid))
    conn().commit()


def get_tx(uid, tid):
    r = conn().execute(
        "SELECT t.*, c.name AS cat_name FROM transactions t"
        " LEFT JOIN categories c ON c.id=t.category_id WHERE t.id=? AND t.user_id=?",
        (tid, uid)).fetchone()
    return dict(r) if r else None


def query_tx(uid, search="", ttype=None, category_id=None, tag_id=None, dfrom=None, dto=None):
    q = ("SELECT t.*, c.name AS cat_name, c.icon AS cat_icon FROM transactions t"
         " LEFT JOIN categories c ON c.id = t.category_id WHERE t.user_id = ?")
    args = [uid]
    if ttype:
        q += " AND t.type=?"
        args.append(ttype)
    if category_id:
        q += " AND t.category_id=?"
        args.append(category_id)
    if dfrom:
        q += " AND t.date>=?"
        args.append(dfrom)
    if dto:
        q += " AND t.date<=?"
        args.append(dto)
    if search:
        q += " AND (t.description LIKE ? OR t.notes LIKE ? OR c.name LIKE ?)"
        args += [f"%{search}%"] * 3
    if tag_id:
        q += " AND EXISTS (SELECT 1 FROM transaction_tags tt WHERE tt.transaction_id=t.id AND tt.tag_id=?)"
        args.append(tag_id)
    q += " ORDER BY t.date DESC, t.id DESC"
    return _rows(conn().execute(q, args))


def set_tx_tags(tid, tag_ids):
    c = conn()
    c.execute("DELETE FROM transaction_tags WHERE transaction_id=?", (tid,))
    c.executemany("INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id) VALUES (?,?)",
                  [(tid, t) for t in tag_ids])
    c.commit()


def tx_tag_ids(tid):
    return [r["tag_id"] for r in conn().execute(
        "SELECT tag_id FROM transaction_tags WHERE transaction_id=?", (tid,))]


def tx_tag_names(tid):
    r = conn().execute(
        "SELECT GROUP_CONCAT(tg.name, ', ') AS names FROM transaction_tags tt"
        " JOIN tags tg ON tg.id=tt.tag_id WHERE tt.transaction_id=?", (tid,)).fetchone()
    return r["names"] or ""


# -------------------------------------------------------------- analytics
def totals_between(uid, dfrom, dto):
    rows = conn().execute(
        "SELECT type, SUM(amount) s, COUNT(*) n FROM transactions"
        " WHERE user_id=? AND date>=? AND date<=? GROUP BY type", (uid, dfrom, dto))
    out = {"income": 0.0, "expense": 0.0, "savings": 0.0, "count": 0}
    for r in rows:
        out[r["type"]] = r["s"] or 0.0
        out["count"] += r["n"]
    return out


def category_breakdown(uid, ttype, dfrom, dto):
    return _rows(conn().execute(
        "SELECT COALESCE(c.name,'Uncategorized') AS name, COALESCE(c.color,'#64748B') AS color,"
        " SUM(t.amount) AS total, COUNT(*) AS n FROM transactions t"
        " LEFT JOIN categories c ON c.id=t.category_id"
        " WHERE t.user_id=? AND t.type=? AND t.date>=? AND t.date<=?"
        " GROUP BY c.id ORDER BY total DESC", (uid, ttype, dfrom, dto)))


def day_totals(uid, dfrom, dto):
    rows = conn().execute(
        "SELECT date, type, SUM(amount) s FROM transactions WHERE user_id=? AND date>=? AND date<=?"
        " GROUP BY date, type", (uid, dfrom, dto))
    out = {}
    for r in rows:
        out.setdefault(r["date"], {})[r["type"]] = r["s"] or 0.0
    return out


def daily_series(uid, year, month):
    import calendar as _cal
    days = _cal.monthrange(year, month)[1]
    rows = conn().execute(
        "SELECT CAST(strftime('%d', date) AS INTEGER) d, type, SUM(amount) s FROM transactions"
        " WHERE user_id=? AND strftime('%Y',date)=? AND strftime('%m',date)=?"
        " GROUP BY d, type", (uid, str(year), f"{month:02d}"))
    out = [{"income": 0.0, "expense": 0.0, "savings": 0.0} for _ in range(days + 1)]
    for r in rows:
        out[r["d"]][r["type"]] = r["s"] or 0.0
    return out


def monthly_series(uid, year):
    rows = conn().execute(
        "SELECT CAST(strftime('%m', date) AS INTEGER) m, type, SUM(amount) s FROM transactions"
        " WHERE user_id=? AND strftime('%Y',date)=? GROUP BY m, type", (uid, str(year)))
    out = [{"income": 0.0, "expense": 0.0, "savings": 0.0} for _ in range(12)]
    for r in rows:
        out[r["m"] - 1][r["type"]] = r["s"] or 0.0
    return out


def available_years(uid):
    rows = conn().execute(
        "SELECT DISTINCT strftime('%Y', date) y FROM transactions WHERE user_id=? ORDER BY y DESC",
        (uid,))
    years = [int(r["y"]) for r in rows]
    if date.today().year not in years:
        years.append(date.today().year)
    return sorted(set(years), reverse=True)


# -------------------------------------------------------------- recurring
def _advance(d, freq):
    if freq == "daily":
        return d + timedelta(days=1)
    if freq == "weekly":
        return d + timedelta(days=7)
    if freq == "monthly":
        return add_months(d, 1)
    return add_months(d, 12)


def list_rules(uid, active=None):
    q, args = "SELECT * FROM recurrent_rules WHERE user_id=?", [uid]
    if active is not None:
        q += " AND active=?"
        args.append(1 if active else 0)
    return _rows(conn().execute(q + " ORDER BY next_date", args))


def add_rule(uid, ttype, amount, category_id, description, frequency, next_date):
    cur = conn().execute(
        "INSERT INTO recurrent_rules (user_id,type,amount,category_id,description,frequency,next_date)"
        " VALUES (?,?,?,?,?,?,?)", (uid, ttype, amount, category_id, description, frequency, next_date))
    conn().commit()
    return cur.lastrowid


def update_rule(uid, rid, ttype, amount, category_id, description, frequency, next_date):
    conn().execute(
        "UPDATE recurrent_rules SET type=?, amount=?, category_id=?, description=?, frequency=?,"
        " next_date=? WHERE id=? AND user_id=?",
        (ttype, amount, category_id, description, frequency, next_date, rid, uid))
    conn().commit()


def set_rule_active(uid, rid, active):
    conn().execute("UPDATE recurrent_rules SET active=? WHERE id=? AND user_id=?",
                   (1 if active else 0, rid, uid))
    conn().commit()


def delete_rule(uid, rid):
    conn().execute("DELETE FROM recurrent_rules WHERE id=? AND user_id=?", (rid, uid))
    conn().commit()


def apply_recurrent(uid):
    """Record all due occurrences of active rules. Returns number created."""
    c = conn()
    rules = _rows(c.execute("SELECT * FROM recurrent_rules WHERE user_id=? AND active=1", (uid,)))
    today = date.today()
    created = 0
    for rule in rules:
        d = parse_date(rule["next_date"])
        if not d:
            continue
        steps = 0
        while d <= today and steps < 400:
            c.execute(
                "INSERT INTO transactions (user_id,date,type,amount,category_id,project_id,"
                "description,notes) VALUES (?,?,?,?,?,?,?,'Recurring')",
                (uid, d.isoformat(), rule["type"], rule["amount"], rule["category_id"],
                 rule["project_id"], rule["description"]))
            created += 1
            steps += 1
            d = _advance(d, rule["frequency"])
        if steps >= 400:
            d = today
        c.execute("UPDATE recurrent_rules SET next_date=? WHERE id=?", (d.isoformat(), rule["id"]))
    c.commit()
    return created


def upcoming_rules(uid, within_days=60):
    limit = (date.today() + timedelta(days=within_days)).isoformat()
    return _rows(conn().execute(
        "SELECT * FROM recurrent_rules WHERE user_id=? AND active=1 AND next_date<=? ORDER BY next_date",
        (uid, limit)))


# --------------------------------------------------------------- projects
def list_projects(uid):
    return _rows(conn().execute("SELECT * FROM projects WHERE user_id=? ORDER BY name", (uid,)))


def project_stats(uid, pid):
    r = conn().execute(
        "SELECT COALESCE(SUM(CASE WHEN type='savings' THEN amount END),0) saved,"
        " COALESCE(SUM(CASE WHEN type='expense' THEN amount END),0) spent"
        " FROM transactions WHERE user_id=? AND project_id=?", (uid, pid)).fetchone()
    return dict(r)


def add_project(uid, name, target, deadline):
    cur = conn().execute(
        "INSERT INTO projects (user_id,name,target_amount,deadline) VALUES (?,?,?,?)",
        (uid, name, target, deadline))
    conn().commit()
    return cur.lastrowid


def update_project(uid, pid, name, target, deadline):
    conn().execute("UPDATE projects SET name=?, target_amount=?, deadline=? WHERE id=? AND user_id=?",
                   (name, target, deadline, pid, uid))
    conn().commit()


def delete_project(uid, pid):
    conn().execute("DELETE FROM projects WHERE id=? AND user_id=?", (pid, uid))
    conn().commit()