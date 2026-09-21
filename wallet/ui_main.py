import tkinter.messagebox as mb

import customtkinter as ctk

from . import db
from .themes import THEME
from .ui_dashboard import DashboardPage
from .ui_ledger import LedgerPage
from .ui_reports import ReportsPage
from .ui_settings import SettingsPage

NAV = [
    ("dashboard", "📅", "Dashboard"),
    ("ledger", "📒", "Ledger Book"),
    ("reports", "📊", "Reports"),
    ("settings", "⚙️", "Settings"),
]
PAGES = {"dashboard": DashboardPage, "ledger": LedgerPage,
         "reports": ReportsPage, "settings": SettingsPage}


class MainWindow(ctk.CTk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        THEME.set(user["theme_mode"], user["theme_accent"])
        THEME.apply()
        self.wants_logout = False
        self._current = "dashboard"
        self.body = None
        self.sidebar = None

        self.title("Digital Wallet")
        self.geometry("1280x800")
        self.minsize(1100, 720)
        self.configure(fg_color=THEME.c("bg"))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        created = db.apply_recurrent(user["id"])
        if created:
            mb.showinfo("Recurring applied",
                        f"{created} recurring transaction(s) were recorded.")

        self._build_sidebar()
        self.show("dashboard")

    # ----------------------------------------------------- helpers
    @property
    def uid(self):
        return self.user["id"]

    @property
    def sym(self):
        cur = db.get_currency(self.user["id"], self.user["base_currency"])
        return cur["symbol"] if cur else self.user["base_currency"]

    # ----------------------------------------------------- sidebar
    def _build_sidebar(self):
        if self.sidebar:
            self.sidebar.destroy()
        c = THEME.c
        self.sidebar = ctk.CTkFrame(self, width=232, corner_radius=0, fg_color=c("sidebar"))
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="◈  Digital Wallet", anchor="w",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#FFFFFF").pack(fill="x", padx=20, pady=(22, 14))

        chip = ctk.CTkFrame(self.sidebar, fg_color=c("sidebar_hover"), corner_radius=10)
        chip.pack(fill="x", padx=14, pady=(0, 14))
        name = self.user["display_name"] or self.user["username"]
        avatar = ctk.CTkLabel(chip, text=name[0].upper(), width=36, height=36, corner_radius=18,
                              fg_color=c("accent"), text_color="#FFFFFF",
                              font=ctk.CTkFont(size=15, weight="bold"))
        avatar.pack(side="left", padx=(10, 10), pady=10)
        info = ctk.CTkFrame(chip, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=8)
        ctk.CTkLabel(info, text=name, anchor="w", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#FFFFFF").pack(fill="x")
        ctk.CTkLabel(info, text="@" + self.user["username"], anchor="w",
                     font=ctk.CTkFont(size=11), text_color=c("sidebar_text")).pack(fill="x")

        self._nav = {}
        for key, icon, label in NAV:
            b = ctk.CTkButton(self.sidebar, text=f"{icon}   {label}", anchor="w", height=44,
                              corner_radius=10, fg_color="transparent",
                              hover_color=c("sidebar_hover"), text_color=c("sidebar_text"),
                              font=ctk.CTkFont(size=15), command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=12, pady=3)
            self._nav[key] = b

        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=14)
        target = "dark" if self.user["theme_mode"] == "light" else "light"
        icon = "🌙" if target == "dark" else "☀️"
        ctk.CTkButton(bottom, text=f"{icon}   {target.title()} mode", anchor="w", height=38,
                      corner_radius=10, fg_color="transparent", hover_color=c("sidebar_hover"),
                      text_color=c("sidebar_text"), command=self.toggle_mode).pack(fill="x", pady=3)
        ctk.CTkButton(bottom, text="⏻   Log out", anchor="w", height=38, corner_radius=10,
                      fg_color="transparent", hover_color=c("sidebar_hover"),
                      text_color=c("sidebar_text"), command=self.logout).pack(fill="x", pady=3)

    # ----------------------------------------------------- pages
    def show(self, key):
        self._current = key
        self._highlight_nav()
        if self.body:
            self.body.destroy()
        self.body = PAGES[key](self, self)
        self.body.grid(row=0, column=1, sticky="nsew")

    def _highlight_nav(self):
        c = THEME.c
        for k, btn in self._nav.items():
            if k == self._current:
                btn.configure(fg_color=c("accent"), text_color="#FFFFFF",
                              hover_color=c("accent_hover"))
            else:
                btn.configure(fg_color="transparent", text_color=c("sidebar_text"),
                              hover_color=c("sidebar_hover"))

    def refresh_current(self):
        self.show(self._current)

    def refresh_user(self):
        self.user = db.get_user_by_id(self.user["id"])
        self._build_sidebar()
        self._highlight_nav()

    def toggle_mode(self):
        new = "dark" if self.user["theme_mode"] == "light" else "light"
        db.update_user(self.user["id"], theme_mode=new)
        self.refresh_theme()

    def refresh_theme(self):
        self.user = db.get_user_by_id(self.user["id"])
        THEME.set(self.user["theme_mode"], self.user["theme_accent"])
        THEME.apply()
        self.configure(fg_color=THEME.c("bg"))
        self._build_sidebar()
        self.show(self._current)

    def logout(self):
        self.wants_logout = True
        self.after(10, self.destroy)