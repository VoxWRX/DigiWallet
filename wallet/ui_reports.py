import calendar as cal
import csv
from datetime import date
import tkinter.messagebox as mb
from tkinter import filedialog

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from . import db, reporting
from .themes import THEME
from .utils import MONTHS, clear, fmt_compact, fmt_money
from .widgets import Page, StatCard, card, page_header


class ReportsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = THEME.c
        self.data = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        head = page_header(self, "Reports & Analytics",
                           "Monthly and annual overviews with exportable PDF / CSV reports")
        head.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))

        ctrl = card(self)
        ctrl.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        ctrl.grid_columnconfigure(5, weight=1)
        self.var_period = ctk.StringVar(value="Monthly")
        ctk.CTkSegmentedButton(ctrl, values=["Monthly", "Annual"], variable=self.var_period,
                               command=self._on_period, selected_color=c("accent"),
                               selected_hover_color=c("accent_hover"), fg_color=c("card2"),
                               unselected_color=c("card2"), unselected_hover_color=c("border"),
                               text_color=c("text")).grid(row=0, column=0, padx=(14, 12), pady=12)
        self.var_year = ctk.StringVar(value=str(date.today().year))
        ctk.CTkOptionMenu(ctrl, values=[str(y) for y in db.available_years(app.uid)],
                          variable=self.var_year, width=100, fg_color=c("card2"),
                          button_color=c("accent"),
                          button_hover_color=c("accent_hover")).grid(row=0, column=1, padx=6, pady=12)
        self.var_month = ctk.StringVar(value=MONTHS[date.today().month - 1])
        self.menu_month = ctk.CTkOptionMenu(ctrl, values=MONTHS, variable=self.var_month,
                                            width=130, fg_color=c("card2"), button_color=c("accent"),
                                            button_hover_color=c("accent_hover"))
        self.menu_month.grid(row=0, column=2, padx=6, pady=12)
        ctk.CTkButton(ctrl, text="Generate", width=110, fg_color=c("accent"),
                      hover_color=c("accent_hover"),
                      command=self.generate).grid(row=0, column=3, padx=(12, 6), pady=12)
        ctk.CTkButton(ctrl, text="Export PDF", width=110, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=self.export_pdf).grid(row=0, column=4, padx=6, pady=12)
        ctk.CTkButton(ctrl, text="Export CSV", width=110, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=self.export_csv).grid(row=0, column=5, sticky="w", padx=6, pady=12)

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=24, pady=(4, 8))
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

        self.charts = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.charts.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.charts.grid_columnconfigure(0, weight=1)
        self.charts.grid_columnconfigure(1, weight=1)

        self.generate()

    def _on_period(self, _val=None):
        if self.var_period.get() == "Monthly":
            self.menu_month.grid()
        else:
            self.menu_month.grid_remove()

    # ------------------------------------------------------------------ data
    def generate(self):
        try:
            year = int(self.var_year.get())
        except ValueError:
            mb.showerror("Invalid year", "Please choose a valid year.")
            return
        monthly = self.var_period.get() == "Monthly"
        if monthly:
            month = MONTHS.index(self.var_month.get()) + 1
            dfrom = f"{year:04d}-{month:02d}-01"
            dto = f"{year:04d}-{month:02d}-{cal.monthrange(year, month)[1]:02d}"
            label = f"{MONTHS[month - 1]} {year}"
        else:
            month = None
            dfrom, dto = f"{year:04d}-01-01", f"{year:04d}-12-31"
            label = str(year)
        uid = self.app.uid
        self.data = {
            "label": label, "from": dfrom, "to": dto, "year": year, "month": month,
            "totals": db.totals_between(uid, dfrom, dto),
            "cat_exp": db.category_breakdown(uid, "expense", dfrom, dto),
            "cat_inc": db.category_breakdown(uid, "income", dfrom, dto),
            "cat_sav": db.category_breakdown(uid, "savings", dfrom, dto),
            "monthly": db.monthly_series(uid, year),
            "daily": db.daily_series(uid, year, month) if monthly else None,
            "txs": db.query_tx(uid, dfrom=dfrom, dto=dto),
        }
        self._render_stats()
        self._render_charts()

    def _render_stats(self):
        t = self.data["totals"]
        net = t["income"] - t["expense"] - t["savings"]
        sym, c = self.app.sym, THEME.c
        self.card_income.set(fmt_money(t["income"], sym), c("pos"))
        self.card_expense.set(fmt_money(t["expense"], sym), c("neg"))
        self.card_savings.set(fmt_money(t["savings"], sym), c("accent"))
        self.card_net.set(fmt_money(net, sym), c("pos") if net >= 0 else c("neg"))

    # ---------------------------------------------------------------- charts
    def _fig_colors(self, light=False):
        if light:
            return dict(card="#FFFFFF", text="#0F172A", muted="#64748B", border="#E2E8F0",
                        accent=THEME.light("accent"), pos="#16A34A", neg="#DC2626")
        return dict(card=THEME.c("card"), text=THEME.c("text"), muted=THEME.c("muted"),
                    border=THEME.c("border"), accent=THEME.c("accent"),
                    pos=THEME.c("pos"), neg=THEME.c("neg"))

    def _new_ax(self, col, w=4.9, h=3.1):
        fig = Figure(figsize=(w, h), dpi=100)
        fig.patch.set_facecolor(col["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(col["card"])
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(colors=col["muted"], labelsize=8)
        ax.grid(axis="y", color=col["border"], linewidth=0.7)
        ax.set_axisbelow(True)
        return fig, ax

    def _legend(self, ax, col):
        leg = ax.legend(fontsize=8, frameon=False)
        for t in leg.get_texts():
            t.set_color(col["text"])

    def _pie(self, breakdown, col):
        fig = Figure(figsize=(5.2, 3.2), dpi=100)
        fig.patch.set_facecolor(col["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(col["card"])
        if not breakdown:
            ax.text(0.5, 0.5, "No expenses recorded", ha="center", va="center",
                    color=col["muted"], fontsize=10)
            ax.set_axis_off()
            return fig
        items = breakdown[:8]
        if len(breakdown) > 8:
            items.append({"name": "Other", "color": "#94A3B8",
                          "total": sum(r["total"] for r in breakdown[8:]), "n": 0})
        wedges, _texts, autotexts = ax.pie(
            [r["total"] for r in items], colors=[r["color"] for r in items], startangle=90,
            autopct=lambda p: f"{p:.0f}%" if p >= 4 else "", pctdistance=0.78,
            wedgeprops=dict(width=0.42, edgecolor=col["card"], linewidth=1.5),
            textprops=dict(color=col["text"], fontsize=8))
        for t in autotexts:
            t.set_color(col["text"])
        ax.legend(wedges, [f"{r['name']}  ({fmt_compact(r['total'])})" for r in items],
                  loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=8)
        for t in ax.get_legend().get_texts():
            t.set_color(col["text"])
        fig.subplots_adjust(right=0.52, left=0.02, top=0.95, bottom=0.05)
        return fig

    def _daily_bars(self, col):
        series = self.data["daily"]
        days = len(series) - 1
        fig, ax = self._new_ax(col)
        xs = list(range(1, days + 1))
        ax.bar([x - 0.2 for x in xs], [series[d]["income"] for d in xs], width=0.4,
               color=col["pos"], label="Income")
        ax.bar([x + 0.2 for x in xs], [series[d]["expense"] for d in xs], width=0.4,
               color=col["neg"], label="Expenses")
        ax.set_xticks(list(range(1, days + 1, 2)))
        self._legend(ax, col)
        fig.tight_layout()
        return fig

    def _cumulative(self, col):
        series = self.data["daily"]
        days = len(series) - 1
        fig, ax = self._new_ax(col)
        run, ys = 0.0, []
        for d in range(1, days + 1):
            run += series[d]["income"] - series[d]["expense"] - series[d]["savings"]
            ys.append(run)
        ax.plot(range(1, days + 1), ys, color=col["accent"], linewidth=1.8, marker="o",
                markersize=2.5)
        ax.axhline(0, color=col["muted"], linewidth=0.8, linestyle="--")
        ax.fill_between(range(1, days + 1), ys, 0, color=col["accent"], alpha=0.10)
        ax.set_xticks(list(range(1, days + 1, 2)))
        fig.tight_layout()
        return fig

    def _monthly_bars(self, col):
        series = self.data["monthly"]
        fig, ax = self._new_ax(col)
        xs = list(range(12))
        ax.bar([x - 0.2 for x in xs], [m["income"] for m in series], width=0.4,
               color=col["pos"], label="Income")
        ax.bar([x + 0.2 for x in xs], [m["expense"] for m in series], width=0.4,
               color=col["neg"], label="Expenses")
        ax.set_xticks(xs)
        ax.set_xticklabels([m[:3] for m in MONTHS])
        self._legend(ax, col)
        fig.tight_layout()
        return fig

    def _net_lines(self, col):
        series = self.data["monthly"]
        fig, ax = self._new_ax(col)
        xs = list(range(12))
        net = [m["income"] - m["expense"] - m["savings"] for m in series]
        run, cum = 0.0, []
        for v in net:
            run += v
            cum.append(run)
        ax.plot(xs, net, color=col["accent"], linewidth=1.8, marker="o", markersize=3,
                label="Monthly net")
        ax.plot(xs, cum, color=col["muted"], linewidth=1.4, linestyle="--",
                label="Cumulative net")
        ax.axhline(0, color=col["muted"], linewidth=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels([m[:3] for m in MONTHS])
        self._legend(ax, col)
        fig.tight_layout()
        return fig

    def _figures(self, light=False):
        col = self._fig_colors(light)
        figs = [("Expenses by category", self._pie(self.data["cat_exp"], col))]
        if self.data["month"]:
            figs.append(("Daily income vs expenses", self._daily_bars(col)))
            figs.append(("Cumulative net", self._cumulative(col)))
        else:
            figs.append(("Monthly income vs expenses", self._monthly_bars(col)))
            figs.append(("Monthly net & cumulative", self._net_lines(col)))
        return figs

    def _render_charts(self):
        clear(self.charts)
        for i, (title, fig) in enumerate(self._figures(light=False)):
            fr = card(self.charts)
            r, cn = divmod(i, 2)
            fr.grid(row=r, column=cn, sticky="nsew", padx=6, pady=6)
            ctk.CTkLabel(fr, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=THEME.c("text"), anchor="w"
                         ).pack(fill="x", padx=12, pady=(10, 0))
            canvas = FigureCanvasTkAgg(fig, master=fr)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # --------------------------------------------------------------- exports
    def export_pdf(self):
        if not self.data:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF document", "*.pdf")],
            initialfile=f"wallet_report_{self.data['from']}_{self.data['to']}.pdf")
        if not path:
            return
        try:
            figs = self._figures(light=True)
            reporting.export_pdf(path, self.app.user, self.data, figs, self.app.sym)
            for _t, f in figs:
                f.clf()
            mb.showinfo("Export complete", f"PDF report saved to:\n{path}")
        except Exception as e:
            mb.showerror("Export failed", str(e))

    def export_csv(self):
        if not self.data:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"wallet_report_{self.data['from']}_{self.data['to']}.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Digital Wallet report", self.data["label"],
                        f"generated {date.today().isoformat()}"])
            w.writerow([])
            t = self.data["totals"]
            w.writerow(["Total income", f"{t['income']:.2f}"])
            w.writerow(["Total expenses", f"{t['expense']:.2f}"])
            w.writerow(["Total savings", f"{t['savings']:.2f}"])
            w.writerow(["Net", f"{t['income'] - t['expense'] - t['savings']:.2f}"])
            w.writerow([])
            w.writerow(["Date", "Type", "Category", "Description", "Tags", "Amount", "Currency",
                        "Notes"])
            for tx in self.data["txs"]:
                w.writerow([tx["date"], tx["type"], tx["cat_name"] or "", tx["description"] or "",
                            db.tx_tag_names(tx["id"]), f"{tx['amount']:.2f}",
                            self.app.user["base_currency"], tx["notes"] or ""])
        mb.showinfo("Export complete", f"CSV saved to:\n{path}")