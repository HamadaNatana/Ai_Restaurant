import tkinter as tk
from tkinter import messagebox
from data import authenticate


class LoginScreen(tk.Frame):
    """
    Simple login screen used by all roles.
    This fixes the import error when ManagerScreen calls logout.
    """

    def __init__(self, master):
        super().__init__(master, bg="#f5f5f5")
        self.master = master
        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Restaurant System Login",
                 font=("Arial", 22, "bold"), bg="#f5f5f5").pack(pady=25)

        form = tk.Frame(self, bg="#f5f5f5")
        form.pack(pady=10)

        tk.Label(form, text="Username:", font=("Arial", 12),
                 bg="#f5f5f5").grid(row=0, column=0, padx=8, pady=8)
        tk.Label(form, text="Password:", font=("Arial", 12),
                 bg="#f5f5f5").grid(row=1, column=0, padx=8, pady=8)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Entry(form, textvariable=self.username_var, width=25).grid(row=0, column=1)
        tk.Entry(form, show="*", textvariable=self.password_var,
                 width=25).grid(row=1, column=1)

        tk.Button(self, text="Login", width=15, font=("Arial", 12),
                  command=self._login).pack(pady=15)

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Enter username and password.")
            return

        user = authenticate(username, password)

        if not user:
            messagebox.showerror("Invalid", "Incorrect username or password.")
            return

        # Redirect based on role
        role = user["role"]

        if role in ("CUSTOMER", "VIP"):
            from customer_gui import CustomerScreen
            self.destroy()
            CustomerScreen(self.master, user)

        elif role == "CHEF":
            from chef_gui import ChefScreen  # if exists
            self.destroy()
            ChefScreen(self.master, user)

        elif role == "DELIVERY":
            from delivery_gui import DeliveryScreen  # if exists
            self.destroy()
            DeliveryScreen(self.master, user)

        elif role == "MANAGER":
            from manager_gui import ManagerScreen
            self.destroy()
            ManagerScreen(self.master, user)

        else:
            messagebox.showerror("Error", f"Unknown role: {role}")
