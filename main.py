"""Digital Wallet — local, multi-user personal finance app."""
from wallet import db
from wallet.ui_login import LoginApp
from wallet.ui_main import MainWindow


def main():
    db.init_db()
    while True:
        login = LoginApp()
        login.mainloop()
        user = getattr(login, "result_user", None)
        if not user:
            return  # window closed -> exit
        win = MainWindow(user)
        win.mainloop()
        if not getattr(win, "wants_logout", False):
            return  # app closed -> exit, otherwise loop back to login


if __name__ == "__main__":
    main()