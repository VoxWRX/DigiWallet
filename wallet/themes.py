import customtkinter as ctk

PALETTES = {
    "blue": {
        "light": dict(
            accent="#2563EB", accent_hover="#1D4ED8", accent_soft="#DBEAFE",
            bg="#F1F5F9", card="#FFFFFF", card2="#F8FAFC", text="#0F172A",
            muted="#64748B", border="#E2E8F0", pos="#16A34A", neg="#DC2626",
            sidebar="#0F172A", sidebar_text="#CBD5E1", sidebar_hover="#1E293B"),
        "dark": dict(
            accent="#3B82F6", accent_hover="#2563EB", accent_soft="#1E3A8A",
            bg="#0B1220", card="#111A2C", card2="#0D1526", text="#E2E8F0",
            muted="#94A3B8", border="#22304C", pos="#4ADE80", neg="#F87171",
            sidebar="#0B1220", sidebar_text="#94A3B8", sidebar_hover="#182642"),
    },
    "pink": {
        "light": dict(
            accent="#DB2777", accent_hover="#BE185D", accent_soft="#FCE7F3",
            bg="#FAF5F8", card="#FFFFFF", card2="#FDF9FB", text="#3B1224",
            muted="#96707F", border="#F1DEE6", pos="#16A34A", neg="#DC2626",
            sidebar="#3B0A24", sidebar_text="#E7C9D8", sidebar_hover="#541537"),
        "dark": dict(
            accent="#EC4899", accent_hover="#DB2777", accent_soft="#4A1030",
            bg="#170D12", card="#221622", card2="#1C121C", text="#F4E7EE",
            muted="#B390A0", border="#3C2534", pos="#4ADE80", neg="#F87171",
            sidebar="#120A0F", sidebar_text="#B390A0", sidebar_hover="#241522"),
    },
    "green": {
        "light": dict(
            accent="#16A34A", accent_hover="#15803D", accent_soft="#DCFCE7",
            bg="#F2F7F4", card="#FFFFFF", card2="#F8FBF9", text="#122619",
            muted="#64806E", border="#DDEAE1", pos="#0D9488", neg="#DC2626",
            sidebar="#0C2A1D", sidebar_text="#C6E3D2", sidebar_hover="#143C29"),
        "dark": dict(
            accent="#22C55E", accent_hover="#16A34A", accent_soft="#0B3B24",
            bg="#0B1512", card="#10201A", card2="#0D1A15", text="#E4F1E9",
            muted="#93B3A0", border="#20382C", pos="#34D399", neg="#F87171",
            sidebar="#08120E", sidebar_text="#93B3A0", sidebar_hover="#14251E"),
    },
}


class ThemeManager:
    def __init__(self):
        self.mode, self.accent = "light", "blue"

    def set(self, mode=None, accent=None):
        if mode:
            self.mode = mode
        if accent:
            self.accent = accent

    def apply(self):
        ctk.set_appearance_mode(self.mode)

    def c(self, key):
        return PALETTES[self.accent][self.mode][key]

    def light(self, key):
        return PALETTES[self.accent]["light"][key]


THEME = ThemeManager()