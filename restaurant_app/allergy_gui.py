import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ALLERGY_CSV = DATA_DIR / "allergy_prefs.csv"

# FULL ALLERGEN LIST (expandable)
ALLERGENS = [
    "milk", "egg", "peanut", "tree_nut",
    "fish", "shellfish", "wheat", "soy",
    "sesame", "gluten", "corn", "chili",
]


def load_allergy_prefs(username: str):
    """Load a user's allergens from CSV."""
    if not ALLERGY_CSV.exists():
        return []

    with open(ALLERGY_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username:
                allergens = row.get("allergens", "").strip()
                if not allergens:
                    return []
                return [a.strip() for a in allergens.split(",") if a.strip()]
    return []


def save_allergy_prefs(username: str, allergens):
    """Save updated allergy list."""
    rows = []
    found = False

    if ALLERGY_CSV.exists():
        with open(ALLERGY_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["username"] == username:
                    row["allergens"] = ",".join(allergens)
                    found = True
                rows.append(row)

    if not found:
        rows.append({"username": username, "allergens": ",".join(allergens)})

    with open(ALLERGY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "allergens"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


class AllergySettingsScreen(tk.Frame):
    """UC22 – Manage user allergy preferences."""

    def __init__(self, master, user):
        super().__init__(master, bg="#fafafa")
        self.master = master
        self.user = user
        self.pack(fill="both", expand=True)

        self.vars = {}
        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self,
            text="Allergy Settings",
            font=("Arial", 22, "bold"),
            bg="#fafafa"
        ).pack(pady=20)

        tk.Label(
            self, text=f"User: {self.user['username']}",
            font=("Arial", 12),
            bg="#fafafa"
        ).pack(pady=5)

        frame = tk.Frame(self, bg="#fafafa")
        frame.pack(pady=20)

        current = set(load_allergy_prefs(self.user["username"]))

        for i, allergen in enumerate(ALLERGENS):
            var = tk.BooleanVar(value=(allergen in current))
            cb = tk.Checkbutton(
                frame, text=allergen.capitalize(), variable=var,
                bg="#fafafa", font=("Arial", 11)
            )
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=15, pady=5)
            self.vars[allergen] = var

        btn_frame = tk.Frame(self, bg="#fafafa")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame, text="Save", width=15,
            command=self._save, font=("Arial", 12)
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame, text="Back", width=15,
            command=self._back, font=("Arial", 12)
        ).grid(row=0, column=1, padx=10)

    def _save(self):
        selected = [a for a, v in self.vars.items() if v.get()]
        save_allergy_prefs(self.user["username"], selected)
        messagebox.showinfo("Saved", "Your allergy preferences were updated.")

    def _back(self):
        from customer_gui import CustomerScreen
        self.destroy()
        CustomerScreen(self.master, self.user)
