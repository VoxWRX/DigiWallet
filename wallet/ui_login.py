import time

import customtkinter as ctk
import tkinter.messagebox as mb

from . import auth, db
from .themes import THEME
from .utils import center
from .widgets import card


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.result_user = None
        self._fails = 0
        self._locked_until = 0.0
        self._register_mode = False

        THEME.set("light", "blue")
        THEME.apply()
        self.title("Digital Wallet — Sign in")
        self.resizable(False, False)
        self.configure(fg_color=THEME.c("bg"))
        center(self, 430, 480)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._card = card(self)
        self._card.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")
        self._build()

    def _build(self):
        for w in self._card.winfo_children():
            w.destroy()
        c = THEME.c
        self._card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._card, text="◈", font=ctk.CTkFont(size=34),
                     text_color=c("accent")).grid(row=0, column=0, pady=(26, 0))
        ctk.CTkLabel(self._card, text="Digital Wallet",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=c("text")).grid(row=1, column=0, pady=(0, 2))
        ctk.CTkLabel(self._card, text="Create your account" if self._register_mode else "Welcome back",
                     text_color=c("muted")).grid(row=2, column=0, pady=(0, 16))

        r = 3
        if self._register_mode:
            self.e_name = ctk.CTkEntry(self._card, placeholder_text="Display name")
            self.e_name.grid(row=r, column=0, padx=32, pady=5, sticky="ew")
            r += 1
        self.e_user = ctk.CTkEntry(self._card, placeholder_text="Username")
        self.e_user.grid(row=r, column=0, padx=32, pady=5, sticky="ew")
        r += 1
        self.e_pass = ctk.CTkEntry(self._card, placeholder_text="Password", show="•")
        self.e_pass.grid(row=r, column=0, padx=32, pady=5, sticky="ew")
        r += 1
        if self._register_mode:
            self.e_pass2 = ctk.CTkEntry(self._card, placeholder_text="Confirm password", show="•")
            self.e_pass2.grid(row=r, column=0, padx=32, pady=5, sticky="ew")
            r += 1
            ctk.CTkLabel(self._card, text="Base currency", text_color=c("muted")
                         ).grid(row=r, column=0, padx=32, sticky="w")
            r += 1
            self.var_cur = ctk.StringVar(value="MAD")
            ctk.CTkOptionMenu(self._card,
                              values=[code for code, _, _ in db.DEFAULT_CURRENCIES],
                              variable=self.var_cur, fg_color=c("card2"),
                              button_color=c("accent"),
                              button_hover_color=c("accent_hover")
                              ).grid(row=r, column=0, padx=32, pady=(2, 4), sticky="ew")
            r += 1

        self.btn_main = ctk.CTkButton(
            self._card, text="Create account" if self._register_mode else "Sign in",
            height=40, fg_color=c("accent"), hover_color=c("accent_hover"),
            command=self._register_account if self._register_mode else self._login)
        self.btn_main.grid(row=r, column=0, padx=32, pady=(12, 4), sticky="ew")
        r += 1
        ctk.CTkButton(
            self._card, text="← Back to sign in" if self._register_mode else "Create a new account",
            fg_color="transparent", text_color=c("accent"), hover_color=c("card2"),
            command=self._toggle).grid(row=r, column=0, padx=32, pady=(2, 18), sticky="ew")

        self.e_user.focus()
        self.bind("<Return>", lambda e: self.btn_main.invoke())

    def _toggle(self):
        self._register_mode = not self._register_mode
        center(self, 430, 600 if self._register_mode else 480)
        self._build()

    def _login(self):
        if time.time() < self._locked_until:
            mb.showwarning("Locked", "Too many failed attempts — please wait ~30 seconds.", parent=self)
            return
        user = db.get_user_by_username(self.e_user.get().strip())
        if not user or not auth.verify_password(self.e_pass.get(), user["password_hash"], user["salt"]):
            self._fails += 1
            if self._fails >= 5:
                self._locked_until = time.time() + 30
                self._fails = 0
            mb.showerror("Sign in failed", "Invalid username or password.", parent=self)
            return
        self.result_user = user
        self.after(10, self.destroy)

    def _register_account(self):
        username = self.e_user.get().strip()
        pw = self.e_pass.get()
        if len(username) < 3:
            mb.showerror("Invalid", "Username must be at least 3 characters.", parent=self)
            return
        if len(pw) < 4:
            mb.showerror("Invalid", "Password must be at least 4 characters.", parent=self)
            return
        if pw != self.e_pass2.get():
            mb.showerror("Invalid", "Passwords do not match.", parent=self)
            return
        if db.get_user_by_username(username):
            mb.showerror("Invalid", "That username is already taken.", parent=self)
            return
        pw_hash, salt = auth.make_password(pw)
        uid = db.create_user(username, pw_hash, salt, self.e_name.get().strip() or username,
                             self.var_cur.get())
        self.result_user = db.get_user_by_id(uid)
        self.after(10, self.destroy)