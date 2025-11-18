import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import csv
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_CSV = DATA_DIR / "knowledge_base.csv"
KB_FLAGS_CSV = DATA_DIR / "kb_flags.csv"
USERS_CSV = DATA_DIR / "users.csv"


# -------------------------------------------------------------
# LOW-LEVEL CSV HANDLING
# -------------------------------------------------------------

def _read_csv(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


# -------------------------------------------------------------
# KB FUNCTIONS
# -------------------------------------------------------------

def load_kb():
    return _read_csv(KB_CSV)


def save_kb(rows):
    fieldnames = ["kb_id", "question", "answer", "author_username"]
    _write_csv(KB_CSV, rows, fieldnames)


# -------------------------------------------------------------
# FLAG FUNCTIONS
# -------------------------------------------------------------

def load_flags():
    return _read_csv(KB_FLAGS_CSV)


def save_flags(rows):
    fieldnames = ["kb_id", "flagged_by", "rating", "comment", "created_at"]
    _write_csv(KB_FLAGS_CSV, rows, fieldnames)


# -------------------------------------------------------------
# USER BAN SYSTEM
# -------------------------------------------------------------

def ban_user_from_kb(username):
    """
    Adds a field 'kb_banned' to users.csv (if missing).
    """
    rows = _read_csv(USERS_CSV)

    fieldnames = list(rows[0].keys()) if rows else [
        "user_id", "username", "password", "role", "status",
        "warnings", "deposit", "total_spent", "num_orders", "blacklisted"
    ]

    if "kb_banned" not in fieldnames:
        fieldnames.append("kb_banned")

    for r in rows:
        if r.get("username") == username:
            r["kb_banned"] = "True"
        elif "kb_banned" not in r:
            r["kb_banned"] = "False"

    _write_csv(USERS_CSV, rows, fieldnames)


def is_user_banned_from_kb(username):
    rows = _read_csv(USERS_CSV)
    for r in rows:
        if r.get("username") == username:
            return r.get("kb_banned", "False") == "True"
    return False


# -------------------------------------------------------------
# GUI FOR MANAGER FLAG REVIEW (UC21)
# -------------------------------------------------------------

class ManagerKBReviewScreen(tk.Frame):
    """
    UC21 — Manager reviews flagged knowledge base entries.
    Supports:
    - viewing flags
    - deleting KB entry
    - banning author
    - clearing flags
    """

    def __init__(self, master, user):
        super().__init__(master, bg="#f5f5f5")
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self.kb_rows = load_kb()
        self.flags = load_flags()

        self._build_ui()

    # ---------------- UI Layout -------------------

    def _build_ui(self):
        header = tk.Frame(self, bg="#f5f5f5")
        header.pack(fill="x", pady=10)

        tk.Label(
            header, text="Flagged Knowledge Base Review",
            font=("Arial", 22, "bold"), bg="#f5f5f5"
        ).pack()

        main = tk.Frame(self, bg="#f5f5f5")
        main.pack(fill="both", expand=True, padx=15, pady=10)

        # LEFT: List of flags
        left = tk.Frame(main, bg="#ffffff", bd=2, relief="groove")
        left.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(
            left, text="Flagged Answers",
            font=("Arial", 16, "bold"), bg="#ffffff"
        ).pack(pady=10)

        columns = ("kb_id", "flagged_by", "rating", "comment", "created")
        self.flag_tree = ttk.Treeview(left, columns=columns, show="headings", height=20)
        for col in columns:
            self.flag_tree.heading(col, text=col.replace("_", " ").title())

        for f in self.flags:
            self.flag_tree.insert(
                "", tk.END,
                iid=f["kb_id"],
                values=(
                    f["kb_id"], f["flagged_by"], f["rating"],
                    f["comment"], f["created_at"]
                )
            )

        self.flag_tree.pack(fill="y", expand=True)
        self.flag_tree.bind("<<TreeviewSelect>>", self._on_select_flag)

        # RIGHT: Detail panel
        right = tk.Frame(main, bg="#ffffff", bd=2, relief="groove")
        right.pack(side="left", fill="both", expand=True)

        tk.Label(
            right, text="Flag Details",
            font=("Arial", 16, "bold"), bg="#ffffff"
        ).pack(pady=10)

        self.detail_text = tk.Text(
            right, wrap="word", font=("Arial", 11),
            bg="#fafafa", state="disabled", height=25
        )
        self.detail_text.pack(fill="both", expand=True, padx=10)

        # Buttons
        btn_frame = tk.Frame(right, bg="#ffffff")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Delete KB Entry",
            command=self._delete_kb, width=18
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame, text="Ban Author",
            command=self._ban_author, width=18
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            btn_frame, text="Clear Flag",
            command=self._clear_flag, width=18
        ).grid(row=0, column=2, padx=10)

        tk.Button(
            self, text="Back",
            command=self._back
        ).pack(pady=10)

    # ---------------- Logic -------------------

    def _on_select_flag(self, event=None):
        sel = self.flag_tree.focus()
        if not sel:
            return

        flag = next((f for f in self.flags if f["kb_id"] == sel), None)
        kb = next((k for k in self.kb_rows if k["kb_id"] == sel), None)

        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", tk.END)

        if flag:
            self.detail_text.insert(tk.END, f"Flag ID: {flag['kb_id']}\n")
            self.detail_text.insert(tk.END, f"Flagged By: {flag['flagged_by']}\n")
            self.detail_text.insert(tk.END, f"Rating: {flag['rating']}\n")
            self.detail_text.insert(tk.END, f"Comment: {flag['comment']}\n")
            self.detail_text.insert(tk.END, f"Flag Time: {flag['created_at']}\n")
            self.detail_text.insert(tk.END, "\n")

        if kb:
            self.detail_text.insert(tk.END, f"QUESTION:\n{kb['question']}\n\n")
            self.detail_text.insert(tk.END, f"ANSWER:\n{kb['answer']}\n\n")
            self.detail_text.insert(tk.END, f"AUTHOR: {kb['author_username']}\n")

        self.detail_text.config(state="disabled")

    def _delete_kb(self):
        sel = self.flag_tree.focus()
        if not sel:
            return

        self.kb_rows = [k for k in self.kb_rows if k["kb_id"] != sel]
        save_kb(self.kb_rows)

        messagebox.showinfo("Removed", "KB entry has been deleted.")

        self._clear_flag()

    def _ban_author(self):
        sel = self.flag_tree.focus()
        if not sel:
            return

        kb = next((k for k in self.kb_rows if k["kb_id"] == sel), None)
        if not kb:
            return

        ban_user_from_kb(kb["author_username"])

        messagebox.showinfo(
            "Author Banned",
            f"User '{kb['author_username']}' is now banned from writing KB answers."
        )

    def _clear_flag(self):
        sel = self.flag_tree.focus()
        if not sel:
            return

        self.flags = [f for f in self.flags if f["kb_id"] != sel]
        save_flags(self.flags)

        self.flag_tree.delete(sel)

        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.config(state="disabled")

        messagebox.showinfo("Flag Cleared", "Flag has been removed from the system.")

    def _back(self):
        from manager_gui import ManagerScreen
        self.destroy()
        ManagerScreen(self.master, self.user)
