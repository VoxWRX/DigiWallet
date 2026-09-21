"""Add / edit transaction dialog (shared by dashboard, day view and ledger)."""
import tkinter.messagebox as mb

import customtkinter as ctk

from . import db
from .themes import THEME
from .utils import parse_date, parse_float, today_str
from .widgets import Dialog, LABEL_TYPES, TYPE_LABELS


class TransactionDialog(Dialog):
    def __init__(self, app, tx=None, preset_date=None, parent=None):
        self.tx = tx
        self.saved = False
        super().__init__(app, "Edit transaction" if tx else "Add transaction",
                         width=500, height=680, parent=parent)
        self.resizable(False, True)
        c = THEME.c
        self.currencies = [r["code"] for r in db.list_currencies(app.uid)]
        self.base = app.user["base_currency"]
        self.projects = db.list_projects(app.uid)

        # type
        self.type_seg = ctk.CTkSegmentedButton(
            self.body, values=list(TYPE_LABELS.values()), command=self._on_type,
            selected_color=c("accent"), selected_hover_color=c("accent_hover"),
            fg_color=c("card2"), unselected_color=c("card2"),
            unselected_hover_color=c("border"), text_color=c("text"))
        self.type_seg.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 8))

        # amount + currency
        amt = ctk.CTkFrame(self.body, fg_color="transparent")
        amt.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=6)
        amt.grid_columnconfigure(0, weight=1)
        self.e_amount = ctk.CTkEntry(amt, placeholder_text="Amount")
        self.e_amount.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.var_cur = ctk.StringVar(value=self.base)
        ctk.CTkOptionMenu(amt, values=self.currencies, variable=self.var_cur, width=100,
                          command=lambda _v: self._on_currency(), fg_color=c("card2"),
                          button_color=c("accent"),
                          button_hover_color=c("accent_hover")).grid(row=0, column=1)

        # conversion rate (foreign currency only)
        self.rate_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.rate_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=2)
        self.rate_frame.grid_columnconfigure(0, weight=1)
        self.rate_lbl = ctk.CTkLabel(self.rate_frame, text="", text_color=c("muted"))
        self.rate_lbl.grid(row=0, column=0, sticky="w")
        self.e_rate = ctk.CTkEntry(self.rate_frame, width=120, placeholder_text="rate")
        self.e_rate.grid(row=0, column=1)

        self.e_date = ctk.CTkEntry(self.body, placeholder_text="Date  (YYYY-MM-DD)")
        self.field_row(3, "Date", self.e_date)

        self.cat_menu = ctk.CTkOptionMenu(self.body, values=["—"], fg_color=c("card2"),
                                          button_color=c("accent"),
                                          button_hover_color=c("accent_hover"))
        self.field_row(4, "Category", self.cat_menu)

        self.proj_lbl = ctk.CTkLabel(self.body, text="Project", text_color=c("muted"), anchor="e")
        self.proj_lbl.grid(row=5, column=0, sticky="e", padx=(16, 8), pady=6)
        self.proj_menu = ctk.CTkOptionMenu(self.body, values=["None"], fg_color=c("card2"),
                                           button_color=c("accent"),
                                           button_hover_color=c("accent_hover"))
        self.proj_menu.grid(row=5, column=1, sticky="ew", padx=(0, 16), pady=6)

        self.e_desc = ctk.CTkEntry(self.body, placeholder_text="Short description")
        self.field_row(6, "Description", self.e_desc)

        # tags
        tbox = ctk.CTkFrame(self.body, fg_color="transparent")
        tbox.grid(row=7, column=0, columnspan=2, sticky="ew", padx=16, pady=6)
        ctk.CTkLabel(tbox, text="Tags", text_color=c("muted")).pack(anchor="w")
        self.tag_frame = ctk.CTkScrollableFrame(tbox, height=76, fg_color=c("card2"))
        self.tag_frame.pack(fill="x", pady=(4, 6))
        quick = ctk.CTkFrame(tbox, fg_color="transparent")
        quick.pack(fill="x")
        self.e_newtag = ctk.CTkEntry(quick, placeholder_text="New tag", width=180)
        self.e_newtag.pack(side="left")
        ctk.CTkButton(quick, text="＋ Add", width=70, fg_color=c("accent"),
                      hover_color=c("accent_hover"), command=self._add_tag).pack(side="left", padx=6)

        self.e_notes = ctk.CTkEntry(self.body, placeholder_text="Notes (optional)")
        self.field_row(8, "Notes", self.e_notes)

        self.buttons("Save transaction", self._save, 9)

        # initial values
        selected = set()
        if tx:
            label = TYPE_LABELS[tx["type"]]
            self.type_seg.set(label)
            self._on_type(label, keep=tx["cat_name"])
            shown = tx["orig_amount"] if tx["orig_amount"] else tx["amount"]
            self.e_amount.insert(0, f"{shown:.2f}")
            self.var_cur.set(tx["orig_currency"] or self.base)
            if tx["orig_amount"]:
                self.e_rate.insert(0, f"{tx['amount'] / tx['orig_amount']:.4f}")
            self.e_date.insert(0, tx["date"])
            self.e_desc.insert(0, tx["description"] or "")
            self.e_notes.insert(0, tx["notes"] or "")
            if tx["type"] == "savings" and tx["project_id"]:
                proj = next((p for p in self.projects if p["id"] == tx["project_id"]), None)
                if proj:
                    self.proj_menu.set(proj["name"])
            selected = set(db.tx_tag_ids(tx["id"]))
        else:
            self.type_seg.set("Expense")
            self._on_type("Expense")
            self.e_date.insert(0, preset_date or today_str())

        self._build_tags(selected)
        self._on_currency()

    # ----------------------------------------------------------- handlers
    def _on_type(self, label, keep=None):
        ttype = LABEL_TYPES[label]
        cats = db.list_categories(self.app.uid, ttype)
        self.cat_map = {x["name"]: x["id"] for x in cats}
        values = list(self.cat_map) or ["—"]
        self.cat_menu.configure(values=values)
        self.cat_menu.set(keep if keep in self.cat_map else values[0])
        self.proj_menu.configure(values=["None"] + [p["name"] for p in self.projects])
        self.proj_menu.set("None")
        if ttype == "savings":
            self.proj_lbl.grid()
            self.proj_menu.grid()
        else:
            self.proj_lbl.grid_remove()
            self.proj_menu.grid_remove()

    def _on_currency(self):
        code = self.var_cur.get()
        if code == self.base:
            self.rate_frame.grid_remove()
        else:
            self.rate_frame.grid()
            self.rate_lbl.configure(text=f"1 {code} = ? {self.base}")

    def _build_tags(self, selected):
        for w in self.tag_frame.winfo_children():
            w.destroy()
        self.tag_vars = {}
        tags = db.list_tags(self.app.uid)
        if not tags:
            ctk.CTkLabel(self.tag_frame, text="No tags yet — add one below.",
                         text_color=THEME.c("muted")).pack(padx=8, pady=8)
            return
        for t in tags:
            var = ctk.BooleanVar(value=t["id"] in selected)
            cb = ctk.CTkCheckBox(self.tag_frame, text=t["name"], variable=var,
                                 checkbox_width=18, checkbox_height=18, corner_radius=4,
                                 fg_color=THEME.c("accent"), hover_color=THEME.c("accent_hover"),
                                 text_color=THEME.c("text"))
            cb.pack(anchor="w", padx=10, pady=2)
            self.tag_vars[t["id"]] = var

    def _add_tag(self):
        name = self.e_newtag.get().strip()
        if not name:
            return
        db.add_tag(self.app.uid, name)
        self.e_newtag.delete(0, "end")
        selected = {tid for tid, var in self.tag_vars.items() if var.get()}
        for t in db.list_tags(self.app.uid):
            if t["name"] == name:
                selected.add(t["id"])
        self._build_tags(selected)

    def _save(self):
        amount = parse_float(self.e_amount.get())
        if amount is None or amount <= 0:
            mb.showerror("Invalid amount", "Enter a positive number.", parent=self)
            return
        d = parse_date(self.e_date.get())
        if not d:
            mb.showerror("Invalid date", "Use the YYYY-MM-DD format.", parent=self)
            return
        ttype = LABEL_TYPES[self.type_seg.get()]
        code = self.var_cur.get()
        orig_amount = None
        if code != self.base:
            rate = parse_float(self.e_rate.get())
            if rate is None or rate <= 0:
                mb.showerror("Invalid rate",
                             f"Enter the conversion rate (1 {code} = ? {self.base}).", parent=self)
                return
            base_amount = amount * rate
            orig_amount = amount
        else:
            base_amount = amount
        cat_id = self.cat_map.get(self.cat_menu.get())
        project_id = None
        if ttype == "savings" and self.proj_menu.get() != "None":
            project_id = next((p["id"] for p in self.projects
                               if p["name"] == self.proj_menu.get()), None)
        tag_ids = [tid for tid, var in self.tag_vars.items() if var.get()]
        desc = self.e_desc.get().strip()
        notes = self.e_notes.get().strip()

        if self.tx:
            db.update_tx(self.app.uid, self.tx["id"], d.isoformat(), ttype, base_amount,
                         cat_id, project_id, desc, notes, orig_amount,
                         code if orig_amount else None)
            db.set_tx_tags(self.tx["id"], tag_ids)
        else:
            tid = db.add_tx(self.app.uid, d.isoformat(), ttype, base_amount, cat_id,
                            project_id, desc, notes, orig_amount, code if orig_amount else None)
            db.set_tx_tags(tid, tag_ids)
        self.saved = True
        self.destroy()