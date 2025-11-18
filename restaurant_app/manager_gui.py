import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from data import (
    load_users, save_users,
    load_topics, save_topics,
    load_posts, load_all_posts,
)
from manager_kb_review_gui import ManagerKBReviewScreen


# ============================================================
# COLOR PALETTE (DARK MODE)
# ============================================================
SIDEBAR_BG = "#1e1e1e"
SIDEBAR_FG = "#ffffff"
MAIN_BG = "#f5f5f5"
CARD_BG = "#ffffff"


# ============================================================
# MANAGER DASHBOARD MAIN CLASS
# ============================================================
class ManagerScreen(tk.Frame):
    """
    Full-featured Manager Dashboard
    UC02, UC09–UC14, UC17–UC18, UC21, UC16, Finance Summary
    DoorDash/UberEats–style dark sidebar with dynamic panels.
    """

    def __init__(self, master, user):
        super().__init__(master, bg=MAIN_BG)
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self._build_layout()
        self.show_dashboard()

    # ========================================================
    # LAYOUT STRUCTURE
    # ========================================================
    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=240)
        self.sidebar.pack(side="left", fill="y")

        # Main content
        self.main = tk.Frame(self, bg=MAIN_BG)
        self.main.pack(side="right", fill="both", expand=True)

        # Sidebar Buttons
        self._sidebar_button("📊 Dashboard", self.show_dashboard)
        self._sidebar_button("🧾 Pending Registrations", self.show_pending_registrations)
        self._sidebar_button("👥 Customer Management", self.show_customer_management)
        self._sidebar_button("📮 Complaints & Disputes", self.show_complaints)
        self._sidebar_button("🧑‍🍳 Employee HR", self.show_employee_hr)
        self._sidebar_button("🚗 Delivery Assignment", self.show_delivery_assignment)
        self._sidebar_button("🧠 KB Moderation", self.show_kb_moderation)
        self._sidebar_button("💬 Discussion Moderation", self.show_discussion_moderation)
        self._sidebar_button("💵 Finance Overview", self.show_finance_overview)

        # Logout button
        tk.Button(
            self.sidebar, text="Logout", font=("Arial", 12, "bold"),
            fg="#ffffff", bg="#333333", relief="flat",
            command=self._logout
        ).pack(side="bottom", pady=30, fill="x")

    def _sidebar_button(self, text, command):
        btn = tk.Button(
            self.sidebar,
            text=text,
            anchor="w",
            padx=20,
            pady=10,
            bg=SIDEBAR_BG,
            fg=SIDEBAR_FG,
            relief="flat",
            activebackground="#333333",
            activeforeground="white",
            font=("Arial", 12)
        )
        btn.pack(fill="x")
        btn.config(command=command)

    def _clear_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    # ========================================================
    # PANEL 1: DASHBOARD
    # ========================================================
    def show_dashboard(self):
        self._clear_main()
        tk.Label(
            self.main, text="Manager Dashboard", font=("Arial", 24, "bold"),
            bg=MAIN_BG
        ).pack(pady=20)

        users = load_users()
        customers = [u for u in users if u["role"] in ("CUSTOMER", "VIP")]
        employees = [u for u in users if u["role"] in ("CHEF", "DELIVERY")]

        stats = [
            ("Total Customers", len(customers)),
            ("Total Employees", len(employees)),
            ("Pending Approvals", len([u for u in users if u["status"] == "PENDING"])),
        ]

        for title, value in stats:
            frame = tk.Frame(self.main, bg=CARD_BG, bd=2, relief="groove")
            frame.pack(pady=10, padx=40, fill="x")
            tk.Label(frame, text=title, font=("Arial", 16), bg=CARD_BG).pack(side="left", padx=20)
            tk.Label(frame, text=str(value), font=("Arial", 18, "bold"), bg=CARD_BG).pack(side="right", padx=20)

    # ========================================================
    # PANEL 2: PENDING REGISTRATIONS (UC02)
    # ========================================================
    def show_pending_registrations(self):
        self._clear_main()
        tk.Label(self.main, text="Pending Customer Registrations",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=15)

        users = load_users()
        pending = [u for u in users if u["status"] == "PENDING"]

        columns = ("user_id", "username", "role")
        tree = ttk.Treeview(self.main, columns=columns, show="headings", height=12)
        tree.pack(pady=15)

        for c in columns:
            tree.heading(c, text=c)

        for u in pending:
            tree.insert("", tk.END, values=(u["user_id"], u["username"], u["role"]))

        # Buttons
        btn_frame = tk.Frame(self.main, bg=MAIN_BG)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Approve", width=15,
                  command=lambda: self._approve_user(tree)).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="Reject", width=15,
                  command=lambda: self._reject_user(tree)).grid(row=0, column=1, padx=10)

    def _approve_user(self, tree):
        sel = tree.focus()
        if not sel:
            return
        values = tree.item(sel)["values"]
        user_id = values[0]

        users = load_users()
        for u in users:
            if u["user_id"] == user_id:
                u["status"] = "ACTIVE"
        save_users(users)
        messagebox.showinfo("Approved", "User approved successfully.")
        self.show_pending_registrations()

    def _reject_user(self, tree):
        sel = tree.focus()
        if not sel:
            return
        values = tree.item(sel)["values"]
        username = values[1]

        users = load_users()
        users = [u for u in users if u["username"] != username]
        save_users(users)
        messagebox.showinfo("Removed", "User rejected and removed.")
        self.show_pending_registrations()

    # ========================================================
    # PANEL 3: CUSTOMER MANAGEMENT (UC09 / UC10)
    # ========================================================
    def show_customer_management(self):
        self._clear_main()
        tk.Label(self.main, text="Customer Management",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=20)

        columns = ("user_id", "username", "role", "warnings", "deposit", "status")
        tree = ttk.Treeview(self.main, columns=columns, show="headings", height=15)
        tree.pack(pady=10)

        for c in columns:
            tree.heading(c, text=c)

        users = load_users()
        customers = [u for u in users if u["role"] in ("CUSTOMER", "VIP")]

        for c in customers:
            tree.insert("", tk.END, values=(
                c["user_id"], c["username"], c["role"],
                c["warnings"], c["deposit"], c["status"]
            ))

        btn_frame = tk.Frame(self.main, bg=MAIN_BG)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Promote to VIP", command=lambda: self._promote(tree)).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Demote to Customer", command=lambda: self._demote(tree)).grid(row=0, column=1, padx=10)
        tk.Button(btn_frame, text="Kick Out", command=lambda: self._kick(tree)).grid(row=0, column=2, padx=10)

    def _promote(self, tree):
        sel = tree.focus()
        if not sel:
            return
        username = tree.item(sel)["values"][1]

        users = load_users()
        for u in users:
            if u["username"] == username:
                u["role"] = "VIP"
        save_users(users)
        messagebox.showinfo("Success", "User promoted to VIP.")
        self.show_customer_management()

    def _demote(self, tree):
        sel = tree.focus()
        if not sel:
            return
        username = tree.item(sel)["values"][1]

        users = load_users()
        for u in users:
            if u["username"] == username:
                u["role"] = "CUSTOMER"
        save_users(users)
        messagebox.showinfo("Success", "User demoted.")
        self.show_customer_management()

    def _kick(self, tree):
        sel = tree.focus()
        if not sel:
            return

        username = tree.item(sel)["values"][1]
        users = load_users()
        for u in users:
            if u["username"] == username:
                u["blacklisted"] = True
                u["status"] = "REMOVED"

        save_users(users)
        messagebox.showinfo("Kicked", "Customer has been kicked and blacklisted.")
        self.show_customer_management()

    # ========================================================
    # PANEL 4: COMPLAINT MANAGEMENT (UC12–UC14)
    # ========================================================
    def show_complaints(self):
        self._clear_main()
        tk.Label(self.main, text="Complaints & Disputes",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=15)

        tk.Label(self.main, text="(Coming soon — requires your complaint CSV)", 
                 font=("Arial", 14), bg=MAIN_BG).pack(pady=20)

    # ========================================================
    # PANEL 5: EMPLOYEE HR MANAGEMENT (UC11)
    # ========================================================
    def show_employee_hr(self):
        self._clear_main()
        tk.Label(self.main, text="Employee HR",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=15)

        tk.Label(self.main, text="(Coming soon — requires employee CSV structure)",
                 font=("Arial", 14), bg=MAIN_BG).pack(pady=20)

    # ========================================================
    # PANEL 6: DELIVERY ASSIGNMENT (UC17–UC18)
    # ========================================================
    def show_delivery_assignment(self):
        self._clear_main()
        tk.Label(self.main, text="Delivery Assignment",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=15)

        tk.Label(self.main, text="(Coming soon — requires bids CSV and delivery orders)",
                 font=("Arial", 14), bg=MAIN_BG).pack(pady=20)

    # ========================================================
    # PANEL 7: KNOWLEDGE BASE MODERATION (UC21)
    # ========================================================
    def show_kb_moderation(self):
        self._clear_main()
        ManagerKBReviewScreen(self.main, self.user)

    # ========================================================
    # PANEL 8: DISCUSSION MODERATION (UC16)
    # ========================================================
    def show_discussion_moderation(self):
        self._clear_main()
        tk.Label(self.main, text="Discussion Moderation",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=15)

        tk.Label(self.main, text="(Coming soon — moderation rules)",
                 font=("Arial", 14), bg=MAIN_BG).pack(pady=20)

    # ========================================================
    # PANEL 9: FINANCE OVERVIEW
    # ========================================================
    def show_finance_overview(self):
        self._clear_main()
        tk.Label(self.main, text="Finance Overview",
                 font=("Arial", 20, "bold"), bg=MAIN_BG).pack(pady=15)

        users = load_users()
        total_deposit = sum([u["deposit"] for u in users])
        total_spent = sum([u["total_spent"] for u in users])

        frame = tk.Frame(self.main, bg=CARD_BG, bd=2, relief="groove")
        frame.pack(pady=10, padx=40, fill="x")
        tk.Label(frame, text=f"Total Customer Deposits: ${total_deposit:.2f}",
                 font=("Arial", 16), bg=CARD_BG).pack(side="left", padx=20)
        tk.Label(frame, text=f"Total Customer Spending: ${total_spent:.2f}",
                 font=("Arial", 16), bg=CARD_BG).pack(side="right", padx=20)

    # ========================================================
    # LOGOUT
    # ========================================================
    def _logout(self):
        from login_screen import LoginScreen
        self.destroy()
        LoginScreen(self.master)
