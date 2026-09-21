import customtkinter as ctk

class MyWin(ctk.CTkToplevel):
    def destroy(self):
        self.after(10, super().destroy)

app = ctk.CTk()
win = MyWin(app)
win.after(500, win.destroy)
app.after(1000, app.destroy)
app.mainloop()
print("Success")
