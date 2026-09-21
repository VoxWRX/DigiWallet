"""Digital Wallet — local, multi-user personal finance app."""
from wallet import db
from wallet.ui_login import LoginApp
from wallet.ui_main import MainWindow
import customtkinter as ctk


def silent_bgerror(*args):
    if args and ("invalid command name" in str(args[0]) or "application has been destroyed" in str(args[0])):
        return
    import sys
    print("bgerror:", *args, file=sys.stderr)

def main():
    db.init_db()
    
    root = ctk.CTk()
    root.withdraw()
    root.tk.createcommand("bgerror", silent_bgerror)
    
    while True:
        login = LoginApp(root)
        root.wait_window(login)
        
        user = getattr(login, "result_user", None)
        if not user:
            break  # window closed -> exit
            
        win = MainWindow(root, user)
        root.wait_window(win)
        
        if not getattr(win, "wants_logout", False):
            break  # app closed -> exit, otherwise loop back to login
            
    root.destroy()


if __name__ == "__main__":
    main()