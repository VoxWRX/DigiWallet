import csv
import tkinter.messagebox as mb
from tkinter import filedialog, ttk

import customtkinter as ctk

from . import db
from .themes import THEME
from .utils import fmt_money, parse_date
from .widgets import Page, card, page_header, TYPE_LABELS
from .ui_transaction import TransactionDialog

SIGN = {"income": "+", "expense": "−", "savings": "◆"}


class LedgerPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = THEME.c
        self.rows = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        head = page_header(self, "Ledger Book", "View, edit and manage all your records")
        head.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 4))
        actions = ctk.CTkFrame(head, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkButton(actions, text="Export CSV", fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=self._export_csv).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="＋ Add record", fg_color=c("accent"),
                      hover_color=c("accent_hover"), command=self._add).pack(side="left")

        fcard = card(self)
        fcard.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        self.e_search = ctk.CTkEntry(fcard, placeholder_text="Search…", width=190)
        self.e_search.grid(row=0, column=0, padx=(14, 6), pady=12)
        self.var_type = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(fcard, values=["All"] + list(TYPE_LABELS.values()),
                          variable=self.var_type, width=105, fg_color=c("card2"),
                          button_color=c("accent"),
                          button_hover_color=c("accent_hover")).grid(row=0, column=1, padx=6)
        self.cat_map = {f"{x['name']} · {x['type']}": x["id"]
                        for x in db.list_categories(app.uid)}
        self.var_cat = ctk.StringVar(value="All categories")
        ctk.CTkOptionMenu(fcard, values=["All categories"] + list(self.cat_map),
                          variable=self.var_cat, width=185, fg_color=c("card2"),
                          button_color=c("accent"),
                          button_hover_color=c("accent_hover")).grid(row=0, column=2, padx=6)
        self.tag_map = {t["name"]: t["id"] for t in db.list_tags(app.uid)}
        self.var_tag = ctk.StringVar(value="All tags")
        ctk.CTkOptionMenu(fcard, values=["All tags"] + list(self.tag_map),
                          variable=self.var_tag, width=125, fg_color=c("card2"),
                          button_color=c("accent"),
                          button_hover_color=c("accent_hover")).grid(row=0, column=3, padx=6)
        self.e_from = ctk.CTkEntry(fcard, placeholder_text="From", width=95)
        self.e_from.grid(row=0, column=4, padx=6)
        self.e_to = ctk.CTkEntry(fcard, placeholder_text="To", width=95)
        self.e_to.grid(row=0, column=5, padx=6)
        ctk.CTkButton(fcard, text="Apply", fg_color=c("accent"), hover_color=c("accent_hover"),
                      command=self.load).grid(row=0, column=6, padx=6)
        ctk.CTkButton(fcard, text="Reset", fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=self._reset).grid(row=0, column=7, padx=(6, 14))

        tcard = card(self)
        tcard.grid(row=2, column=0, sticky="nsew", padx=24, pady=(8, 16))
        tcard.grid_columnconfigure(0, weight=1)
        tcard.grid_rowconfigure(0, weight=1)

        cols = ("date", "type", "category", "description", "tags", "amount", "currency")
        self.tree = ttk.Treeview(tcard, columns=cols, show="headings", selectmode="browse")
        headings = {"date": ("Date", 95), "type": ("Type", 85), "category": ("Category", 165),
                    "description": ("Description", 250), "tags": ("Tags", 140),
                    "amount": (f"Amount ({app.user['base_currency']})", 130),
                    "currency": ("Currency", 90)}
        for key, (text, width) in headings.items():
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor="e" if key == "amount" else "w")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sb = ctk.CTkScrollbar(tcard, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        self.tree.configure(yscrollcommand=sb.set)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Wallet.Treeview", background=c("card"), foreground=c("text"),
                        fieldbackground=c("card"), rowheight=30, bordercolor=c("border"),
                        borderwidth=0, font=("Helvetica", 11))
        style.configure("Wallet.Treeview.Heading", background=c("card2"), foreground=c("muted"),
                        bordercolor=c("border"), borderwidth=0, font=("Helvetica", 10, "bold"))
        style.map("Wallet.Treeview", background=[("selected", c("accent"))],
                  foreground=[("selected", "#FFFFFF")])
        style.map("Wallet.Treeview.Heading", background=[("active", c("card2"))])
        self.tree.configure(style="Wallet.Treeview")
        self.tree.tag_configure("income", foreground=c("pos"))
        self.tree.tag_configure("expense", foreground=c("neg"))
        self.tree.tag_configure("savings", foreground=c("accent"))
        self.tree.bind("<Double-1>", lambda e: self._edit())

        foot = ctk.CTkFrame(tcard, fg_color="transparent")
        foot.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        self.lbl_count = ctk.CTkLabel(foot, text="", text_color=c("muted"))
        self.lbl_count.pack(side="left")
        ctk.CTkButton(foot, text="Edit selected", width=110, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=self._edit).pack(side="right", padx=(6, 0))
        ctk.CTkButton(foot, text="Delete selected", width=120, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("neg"), hover_color=c("card2"),
                      command=self._delete).pack(side="right")

        self.load()

    # ------------------------------------------------------------------ data
    def load(self):
        ttype = None
        if self.var_type.get() != "All":
            from .widgets import LABEL_TYPES
            ttype = LABEL_TYPES[self.var_type.get()]
        dfrom, dto = parse_date(self.e_from.get()), parse_date(self.e_to.get())
        self.rows = db.query_tx(
            self.app.uid, search=self.e_search.get().strip(), ttype=ttype,
            category_id=self.cat_map.get(self.var_cat.get()),
            tag_id=self.tag_map.get(self.var_tag.get()),
            dfrom=dfrom.isoformat() if dfrom else None,
            dto=dto.isoformat() if dto else None)

        self.tree.delete(*self.tree.get_children())
        base = self.app.user["base_currency"]
        for tx in self.rows:
            self.tree.insert("", "end", iid=str(tx["id"]), tags=(tx["type"],),
                             values=(tx["date"], TYPE_LABELS[tx["type"]],
                                     f"{tx['cat_icon'] or '🧾'} {tx['cat_name'] or 'Uncategorized'}",
                                     tx["description"] or "", db.tx_tag_names(tx["id"]),
                                     f"{SIGN[tx['type']]} {fmt_money(tx['amount'], '')}",
                                     tx["orig_currency"] or base))
        total = {"income": 0.0, "expense": 0.0, "savings": 0.0}
        for tx in self.rows:
            total[tx["type"]] += tx["amount"]
        net = total["income"] - total["expense"] - total["savings"]
        sym = self.app.sym
        self.lbl_count.configure(
            text=f"{len(self.rows)} records   ·   In {fmt_money(total['income'], sym)}"
                 f"   ·   Out {fmt_money(total['expense'], sym)}"
                 f"   ·   Saved {fmt_money(total['savings'], sym)}"
                 f"   ·   Net {fmt_money(net, sym)}")

    def _reset(self):
        self.e_search.delete(0, "end")
        self.var_type.set("All")
        self.var_cat.set("All categories")
        self.var_tag.set("All tags")
        self.e_from.delete(0, "end")
        self.e_to.delete(0, "end")
        self.load()

    # ---------------------------------------------------------------- actions
    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _add(self):
        dlg = TransactionDialog(self.app)
        self.wait_window(dlg)
        if dlg.saved:
            self.load()

    def _edit(self):
        tid = self._selected_id()
        if not tid:
            return
        tx = db.get_tx(self.app.uid, tid)
        if not tx:
            return
        dlg = TransactionDialog(self.app, tx=tx)
        self.wait_window(dlg)
        if dlg.saved:
            self.load()

    def _delete(self):
        tid = self._selected_id()
        if not tid:
            return
        if mb.askyesno("Delete", "Delete the selected transaction?", parent=self):
            db.delete_tx(self.app.uid, tid)
            self.load()

    def _export_csv(self):
        if not self.rows:
            mb.showinfo("Nothing to export", "No records match the current filters.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")],
                                            initialfile="ledger_export.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Type", "Category", "Description", "Tags", "Amount", "Currency",
                        "Original amount", "Original currency", "Notes"])
            for tx in self.rows:
                w.writerow([tx["date"], tx["type"], tx["cat_name"] or "", tx["description"] or "",
                            db.tx_tag_names(tx["id"]), f"{tx['amount']:.2f}",
                            self.app.user["base_currency"],
                            f"{tx['orig_amount']:.2f}" if tx["orig_amount"] else "",
                            tx["orig_currency"] or "", tx["notes"] or ""])
        mb.showinfo("Export complete", f"CSV saved to:\n{path}")