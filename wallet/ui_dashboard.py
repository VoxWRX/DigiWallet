import calendar as cal
from datetime import date, timedelta

import tkinter.messagebox as mb
import customtkinter as ctk

from . import db
from .themes import THEME
from .utils import clear, fmt_compact, fmt_money, month_name, parse_date, safe_grab
from .widgets import Page, StatCard, card
from .ui_transaction import TransactionDialog

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SIGN = {"income": "+", "expense": "−", "savings": "◆"}
COLOR_KEY = {"income": "pos", "expense": "neg", "savings": "accent"}


class DashboardPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        t = date.today()
        self.year, self.month = t.year, t.month
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        c = THEME.c
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        head.grid_columnconfigure(4, weight=1)
        ctk.CTkButton(head, text="‹", width=36, fg_color=c("card"), hover_color=c("card2"),
                      text_color=c("text"), border_width=1, border_color=c("border"),
                      command=self._prev_month).grid(row=0, column=0, padx=(0, 6))
        self.title_lbl = ctk.CTkLabel(head, text="", width=170,
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.grid(row=0, column=1)
        ctk.CTkButton(head, text="›", width=36, fg_color=c("card"), hover_color=c("card2"),
                      text_color=c("text"), border_width=1, border_color=c("border"),
                      command=self._next_month).grid(row=0, column=2, padx=(6, 10))
        ctk.CTkButton(head, text="Today", width=70, fg_color=c("card"), hover_color=c("card2"),
                      text_color=c("text"), border_width=1, border_color=c("border"),
                      command=self._today).grid(row=0, column=3, sticky="w")
        ctk.CTkButton(head, text="＋  Add transaction", fg_color=c("accent"),
                      hover_color=c("accent_hover"),
                      command=self._add).grid(row=0, column=4, sticky="e")

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)
        self.card_income = StatCard(stats, "Income")
        self.card_income.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.card_expense = StatCard(stats, "Expenses")
        self.card_expense.grid(row=0, column=1, sticky="ew", padx=10)
        self.card_savings = StatCard(stats, "Savings")
        self.card_savings.grid(row=0, column=2, sticky="ew", padx=10)
        self.card_net = StatCard(stats, "Net")
        self.card_net.grid(row=0, column=3, sticky="ew", padx=(10, 0))

        self.cal_card = card(self)
        self.cal_card.grid(row=2, column=0, sticky="nsew", padx=24, pady=(4, 8))
        self.cal_card.grid_columnconfigure(tuple(range(7)), weight=1)
        self.cal_card.grid_rowconfigure(1, weight=1)
        for i, wd in enumerate(WEEKDAYS):
            ctk.CTkLabel(self.cal_card, text=wd, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c("muted")).grid(row=0, column=i, padx=6, pady=(10, 4), sticky="w")
        self.grid_frame = ctk.CTkFrame(self.cal_card, fg_color="transparent")
        self.grid_frame.grid(row=1, column=0, columnspan=7, sticky="nsew", padx=10, pady=(0, 10))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 18))
        bottom.grid_columnconfigure((0, 1), weight=1)
        self.recur_card = card(bottom)
        self.recur_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.proj_card = card(bottom)
        self.proj_card.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        self.render()

    # ------------------------------------------------------------ month nav
    def _prev_month(self):
        m, y = self.month - 1, self.year
        if m == 0:
            m, y = 12, y - 1
        self.month, self.year = m, y
        self.render()

    def _next_month(self):
        m, y = self.month + 1, self.year
        if m == 13:
            m, y = 1, y + 1
        self.month, self.year = m, y
        self.render()

    def _today(self):
        t = date.today()
        self.year, self.month = t.year, t.month
        self.render()

    def _add(self):
        dlg = TransactionDialog(self.app)
        self.wait_window(dlg)
        if dlg.saved:
            self.render()

    # ------------------------------------------------------------ render
    def render(self):
        uid, c, sym = self.app.uid, THEME.c, self.app.sym
        self.title_lbl.configure(text=month_name(self.year, self.month))

        first = date(self.year, self.month, 1)
        last = date(self.year, self.month, cal.monthrange(self.year, self.month)[1])
        totals = db.totals_between(uid, first.isoformat(), last.isoformat())
        net = totals["income"] - totals["expense"] - totals["savings"]
        self.card_income.set(fmt_money(totals["income"], sym), c("pos"))
        self.card_expense.set(fmt_money(totals["expense"], sym), c("neg"))
        self.card_savings.set(fmt_money(totals["savings"], sym), c("accent"))
        self.card_net.set(fmt_money(net, sym), c("pos") if net >= 0 else c("neg"))

        clear(self.grid_frame)
        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1)
        for i in range(6):
            self.grid_frame.grid_rowconfigure(i, weight=1)

        days = db.day_totals(uid, first.isoformat(), last.isoformat())
        start = first - timedelta(days=first.weekday())
        today_iso = date.today().isoformat()
        for idx in range(42):
            d = start + timedelta(days=idx)
            row, col = divmod(idx, 7)
            in_month = d.month == self.month
            iso = d.isoformat()
            info = days.get(iso, {})
            base_fg = c("card") if in_month else "transparent"

            cell = ctk.CTkFrame(self.grid_frame, corner_radius=8, fg_color=base_fg,
                                border_width=2 if iso == today_iso else 0,
                                border_color=c("accent"), cursor="hand2")
            cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            cell.grid_columnconfigure(0, weight=1)

            day_lbl = ctk.CTkLabel(cell, text=str(d.day), anchor="e",
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=c("text") if in_month else c("muted"))
            day_lbl.pack(fill="x", padx=8, pady=(5, 0))
            widgets = [cell, day_lbl]
            lines = []
            if info.get("income"):
                lines.append((f"+{fmt_compact(info['income'])}", c("pos")))
            if info.get("expense"):
                lines.append((f"−{fmt_compact(info['expense'])}", c("neg")))
            if info.get("savings"):
                lines.append((f"◆ {fmt_compact(info['savings'])}", c("accent")))
            for txt, colr in lines:
                lbl = ctk.CTkLabel(cell, text=txt, anchor="w",
                                   font=ctk.CTkFont(size=12), text_color=colr)
                lbl.pack(fill="x", padx=8)
                widgets.append(lbl)
            for w in widgets:
                w.bind("<Button-1>", lambda e, iso=iso: self._open_day(iso))
                w.bind("<Enter>", lambda e, f=cell: f.configure(fg_color=THEME.c("card2")))
                w.bind("<Leave>", lambda e, f=cell, b=base_fg: f.configure(fg_color=b))

        self._render_recurring()
        self._render_projects()

    def _render_recurring(self):
        clear(self.recur_card)
        c = THEME.c
        ctk.CTkLabel(self.recur_card, text="Upcoming recurring",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=c("text")).pack(fill="x", padx=14, pady=(12, 4))
        rules = db.upcoming_rules(self.app.uid, 60)
        if not rules:
            ctk.CTkLabel(self.recur_card, text="Nothing scheduled in the next 60 days.",
                         text_color=c("muted")).pack(fill="x", padx=14, pady=(0, 12), anchor="w")
            return
        sym = self.app.sym
        for r in rules[:6]:
            row = ctk.CTkFrame(self.recur_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=r["description"] or "(no description)", anchor="w",
                         text_color=c("text")).pack(side="left")
            ctk.CTkLabel(row, text=f"{fmt_money(r['amount'], sym)} · {r['frequency']} · {r['next_date']}",
                         text_color=c("muted")).pack(side="right")
        ctk.CTkLabel(self.recur_card, text="Manage in Settings → Recurring.",
                     text_color=c("muted"), font=ctk.CTkFont(size=11)
                     ).pack(fill="x", padx=14, pady=(2, 10), anchor="w")

    def _render_projects(self):
        clear(self.proj_card)
        c = THEME.c
        ctk.CTkLabel(self.proj_card, text="Project funds",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=c("text")).pack(fill="x", padx=14, pady=(12, 4))
        projects = db.list_projects(self.app.uid)
        if not projects:
            ctk.CTkLabel(self.proj_card, text="No projects yet — create one in Settings → Projects.",
                         text_color=c("muted")).pack(fill="x", padx=14, pady=(0, 12), anchor="w")
            return
        sym = self.app.sym
        for p in projects[:4]:
            st = db.project_stats(self.app.uid, p["id"])
            net = st["saved"] - st["spent"]
            target = p["target_amount"] or 0
            pct = max(0.0, min(1.0, net / target)) if target > 0 else 0.0
            row = ctk.CTkFrame(self.proj_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(4, 0))
            ctk.CTkLabel(row, text=p["name"], anchor="w", text_color=c("text")).pack(side="left")
            txt = fmt_money(net, sym) + (f" / {fmt_money(target, sym)}" if target else "")
            ctk.CTkLabel(row, text=txt, text_color=c("muted")).pack(side="right")
            bar = ctk.CTkProgressBar(self.proj_card, height=8, corner_radius=4,
                                     fg_color=c("card2"), progress_color=c("accent"))
            bar.pack(fill="x", padx=14, pady=(2, 4))
            bar.set(pct)
        ctk.CTkLabel(self.proj_card, text="Manage in Settings → Projects.",
                     text_color=c("muted"), font=ctk.CTkFont(size=11)
                     ).pack(fill="x", padx=14, pady=(2, 10), anchor="w")

    def _open_day(self, iso):
        DayDialog(self.app, iso)


class DayDialog(ctk.CTkToplevel):
    def __init__(self, app, day_iso):
        super().__init__(app)
        self.app = app
        self.day = day_iso
        d = parse_date(day_iso)
        self.title(d.strftime("%d %B %Y"))
        self.configure(fg_color=THEME.c("bg"))
        self.geometry("520x600")
        self.transient(app)
        safe_grab(self)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(head, text=d.strftime("%A %d %B %Y"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=THEME.c("text")).pack(side="left")
        ctk.CTkButton(head, text="＋ Add", fg_color=THEME.c("accent"),
                      hover_color=THEME.c("accent_hover"), command=self._add).pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=8)
        self.reload()

    def reload(self):
        clear(self.list_frame)
        c = THEME.c
        txs = db.query_tx(self.app.uid, dfrom=self.day, dto=self.day)
        if not txs:
            ctk.CTkLabel(self.list_frame, text="No transactions on this day.",
                         text_color=c("muted")).pack(pady=30)
            return
        sym = self.app.sym
        for tx in reversed(txs):
            row = card(self.list_frame)
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)
            icon = tx.get("cat_icon") or {"expense": "🍔", "income": "💼", "savings": "🏦"}[tx["type"]]
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=20)
                         ).grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=8)
            ctk.CTkLabel(row, text=tx["description"] or tx.get("cat_name") or tx["type"],
                         anchor="w", text_color=c("text"),
                         font=ctk.CTkFont(size=13, weight="bold")
                         ).grid(row=0, column=1, sticky="w", pady=(8, 0))
            meta = tx.get("cat_name") or "Uncategorized"
            tags = db.tx_tag_names(tx["id"])
            if tags:
                meta += "  ·  " + tags
            ctk.CTkLabel(row, text=meta, anchor="w", text_color=c("muted"),
                         font=ctk.CTkFont(size=11)).grid(row=1, column=1, sticky="w", pady=(0, 8))
            ctk.CTkLabel(row, text=f"{SIGN[tx['type']]} {fmt_money(tx['amount'], sym)}",
                         text_color=c(COLOR_KEY[tx["type"]]),
                         font=ctk.CTkFont(size=14, weight="bold")
                         ).grid(row=0, column=2, rowspan=2, padx=12)
            ctk.CTkButton(row, text="Edit", width=52, height=26, fg_color="transparent",
                          border_width=1, border_color=c("border"), text_color=c("text"),
                          hover_color=c("card2"),
                          command=lambda t=tx: self._edit(t)
                          ).grid(row=0, column=3, rowspan=2, padx=(0, 4), pady=8)
            ctk.CTkButton(row, text="✕", width=30, height=26, fg_color="transparent",
                          border_width=1, border_color=c("border"), text_color=c("neg"),
                          hover_color=c("card2"),
                          command=lambda t=tx: self._delete(t)
                          ).grid(row=0, column=4, rowspan=2, padx=(0, 12), pady=8)

    def _add(self):
        dlg = TransactionDialog(self.app, preset_date=self.day, parent=self)
        self.wait_window(dlg)
        if dlg.saved:
            self.reload()
            self.app.refresh_current()
        safe_grab(self)

    def _edit(self, tx):
        full = db.get_tx(self.app.uid, tx["id"])
        dlg = TransactionDialog(self.app, tx=full, parent=self)
        self.wait_window(dlg)
        if dlg.saved:
            self.reload()
            self.app.refresh_current()
        safe_grab(self)

    def _delete(self, tx):
        if mb.askyesno("Delete", "Delete this transaction?", parent=self):
            db.delete_tx(self.app.uid, tx["id"])
            self.reload()
            self.app.refresh_current()