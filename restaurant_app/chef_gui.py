import tkinter as tk
from tkinter import messagebox
from menu_gui import MenuScreen


class ChefScreen(tk.Frame):
    """
    Minimal Chef dashboard for system navigation.
    Chef responsibilities:
    - Create/update/delete dishes (UC19)
    """

    def __init__(self, master, user):
        super().__init__(master, bg="#1e1e1e")
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text=f"Chef Dashboard - {self.user['username']}",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=25)

        tk.Button(
            self,
            text="Manage Menu (View / Edit Dishes)",
            font=("Arial", 14),
            width=30,
            command=self._open_menu
        ).pack(pady=15)

        tk.Button(
            self,
            text="Logout",
            font=("Arial", 14),
            width=20,
            command=self._logout
        ).pack(pady=30)

    def _open_menu(self):
        """Chef views the menu (later add edit mode)."""
        self.destroy()
        MenuScreen(self.master, self.user)

    def _logout(self):
        from login_screen import LoginScreen
        self.destroy()
        LoginScreen(self.master)
