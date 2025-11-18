import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import csv
from allergy_gui import load_allergy_prefs

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MENU_CSV = DATA_DIR / "menu.csv"


def load_menu_items():
    items = []
    with open(MENU_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ingredients = [
                i.strip().lower()
                for i in row.get("ingredients", "").split(",")
                if i.strip()
            ]
            items.append({
                "item_id": row["item_id"],
                "name": row["name"],
                "description": row["description"],
                "price": float(row["price"]),
                "category": row["category"],
                "ingredients": ingredients,
                "is_special": row["is_special"] == "True",
                "is_available": row["is_available"] == "True",
            })
    return items


class MenuScreen(tk.Frame):
    """UC22 – Menu browsing with allergy filtering."""

    def __init__(self, master, user):
        super().__init__(master, bg="#f5f5f5")
        self.master = master
        self.user = user
        self.allergens = [a.lower() for a in load_allergy_prefs(user["username"])]
        self.menu_items = load_menu_items()
        self.hidden_items = []

        self.pack(fill="both", expand=True)
        self._build_ui()
        self._populate()

    # ---------------------------------------------------------
    # UI BUILD
    # ---------------------------------------------------------

    def _build_ui(self):
        tk.Label(
            self,
            text="Menu (Allergy-Filtered)",
            font=("Arial", 22, "bold"),
            bg="#f5f5f5"
        ).pack(pady=15)

        if self.allergens:
            txt = "Hiding dishes containing: " + ", ".join(self.allergens)
        else:
            txt = "No allergens selected — showing full menu."

        tk.Label(self, text=txt, bg="#f5f5f5", fg="#444", font=("Arial", 11)).pack()

        # TABLE
        cols = ("Name", "Price", "Category", "Ingredients", "VIP")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=17)

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # BUTTONS
        bf = tk.Frame(self, bg="#f5f5f5")
        bf.pack(pady=10)

        tk.Button(bf, text="Refresh Filter", width=18, command=self._refresh).grid(row=0, column=0, padx=10)
        tk.Button(bf, text="View Hidden Dishes", width=18, command=self._show_hidden).grid(row=0, column=1, padx=10)
        tk.Button(bf, text="Back", width=18, command=self._back).grid(row=0, column=2, padx=10)

    # ---------------------------------------------------------
    # POPULATE TABLE (APPLY FILTER)
    # ---------------------------------------------------------

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        self.hidden_items = []

        for item in self.menu_items:
            if not item["is_available"]:
                continue

            # VIP ACCESS FILTER
            if item["is_special"] and self.user["role"] != "VIP":
                continue

            # ALLERGY FILTER
            contains_allergy = any(a in item["ingredients"] for a in self.allergens)

            if contains_allergy:
                self.hidden_items.append(item)
                continue

            ingredients_str = ", ".join(item["ingredients"])
            vip_label = "VIP" if item["is_special"] else ""

            self.tree.insert(
                "", "end",
                values=(item["name"], f"${item['price']:.2f}", item["category"], ingredients_str, vip_label)
            )

    # ---------------------------------------------------------
    # SHOW HIDDEN DISHES
    # ---------------------------------------------------------

    def _show_hidden(self):
        if not self.hidden_items:
            messagebox.showinfo("Hidden Dishes", "No dishes were hidden.")
            return

        win = tk.Toplevel(self)
        win.title("Hidden Dishes (Contains Allergens)")
        win.geometry("600x400")

        tk.Label(win, text="Hidden Dishes", font=("Arial", 16, "bold")).pack(pady=10)

        tb = tk.Text(win, wrap="word", bg="#fff", font=("Arial", 11))
        tb.pack(fill="both", expand=True, padx=10, pady=10)

        for item in self.hidden_items:
            tb.insert("end", f"{item['name']} (${item['price']}) — {item['category']}\n")
            tb.insert("end", "Ingredients: ")
            for ing in item["ingredients"]:
                if ing in self.allergens:
                    tb.insert("end", f"{ing} ", "alert")
                else:
                    tb.insert("end", f"{ing} ")
            tb.insert("end", "\n\n")

        tb.tag_config("alert", foreground="red", font=("Arial", 11, "bold"))

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------

    def _refresh(self):
        self.allergens = load_allergy_prefs(self.user["username"])
        self._populate()
        messagebox.showinfo("Filter Applied", "Allergy filter refreshed.")

    # ---------------------------------------------------------
    # BACK
    # ---------------------------------------------------------

    def _back(self):
        from customer_gui import CustomerScreen
        self.destroy()
        CustomerScreen(self.master, self.user)
