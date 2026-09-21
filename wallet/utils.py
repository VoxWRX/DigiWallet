import calendar
from datetime import date, datetime

MONTHS = list(calendar.month_name)[1:]


def today_str():
    return date.today().isoformat()


def parse_date(s):
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def parse_float(s):
    try:
        return float(str(s).strip().replace(",", "."))
    except (ValueError, TypeError):
        return None


def fmt_money(v, sym=""):
    s = f"{v:,.2f}"
    if not sym:
        return s
    return f"{sym}{s}" if len(sym) <= 2 else f"{s} {sym}"


def fmt_compact(v):
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1_000_000:
        return f"{sign}{a / 1_000_000:.1f}M"
    if a >= 1_000:
        return f"{sign}{a / 1_000:.1f}k"
    return f"{sign}{a:.0f}"


def month_name(y, m):
    return f"{calendar.month_name[m]} {y}"


def add_months(d, n):
    mm = d.month - 1 + n
    y = d.year + mm // 12
    m = mm % 12 + 1
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))


def center(win, w, h):
    x = (win.winfo_screenwidth() - w) // 2
    y = max(0, (win.winfo_screenheight() - h) // 3)
    win.geometry(f"{w}x{h}+{x}+{y}")


def safe_grab(win):
    def _grab():
        try:
            pass # win.focus_force()
            pass # win.grab_set()
        except Exception:
            pass
    win.after(120, _grab)


def clear(frame):
    for w in frame.winfo_children():
        w.destroy()