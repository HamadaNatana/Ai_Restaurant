import tkinter as tk
from tkinter import messagebox

from data import authenticate
from customer_gui import CustomerScreen

class LoginScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build_widgets()

    def _build_widgets(self):
        tk.Label(self, text="AI Restaurant Login", font=("Arial", 18)).pack(pady=20)

        form = tk.Frame(self)
        form.pack(pady=10)

        tk.Label(form, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        tk.Entry(form, textvariable=self.username_var).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        tk.Entry(form, textvariable=self.password_var, show="*").grid(row=1, column=1, padx=5, pady=5)

        tk.Button(self, text="Login", command=self._handle_login).pack(pady=20)

    def _handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        user = authenticate(username, password)
        if user:
            messagebox.showinfo("Login", f"Welcome {user['username']}! Role: {user['role']}")
            self._go_to_role_screen(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def _go_to_role_screen(self, user):
        # For now, no matter the role, go to Customer screen
        self.destroy()
        CustomerScreen(self.master, user)
