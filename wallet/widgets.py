import customtkinter as ctk

from .themes import THEME
from .utils import center, safe_grab

TYPE_LABELS = {"expense": "Expense", "income": "Income", "savings": "Savings"}
LABEL_TYPES = {v: k for k, v in TYPE_LABELS.items()}
FREQUENCIES = ["daily", "weekly", "monthly", "yearly"]


class Page(ctk.CTkFrame):
    """Base class for main content pages."""
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app


def card(parent, **kwargs):
    kw = dict(fg_color=THEME.c("card"), corner_radius=12,
              border_width=1, border_color=THEME.c("border"))
    kw.update(kwargs)
    return ctk.CTkFrame(parent, **kw)


def page_header(parent, title, subtitle=""):
    head = ctk.CTkFrame(parent, fg_color="transparent")
    head.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(head, text=title, font=ctk.CTkFont(size=24, weight="bold"),
                 text_color=THEME.c("text")).grid(row=0, column=0, sticky="w")
    if subtitle:
        ctk.CTkLabel(head, text=subtitle, text_color=THEME.c("muted")).grid(row=1, column=0, sticky="w")
    return head


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title):
        super().__init__(parent, fg_color=THEME.c("card"), corner_radius=12,
                         border_width=1, border_color=THEME.c("border"))
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title.upper(), font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=THEME.c("muted")).grid(row=0, column=0, padx=16, pady=(14, 0), sticky="w")
        self.value = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=20, weight="bold"),
                                  text_color=THEME.c("text"))
        self.value.grid(row=1, column=0, padx=16, pady=(2, 14), sticky="w")

    def set(self, text, color=None):
        self.value.configure(text=text, text_color=color or THEME.c("text"))


class Dialog(ctk.CTkToplevel):
    """Small modal dialog with a card body and helper methods."""
    def __init__(self, app, title, width=420, height=380, parent=None):
        super().__init__(parent or app)
        self.app = app
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=THEME.c("bg"))
        self.transient(parent or app)
        self.body = card(self)
        self.body.pack(fill="both", expand=True, padx=14, pady=14)
        center(self, width, height)
        safe_grab(self)

    def destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        # Defer destruction to let CustomTkinter button events finish
        self.after(10, super().destroy)

    def field_row(self, r, label, widget, widget2=None):
        self.body.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.body, text=label, text_color=THEME.c("muted"), anchor="e"
                     ).grid(row=r, column=0, sticky="e", padx=(16, 8), pady=6)
        widget.grid(row=r, column=1, sticky="ew", padx=(0, 16), pady=6)
        if widget2 is not None:
            widget2.grid(row=r, column=2, sticky="w", padx=(0, 16), pady=6)

    def buttons(self, save_text, on_save, r):
        bar = ctk.CTkFrame(self.body, fg_color="transparent")
        bar.grid(row=r, column=0, columnspan=3, sticky="e", padx=16, pady=(10, 14))
        ctk.CTkButton(bar, text="Cancel", fg_color="transparent", border_width=1,
                      border_color=THEME.c("border"), text_color=THEME.c("text"),
                      hover_color=THEME.c("card2"), command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bar, text=save_text, fg_color=THEME.c("accent"),
                      hover_color=THEME.c("accent_hover"), command=on_save).pack(side="right")