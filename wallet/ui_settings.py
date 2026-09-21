import sqlite3
import tkinter.messagebox as mb

import customtkinter as ctk

from . import db, auth
from .themes import THEME, PALETTES
from .utils import clear, fmt_money, parse_date, parse_float, today_str
from .widgets import (Page, card, Dialog, FREQUENCIES, LABEL_TYPES, TYPE_LABELS)

PRESET_COLORS = ["#EF4444", "#F97316", "#EAB308", "#22C55E", "#14B8A6",
                 "#0EA5E9", "#3B82F6", "#8B5CF6", "#EC4899", "#64748B"]
TAB_NAMES = ("Profile", "Appearance", "Categories", "Tags", "Currencies", "Recurring", "Projects")


class SettingsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        c = THEME.c
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=c("text")).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 6))

        self.tabs = ctk.CTkTabview(
            self, fg_color="transparent",
            segmented_button_selected_color=c("accent"),
            segmented_button_selected_hover_color=c("accent_hover"),
            segmented_button_unselected_color=c("card"),
            segmented_button_unselected_hover_color=c("card2"),
            text_color=c("text"))
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 16))
        for name in TAB_NAMES:
            self.tabs.add(name)
            self.tabs.tab(name).configure(fg_color="transparent")
            self.tabs.tab(name).grid_columnconfigure(0, weight=1)

        self._build_profile()
        self._build_appearance()
        self._build_categories()
        self._build_tags()
        self._build_currencies()
        self._build_recurring()
        self._build_projects()
        self.tabs.set("Profile")

    def _tab_top(self, tab_frame, info, btn_text, btn_cmd):
        top = ctk.CTkFrame(tab_frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        ctk.CTkLabel(top, text=info, text_color=THEME.c("muted"), anchor="w").pack(side="left")
        ctk.CTkButton(top, text=btn_text, fg_color=THEME.c("accent"),
                      hover_color=THEME.c("accent_hover"), command=btn_cmd).pack(side="right")

    # ================================================================ PROFILE
    def _build_profile(self):
        f = self.tabs.tab("Profile")
        clear(f)
        c = THEME.c

        p = card(f)
        p.grid(row=0, column=0, sticky="ew", pady=6)
        p.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(p, text="Profile", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=c("text")).grid(row=0, column=0, columnspan=2,
                                                sticky="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(p, text="Username", text_color=c("muted")).grid(row=1, column=0, sticky="w",
                                                                     padx=16, pady=6)
        ctk.CTkLabel(p, text="@" + self.app.user["username"],
                     text_color=c("text")).grid(row=1, column=1, sticky="w", pady=6)
        ctk.CTkLabel(p, text="Display name", text_color=c("muted")).grid(row=2, column=0, sticky="w",
                                                                          padx=16, pady=6)
        self.e_display = ctk.CTkEntry(p)
        self.e_display.insert(0, self.app.user["display_name"] or "")
        self.e_display.grid(row=2, column=1, sticky="ew", padx=(0, 16), pady=6)
        ctk.CTkLabel(p, text="Base currency", text_color=c("muted")).grid(row=3, column=0, sticky="w",
                                                                           padx=16, pady=6)
        self.var_base = ctk.StringVar(value=self.app.user["base_currency"])
        ctk.CTkOptionMenu(p, values=[r["code"] for r in db.list_currencies(self.app.uid)],
                          variable=self.var_base, width=140, fg_color=c("card2"),
                          button_color=c("accent"),
                          button_hover_color=c("accent_hover")).grid(row=3, column=1, sticky="w", pady=6)
        ctk.CTkButton(p, text="Save profile", fg_color=c("accent"), hover_color=c("accent_hover"),
                      command=self._save_profile).grid(row=4, column=1, sticky="w",
                                                       padx=(0, 16), pady=(8, 4))
        ctk.CTkLabel(p, text="Note: changing the base currency does not convert existing records.",
                     text_color=c("muted"), font=ctk.CTkFont(size=11)
                     ).grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

        s = card(f)
        s.grid(row=1, column=0, sticky="ew", pady=6)
        s.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(s, text="Security", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=c("text")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.e_curpw = ctk.CTkEntry(s, placeholder_text="Current password", show="•")
        self.e_curpw.grid(row=1, column=0, sticky="ew", padx=16, pady=3)
        self.e_newpw = ctk.CTkEntry(s, placeholder_text="New password", show="•")
        self.e_newpw.grid(row=2, column=0, sticky="ew", padx=16, pady=3)
        self.e_confirmpw = ctk.CTkEntry(s, placeholder_text="Confirm new password", show="•")
        self.e_confirmpw.grid(row=3, column=0, sticky="ew", padx=16, pady=3)
        ctk.CTkButton(s, text="Change password", fg_color=c("accent"),
                      hover_color=c("accent_hover"),
                      command=self._change_pw).grid(row=4, column=0, sticky="w", padx=16,
                                                    pady=(4, 14))

        st = card(f)
        st.grid(row=2, column=0, sticky="ew", pady=6)
        ctk.CTkLabel(st, text="Data", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=c("text")).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(st, text=f"All data is stored locally in:\n{db.DB_PATH}",
                     text_color=c("muted"), justify="left"
                     ).pack(anchor="w", padx=16, pady=(0, 14))

    def _save_profile(self):
        db.update_user(self.app.uid, display_name=self.e_display.get().strip(),
                       base_currency=self.var_base.get())
        self.app.refresh_user()
        mb.showinfo("Saved", "Profile updated.")

    def _change_pw(self):
        user = db.get_user_by_id(self.app.uid)
        if not auth.verify_password(self.e_curpw.get(), user["password_hash"], user["salt"]):
            mb.showerror("Wrong password", "Current password is incorrect.")
            return
        new = self.e_newpw.get()
        if len(new) < 4 or new != self.e_confirmpw.get():
            mb.showerror("Invalid", "New passwords must match and be at least 4 characters.")
            return
        h, salt = auth.make_password(new)
        db.update_user(self.app.uid, password_hash=h, salt=salt)
        for e in (self.e_curpw, self.e_newpw, self.e_confirmpw):
            e.delete(0, "end")
        mb.showinfo("Saved", "Password changed.")

    # ============================================================ APPEARANCE
    def _build_appearance(self):
        f = self.tabs.tab("Appearance")
        clear(f)
        c = THEME.c

        mode = card(f)
        mode.grid(row=0, column=0, sticky="ew", pady=6)
        ctk.CTkLabel(mode, text="Appearance", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=c("text")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(mode, text="Choose light or dark mode — applies instantly.",
                     text_color=c("muted")).grid(row=1, column=0, sticky="w", padx=16)
        seg = ctk.CTkSegmentedButton(mode, values=["Light", "Dark"], command=self._set_mode,
                                     selected_color=c("accent"),
                                     selected_hover_color=c("accent_hover"),
                                     fg_color=c("card2"), unselected_color=c("card2"),
                                     unselected_hover_color=c("border"), text_color=c("text"))
        seg.set("Dark" if self.app.user["theme_mode"] == "dark" else "Light")
        seg.grid(row=2, column=0, sticky="w", padx=16, pady=(4, 16))

        acc = card(f)
        acc.grid(row=1, column=0, sticky="ew", pady=6)
        ctk.CTkLabel(acc, text="Accent color", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=c("text")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(acc, text="Pick a color theme — blue, pink or green.",
                     text_color=c("muted")).grid(row=1, column=0, sticky="w", padx=16)
        row = ctk.CTkFrame(acc, fg_color="transparent")
        row.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 16))
        for key, label in (("blue", "Blue"), ("pink", "Pink"), ("green", "Green")):
            col = PALETTES[key]["light"]["accent"]
            ctk.CTkButton(row, text=f"  {label}  ", fg_color=col,
                          hover_color=PALETTES[key]["light"]["accent_hover"],
                          text_color="#FFFFFF", corner_radius=8, height=36,
                          border_width=2 if self.app.user["theme_accent"] == key else 0,
                          border_color=c("text"),
                          command=lambda k=key: self._set_accent(k)).pack(side="left", padx=(0, 10))

    def _set_mode(self, value):
        db.update_user(self.app.uid, theme_mode=value.lower())
        self.app.refresh_theme()

    def _set_accent(self, key):
        db.update_user(self.app.uid, theme_accent=key)
        self.app.refresh_theme()

    # ============================================================ CATEGORIES
    def _build_categories(self):
        f = self.tabs.tab("Categories")
        clear(f)
        self._tab_top(f, "Categories organise your expenses, incomes and savings.",
                      "＋ Add category", lambda: self._edit_category(None))
        self.cat_list = ctk.CTkScrollableFrame(f, fg_color="transparent", height=430)
        self.cat_list.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        f.grid_rowconfigure(1, weight=1)
        for cat in db.list_categories(self.app.uid):
            self._category_row(cat)

    def _category_row(self, cat):
        c = THEME.c
        row = card(self.cat_list)
        row.pack(fill="x", pady=4)
        row.grid_columnconfigure(1, weight=1)
        type_col = {"expense": c("neg"), "income": c("pos"), "savings": c("accent")}[cat["type"]]
        ctk.CTkLabel(row, text=cat["icon"], font=ctk.CTkFont(size=18)
                     ).grid(row=0, column=0, padx=(14, 8), pady=10)
        ctk.CTkLabel(row, text=cat["name"], text_color=c("text"), anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(row, text=TYPE_LABELS[cat["type"]], text_color=type_col,
                     font=ctk.CTkFont(size=11)).grid(row=0, column=2, padx=12)
        ctk.CTkButton(row, text="Edit", width=54, height=28, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=lambda: self._edit_category(cat)).grid(row=0, column=3, padx=4)
        ctk.CTkButton(row, text="✕", width=34, height=28, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("neg"), hover_color=c("card2"),
                      command=lambda: self._delete_category(cat)).grid(row=0, column=4,
                                                                       padx=(4, 14))

    def _edit_category(self, cat):
        dlg = CategoryDialog(self.app, cat)
        self.wait_window(dlg)
        if dlg.saved:
            self._build_categories()

    def _delete_category(self, cat):
        if mb.askyesno("Delete category",
                       f"Delete '{cat['name']}'?\n"
                       "Existing transactions will be kept but become uncategorized.",
                       parent=self):
            db.delete_category(self.app.uid, cat["id"])
            self._build_categories()

    # ================================================================== TAGS
    def _build_tags(self):
        f = self.tabs.tab("Tags")
        clear(f)
        c = THEME.c
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        self.e_tag = ctk.CTkEntry(top, placeholder_text="New tag name", width=220)
        self.e_tag.pack(side="left")
        ctk.CTkButton(top, text="＋ Add tag", fg_color=c("accent"), hover_color=c("accent_hover"),
                      command=self._add_tag).pack(side="left", padx=8)
        self.tag_list = ctk.CTkScrollableFrame(f, fg_color="transparent", height=400)
        self.tag_list.grid(row=1, column=0, sticky="nsew")
        f.grid_rowconfigure(1, weight=1)
        tags = db.list_tags(self.app.uid)
        if not tags:
            ctk.CTkLabel(self.tag_list,
                         text="No tags yet. Tags help you filter transactions in the Ledger Book.",
                         text_color=c("muted"), wraplength=520,
                         justify="left").pack(pady=20, anchor="w")
        for t in tags:
            row = card(self.tag_list)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text="#" + t["name"], text_color=c("text")
                         ).pack(side="left", padx=14, pady=8)
            ctk.CTkButton(row, text="✕", width=34, height=26, fg_color="transparent",
                          border_width=1, border_color=c("border"), text_color=c("neg"),
                          hover_color=c("card2"),
                          command=lambda t=t: self._delete_tag(t)).pack(side="right", padx=14, pady=8)

    def _add_tag(self):
        name = self.e_tag.get().strip()
        if not name:
            return
        if db.add_tag(self.app.uid, name) is None:
            mb.showerror("Duplicate", "That tag already exists.")
        self.e_tag.delete(0, "end")
        self._build_tags()

    def _delete_tag(self, tag):
        if mb.askyesno("Delete tag", f"Delete #{tag['name']}?", parent=self):
            db.delete_tag(self.app.uid, tag["id"])
            self._build_tags()

    # ============================================================ CURRENCIES
    def _build_currencies(self):
        f = self.tabs.tab("Currencies")
        clear(f)
        self._tab_top(f, "MAD (Moroccan Dirham) is preloaded — manage the currencies you use.",
                      "＋ Add currency", lambda: self._edit_currency(None))
        self.cur_list = ctk.CTkScrollableFrame(f, fg_color="transparent", height=430)
        self.cur_list.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        f.grid_rowconfigure(1, weight=1)
        c = THEME.c
        for cur in db.list_currencies(self.app.uid):
            row = card(self.cur_list)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=cur["code"], text_color=c("text"),
                         font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(14, 8), pady=8)
            ctk.CTkLabel(row, text=cur["name"], text_color=c("muted")).pack(side="left")
            if cur["code"] == self.app.user["base_currency"]:
                ctk.CTkLabel(row, text="BASE", text_color=c("accent"),
                             font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=8)
            ctk.CTkButton(row, text="✕", width=34, height=26, fg_color="transparent",
                          border_width=1, border_color=c("border"), text_color=c("neg"),
                          hover_color=c("card2"),
                          command=lambda cur=cur: self._delete_currency(cur)
                          ).pack(side="right", padx=(0, 14), pady=8)
            ctk.CTkButton(row, text="Edit", width=54, height=26, fg_color="transparent",
                          border_width=1, border_color=c("border"), text_color=c("text"),
                          hover_color=c("card2"),
                          command=lambda cur=cur: self._edit_currency(cur)
                          ).pack(side="right", padx=6, pady=8)
            ctk.CTkLabel(row, text=cur["symbol"], text_color=c("text")).pack(side="right", padx=8)

    def _edit_currency(self, cur):
        dlg = CurrencyDialog(self.app, cur)
        self.wait_window(dlg)
        if dlg.saved:
            self._build_currencies()

    def _delete_currency(self, cur):
        if cur["code"] == self.app.user["base_currency"]:
            mb.showerror("Not allowed", "You cannot delete your base currency.")
            return
        if mb.askyesno("Delete currency",
                       f"Delete {cur['code']}? Past records keep their currency code.",
                       parent=self):
            db.delete_currency(self.app.uid, cur["id"])
            self._build_currencies()

    # ============================================================= RECURRING
    def _build_recurring(self):
        f = self.tabs.tab("Recurring")
        clear(f)
        self._tab_top(f, "Recurring rules are applied automatically each time you sign in.",
                      "＋ Add rule", lambda: self._edit_rule(None))
        self.rule_list = ctk.CTkScrollableFrame(f, fg_color="transparent", height=430)
        self.rule_list.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        f.grid_rowconfigure(1, weight=1)
        rules = db.list_rules(self.app.uid)
        if not rules:
            ctk.CTkLabel(self.rule_list,
                         text="No recurring rules yet — e.g. rent, salary or a monthly saving.",
                         text_color=THEME.c("muted")).pack(pady=20, anchor="w")
        for r in rules:
            self._rule_row(r)

    def _rule_row(self, r):
        c = THEME.c
        row = card(self.rule_list)
        row.pack(fill="x", pady=4)
        var = ctk.BooleanVar(value=bool(r["active"]))
        ctk.CTkSwitch(row, text="", variable=var, width=44, progress_color=c("accent"),
                      command=lambda rid=r["id"], v=var: self._toggle_rule(rid, v)
                      ).grid(row=0, column=0, padx=(12, 6), pady=10)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew")
        row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(info, text=r["description"] or "(no description)", anchor="w",
                     text_color=c("text") if r["active"] else c("muted"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x")
        ctk.CTkLabel(info, text=f"{TYPE_LABELS[r['type']]} · {fmt_money(r['amount'], self.app.sym)}"
                                f" · {r['frequency']} · next {r['next_date']}",
                     anchor="w", text_color=c("muted"),
                     font=ctk.CTkFont(size=11)).pack(fill="x")
        ctk.CTkButton(row, text="Edit", width=54, height=28, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=lambda: self._edit_rule(r)).grid(row=0, column=2, padx=4)
        ctk.CTkButton(row, text="✕", width=34, height=28, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("neg"), hover_color=c("card2"),
                      command=lambda: self._delete_rule(r)).grid(row=0, column=3, padx=(4, 14))

    def _toggle_rule(self, rid, var):
        db.set_rule_active(self.app.uid, rid, var.get())

    def _edit_rule(self, r):
        dlg = RuleDialog(self.app, r)
        self.wait_window(dlg)
        if dlg.saved:
            self._build_recurring()

    def _delete_rule(self, r):
        if mb.askyesno("Delete rule",
                       f"Delete recurring '{r['description'] or r['type']}'?", parent=self):
            db.delete_rule(self.app.uid, r["id"])
            self._build_recurring()

    # ============================================================== PROJECTS
    def _build_projects(self):
        f = self.tabs.tab("Projects")
        clear(f)
        self._tab_top(f, "Create funds (e.g. 'New laptop') and link savings to them when "
                         "adding a savings transaction.", "＋ Add project",
                      lambda: self._edit_project(None))
        self.proj_list = ctk.CTkScrollableFrame(f, fg_color="transparent", height=430)
        self.proj_list.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        f.grid_rowconfigure(1, weight=1)
        projects = db.list_projects(self.app.uid)
        if not projects:
            ctk.CTkLabel(self.proj_list, text="No projects yet.",
                         text_color=THEME.c("muted")).pack(pady=20, anchor="w")
        for p in projects:
            self._project_row(p)

    def _project_row(self, p):
        c = THEME.c
        sym = self.app.sym
        st = db.project_stats(self.app.uid, p["id"])
        net = st["saved"] - st["spent"]
        target = p["target_amount"] or 0
        pct = max(0.0, min(1.0, net / target)) if target > 0 else 0.0
        row = card(self.proj_list)
        row.pack(fill="x", pady=4)
        head = ctk.CTkFrame(row, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(head, text=p["name"], text_color=c("text"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        if p["deadline"]:
            ctk.CTkLabel(head, text=f"⏳ {p['deadline']}", text_color=c("muted")).pack(side="left",
                                                                                      padx=10)
        ctk.CTkButton(head, text="✕", width=34, height=26, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("neg"), hover_color=c("card2"),
                      command=lambda: self._delete_project(p)).pack(side="right")
        ctk.CTkButton(head, text="Edit", width=54, height=26, fg_color="transparent", border_width=1,
                      border_color=c("border"), text_color=c("text"), hover_color=c("card2"),
                      command=lambda: self._edit_project(p)).pack(side="right", padx=6)
        txt = (f"Saved {fmt_money(st['saved'], sym)} · Spent {fmt_money(st['spent'], sym)} · "
               f"Net {fmt_money(net, sym)}")
        if target:
            txt += f" of {fmt_money(target, sym)}"
        ctk.CTkLabel(row, text=txt, text_color=c("muted"), anchor="w"
                     ).pack(fill="x", padx=14, pady=(4, 0))
        barwrap = ctk.CTkFrame(row, fg_color="transparent")
        barwrap.pack(fill="x", padx=14, pady=(4, 10))
        bar = ctk.CTkProgressBar(barwrap, height=8, corner_radius=4, fg_color=c("card2"),
                                 progress_color=c("accent"))
        bar.pack(side="left", fill="x", expand=True, pady=4)
        bar.set(pct)
        if target:
            ctk.CTkLabel(barwrap, text=f"{pct * 100:.0f}%", text_color=c("muted"), width=42
                         ).pack(side="right", padx=(8, 0))

    def _edit_project(self, p):
        dlg = ProjectDialog(self.app, p)
        self.wait_window(dlg)
        if dlg.saved:
            self._build_projects()

    def _delete_project(self, p):
        if mb.askyesno("Delete project",
                       f"Delete '{p['name']}'? Linked transactions will be kept but unlinked.",
                       parent=self):
            db.delete_project(self.app.uid, p["id"])
            self._build_projects()


# ==================================================================== dialogs
class CategoryDialog(Dialog):
    def __init__(self, app, cat=None):
        self.cat = cat
        self.saved = False
        super().__init__(app, "Edit category" if cat else "Add category", width=420, height=430)
        c = THEME.c
        self.e_name = ctk.CTkEntry(self.body, placeholder_text="Category name")
        self.field_row(0, "Name", self.e_name)
        self.var_type = ctk.StringVar(value=TYPE_LABELS[cat["type"]] if cat else "Expense")
        self.field_row(1, "Type", ctk.CTkOptionMenu(
            self.body, values=list(TYPE_LABELS.values()), variable=self.var_type,
            fg_color=c("card2"), button_color=c("accent"), button_hover_color=c("accent_hover")))
        self.e_icon = ctk.CTkEntry(self.body, placeholder_text="Emoji e.g. 🍔", width=80)
        self.field_row(2, "Icon", self.e_icon)
        sw = ctk.CTkFrame(self.body, fg_color="transparent")
        sw.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=6)
        ctk.CTkLabel(sw, text="Color", text_color=c("muted")).pack(anchor="w")
        self.selected_color = ctk.StringVar(value=cat["color"] if cat else PRESET_COLORS[3])
        self.swatch_btns = []
        box = ctk.CTkFrame(sw, fg_color="transparent")
        box.pack(anchor="w", pady=4)
        for col in PRESET_COLORS:
            b = ctk.CTkButton(box, width=28, height=28, corner_radius=6, fg_color=col,
                              hover_color=col, text="",
                              border_width=2 if col == self.selected_color.get() else 0,
                              border_color=c("text"), command=lambda cc=col: self._pick(cc))
            b.pack(side="left", padx=3)
            self.swatch_btns.append((b, col))
        if cat:
            self.e_name.insert(0, cat["name"])
            self.e_icon.insert(0, cat["icon"])
        self.buttons("Save category", self._save, 4)

    def _pick(self, col):
        self.selected_color.set(col)
        for b, cc in self.swatch_btns:
            b.configure(border_width=2 if cc == col else 0, border_color=THEME.c("text"))

    def _save(self):
        name = self.e_name.get().strip()
        if not name:
            mb.showerror("Invalid", "Enter a name.", parent=self)
            return
        ttype = LABEL_TYPES[self.var_type.get()]
        icon = self.e_icon.get().strip() or "🧾"
        try:
            if self.cat:
                db.update_category(self.app.uid, self.cat["id"], name, ttype, icon,
                                   self.selected_color.get())
            else:
                db.add_category(self.app.uid, name, ttype, icon, self.selected_color.get())
            self.saved = True
            self.destroy()
        except sqlite3.IntegrityError:
            mb.showerror("Duplicate", "You already have a category with that name and type.",
                         parent=self)


class CurrencyDialog(Dialog):
    def __init__(self, app, cur=None):
        self.cur = cur
        self.saved = False
        super().__init__(app, "Edit currency" if cur else "Add currency", width=400, height=330)
        c = THEME.c
        self.e_code = ctk.CTkEntry(self.body, placeholder_text="Code e.g. MAD")
        self.field_row(0, "Code", self.e_code)
        self.e_name = ctk.CTkEntry(self.body, placeholder_text="Name e.g. Moroccan Dirham")
        self.field_row(1, "Name", self.e_name)
        self.e_symbol = ctk.CTkEntry(self.body, placeholder_text="Symbol e.g. DH", width=90)
        self.field_row(2, "Symbol", self.e_symbol)
        if cur:
            self.e_code.insert(0, cur["code"])
            self.e_name.insert(0, cur["name"])
            self.e_symbol.insert(0, cur["symbol"])
        self.buttons("Save currency", self._save, 3)

    def _save(self):
        code = self.e_code.get().strip().upper()
        name = self.e_name.get().strip() or code
        symbol = self.e_symbol.get().strip() or code
        if not code or len(code) > 6:
            mb.showerror("Invalid", "Enter a currency code (1–6 letters).", parent=self)
            return
        try:
            if self.cur:
                db.update_currency(self.app.uid, self.cur["id"], code, name, symbol)
            else:
                db.add_currency(self.app.uid, code, name, symbol)
            self.saved = True
            self.destroy()
        except sqlite3.IntegrityError:
            mb.showerror("Duplicate", "That currency code already exists.", parent=self)


class RuleDialog(Dialog):
    def __init__(self, app, rule=None):
        self.rule = rule
        self.saved = False
        super().__init__(app, "Edit recurring rule" if rule else "Add recurring rule",
                         width=440, height=540)
        c = THEME.c
        self.var_type = ctk.StringVar(value=TYPE_LABELS[rule["type"]] if rule else "Expense")
        self.field_row(0, "Type", ctk.CTkOptionMenu(
            self.body, values=list(TYPE_LABELS.values()), variable=self.var_type,
            command=lambda _v: self._load_cats(), fg_color=c("card2"),
            button_color=c("accent"), button_hover_color=c("accent_hover")))
        self.e_amount = ctk.CTkEntry(self.body, placeholder_text="Amount")
        self.field_row(1, "Amount", self.e_amount)
        self.e_desc = ctk.CTkEntry(self.body, placeholder_text="Description e.g. Rent, Netflix…")
        self.field_row(2, "Description", self.e_desc)
        self.cat_menu = ctk.CTkOptionMenu(self.body, values=["—"], fg_color=c("card2"),
                                          button_color=c("accent"),
                                          button_hover_color=c("accent_hover"))
        self.field_row(3, "Category", self.cat_menu)
        self.var_freq = ctk.StringVar(value=rule["frequency"] if rule else "monthly")
        self.field_row(4, "Frequency", ctk.CTkOptionMenu(
            self.body, values=FREQUENCIES, variable=self.var_freq, fg_color=c("card2"),
            button_color=c("accent"), button_hover_color=c("accent_hover")))
        self.e_next = ctk.CTkEntry(self.body, placeholder_text="First / next date (YYYY-MM-DD)")
        self.field_row(5, "Next date", self.e_next)

        self.cat_map = {}
        if rule:
            self.e_amount.insert(0, f"{rule['amount']:.2f}")
            self.e_desc.insert(0, rule["description"] or "")
            self.e_next.insert(0, rule["next_date"])
        else:
            self.e_next.insert(0, today_str())
        self._load_cats(keep=rule["category_id"] if rule else None)
        self.buttons("Save rule", self._save, 6)

    def _load_cats(self, keep=None):
        cats = db.list_categories(self.app.uid, LABEL_TYPES[self.var_type.get()])
        self.cat_map = {x["name"]: x["id"] for x in cats}
        values = list(self.cat_map) or ["—"]
        self.cat_menu.configure(values=values)
        if keep and keep in self.cat_map.values():
            self.cat_menu.set(next(n for n, i in self.cat_map.items() if i == keep))
        else:
            self.cat_menu.set(values[0])

    def _save(self):
        amount = parse_float(self.e_amount.get())
        if amount is None or amount <= 0:
            mb.showerror("Invalid", "Enter a positive amount.", parent=self)
            return
        nd = parse_date(self.e_next.get())
        if not nd:
            mb.showerror("Invalid", "Enter a valid date (YYYY-MM-DD).", parent=self)
            return
        ttype = LABEL_TYPES[self.var_type.get()]
        cat_id = self.cat_map.get(self.cat_menu.get())
        desc = self.e_desc.get().strip()
        freq = self.var_freq.get()
        if self.rule:
            db.update_rule(self.app.uid, self.rule["id"], ttype, amount, cat_id, desc, freq,
                           nd.isoformat())
        else:
            db.add_rule(self.app.uid, ttype, amount, cat_id, desc, freq, nd.isoformat())
        self.saved = True
        self.destroy()


class ProjectDialog(Dialog):
    def __init__(self, app, project=None):
        self.project = project
        self.saved = False
        super().__init__(app, "Edit project" if project else "Add project", width=420, height=360)
        self.e_name = ctk.CTkEntry(self.body, placeholder_text="Project name e.g. New laptop")
        self.field_row(0, "Name", self.e_name)
        self.e_target = ctk.CTkEntry(self.body, placeholder_text="Target amount (optional)")
        self.field_row(1, "Target", self.e_target)
        self.e_deadline = ctk.CTkEntry(self.body, placeholder_text="Deadline YYYY-MM-DD (optional)")
        self.field_row(2, "Deadline", self.e_deadline)
        if project:
            self.e_name.insert(0, project["name"])
            if project["target_amount"]:
                self.e_target.insert(0, f"{project['target_amount']:.2f}")
            self.e_deadline.insert(0, project["deadline"] or "")
        self.buttons("Save project", self._save, 3)

    def _save(self):
        name = self.e_name.get().strip()
        if not name:
            mb.showerror("Invalid", "Enter a project name.", parent=self)
            return
        target = parse_float(self.e_target.get()) or 0.0
        if target < 0:
            mb.showerror("Invalid", "Target must be positive.", parent=self)
            return
        dl = self.e_deadline.get().strip()
        if dl and not parse_date(dl):
            mb.showerror("Invalid", "Deadline must be YYYY-MM-DD.", parent=self)
            return
        if self.project:
            db.update_project(self.app.uid, self.project["id"], name, target, dl)
        else:
            db.add_project(self.app.uid, name, target, dl)
        self.saved = True
        self.destroy()