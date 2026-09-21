"""Digital Wallet — local, multi-user personal finance app."""
from wallet import db
from wallet.ui_login import LoginApp
from wallet.ui_main import MainWindow


def silent_bgerror(*args):
    if args and ("invalid command name" in str(args[0]) or "application has been destroyed" in str(args[0])):
        return
    import sys
    print("bgerror:", *args, file=sys.stderr)

def main():
    db.init_db()
    while True:
        login = LoginApp()
        login.tk.createcommand("bgerror", silent_bgerror)
        login.mainloop()
        user = getattr(login, "result_user", None)
        if not user:
            return  # window closed -> exit
        win = MainWindow(user)
        win.tk.createcommand("bgerror", silent_bgerror)
        win.mainloop()
        if not getattr(win, "wants_logout", False):
            return  # app closed -> exit, otherwise loop back to login


if __name__ == "__main__":
    main()