import tkinter as tk
from tkinter import messagebox


class DeliveryScreen(tk.Frame):
    """
    Minimal Delivery Person dashboard.
    Delivery responsibilities:
    - Submit bids for delivery offers (UC17)
    - View assigned orders (future expansion)
    """

    def __init__(self, master, user):
        super().__init__(master, bg="#1f1f1f")
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text=f"Delivery Dashboard - {self.user['username']}",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#1f1f1f"
        ).pack(pady=25)

        tk.Button(
            self,
            text="View Delivery Offers / Submit Bid",
            font=("Arial", 14),
            width=30,
            command=self._not_implemented
        ).pack(pady=15)

        tk.Button(
            self,
            text="Logout",
            font=("Arial", 14),
            width=20,
            command=self._logout
        ).pack(pady=30)

    def _not_implemented(self):
        messagebox.showinfo(
            "Coming Soon",
            "Delivery bidding screen will be added in the HR/Orders phase."
        )

    def _logout(self):
        from login_screen import LoginScreen
        self.destroy()
        LoginScreen(self.master)
