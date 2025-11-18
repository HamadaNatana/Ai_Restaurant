import tkinter as tk
from tkinter import simpledialog, messagebox

from data import deposit_money


class CustomerScreen(tk.Frame):
    def __init__(self, master, user):
        super().__init__(master)
        self.master = master
        self.user = user  # dict from data.py

        # App background (like a web dashboard)
        self.master.configure(bg="#e9ecef")
        self.configure(bg="#e9ecef")
        self.pack(fill="both", expand=True)

        self.deposit_label_var = tk.StringVar()
        self.warning_label_var = tk.StringVar()
        self.role_label_var = tk.StringVar()
        self.vip_badge_var = tk.StringVar()

        self._build_widgets()
        self._refresh_labels()

    def _build_widgets(self):
        # ===== TOP BAR / NAVBAR =====
        top_bar = tk.Frame(self, bg="#343a40", height=50)
        top_bar.pack(fill="x", side="top")

        tk.Label(
            top_bar,
            text="AI-Enabled Restaurant System",
            font=("Segoe UI", 14, "bold"),
            bg="#343a40",
            fg="#ffffff",
        ).pack(side="left", padx=20, pady=10)

        tk.Label(
            top_bar,
            textvariable=self.role_label_var,
            font=("Segoe UI", 11),
            bg="#343a40",
            fg="#ced4da",
        ).pack(side="right", padx=20)

        # ===== CENTER CONTAINER =====
        outer = tk.Frame(self, bg="#e9ecef")
        outer.pack(fill="both", expand=True)

        # "Card" in the middle like a web panel
        card = tk.Frame(
            outer,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#dee2e6",
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=900, height=420)

        # ---- Card Header ----
        header = tk.Frame(card, bg="#ffffff")
        header.pack(fill="x", pady=(15, 5), padx=20)

        tk.Label(
            header,
            text="Customer Dashboard",
            font=("Segoe UI", 20, "bold"),
            bg="#ffffff",
            fg="#212529",
        ).pack(side="left")

        # VIP badge (if applicable)
        vip_label = tk.Label(
            header,
            textvariable=self.vip_badge_var,
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#ffc107",
        )
        vip_label.pack(side="right")

        # ---- Stats section (warnings + deposit) ----
        stats_frame = tk.Frame(card, bg="#ffffff")
        stats_frame.pack(fill="x", padx=20, pady=(5, 10))

        # Left "card" for warnings
        warning_card = tk.Frame(
            stats_frame,
            bg="#f8f9fa",
            bd=0,
            highlightthickness=1,
            highlightbackground="#e9ecef",
        )
        warning_card.pack(side="left", expand=True, fill="both", padx=(0, 10), pady=5)

        tk.Label(
            warning_card,
            text="Warnings",
            font=("Segoe UI", 11, "bold"),
            bg="#f8f9fa",
            fg="#495057",
        ).pack(pady=(10, 2))

        tk.Label(
            warning_card,
            textvariable=self.warning_label_var,
            font=("Segoe UI", 22, "bold"),
            bg="#f8f9fa",
            fg="#dc3545",
        ).pack(pady=(0, 10))

        # Right "card" for deposit
        deposit_card = tk.Frame(
            stats_frame,
            bg="#f8f9fa",
            bd=0,
            highlightthickness=1,
            highlightbackground="#e9ecef",
        )
        deposit_card.pack(side="left", expand=True, fill="both", padx=(10, 0), pady=5)

        tk.Label(
            deposit_card,
            text="Deposit Balance",
            font=("Segoe UI", 11, "bold"),
            bg="#f8f9fa",
            fg="#495057",
        ).pack(pady=(10, 2))

        tk.Label(
            deposit_card,
            textvariable=self.deposit_label_var,
            font=("Segoe UI", 22, "bold"),
            bg="#f8f9fa",
            fg="#198754",
        ).pack(pady=(0, 10))

        # ---- Buttons area ----
        btn_frame = tk.Frame(card, bg="#ffffff")
        btn_frame.pack(pady=(10, 5), padx=20, fill="x")

        # Helper to create consistent flat-ish buttons
        def make_btn(text, cmd, col):
            return tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                font=("Segoe UI", 10),
                bg=col,
                fg="#ffffff",
                activebackground=col,
                activeforeground="#ffffff",
                relief="flat",
                padx=12,
                pady=6,
                cursor="hand2",
            )

        make_btn("Deposit Money", self._handle_deposit, "#0d6efd").grid(
            row=0, column=0, padx=5, pady=5
        )
        make_btn("Allergy Settings", self._open_allergy, "#6610f2").grid(
            row=0, column=1, padx=5, pady=5
        )
        make_btn("AI Help / Chat", self._open_ai_chat, "#198754").grid(
            row=0, column=2, padx=5, pady=5
        )
        make_btn("Discussion Board", self._open_discussion, "#fd7e14").grid(
            row=0, column=3, padx=5, pady=5
        )
        make_btn("View Menu (Allergy-safe)", self._open_menu, "#20c997").grid(
            row=0, column=4, padx=5, pady=5
        )
        make_btn("Logout", self.logout, "#dc3545").grid(
            row=0, column=5, padx=5, pady=5
        )

        # ---- Footer / hint ----
        tk.Label(
            card,
            text="(Ordering, Delivery, HR, etc. from other teammates will appear on separate screens.)",
            font=("Segoe UI", 9),
            fg="#6c757d",
            bg="#ffffff",
        ).pack(pady=(10, 5))

    def _refresh_labels(self):
        """Update label values from self.user (UC15, UC08)."""
        role = self.user.get("role", "CUSTOMER")
        username = self.user.get("username")

        # Top bar text
        self.role_label_var.set(f"{username}  |  Role: {role}")

        # VIP badge
        if role.upper() == "VIP":
            self.vip_badge_var.set("★ VIP Customer")
        else:
            self.vip_badge_var.set("")

        # Stats
        self.warning_label_var.set(str(self.user.get("warnings", 0)))
        self.deposit_label_var.set(f"${self.user.get('deposit', 0.0):.2f}")

    def _handle_deposit(self):
        """Ask for amount, update deposit (UC08)."""
        try:
            amount = simpledialog.askfloat(
                "Deposit Money",
                "Enter amount to deposit ($):",
                minvalue=0.01,
                parent=self,
            )
            if amount is None:
                return  # user cancelled
            updated_user = deposit_money(self.user["username"], amount)
            self.user = updated_user  # replace with latest data
            self._refresh_labels()
            messagebox.showinfo(
                "Deposit Successful",
                f"${amount:.2f} deposited successfully.\n"
                f"New balance: ${self.user['deposit']:.2f}",
            )
        except ValueError as e:
            messagebox.showerror("Deposit Error", str(e))

    def _open_allergy(self):
        """Open UC22 – Allergy Settings screen."""
        from allergy_gui import AllergySettingsScreen

        self.destroy()
        AllergySettingsScreen(self.master, self.user)

    def _open_ai_chat(self):
        """Open UC20/UC21 – AI Customer Service Chat screen."""
        from ai_chat_gui import AiChatScreen

        self.destroy()
        AiChatScreen(self.master, self.user)

    def _open_discussion(self):
        """Open UC16 – Discussion Board screen."""
        from discussion_gui import DiscussionBoardScreen

        self.destroy()
        DiscussionBoardScreen(self.master, self.user)

    def _open_menu(self):
        """Open allergy-filtered Menu screen (UC22 applied to menu)."""
        from menu_gui import MenuScreen

        self.destroy()
        MenuScreen(self.master, self.user)

    def logout(self):
        """Destroy this screen and return to login."""
        from login_gui import LoginScreen  # lazy import to avoid circular

        self.destroy()
        LoginScreen(self.master)
