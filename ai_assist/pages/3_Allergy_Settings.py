import csv
from pathlib import Path

import streamlit as st

# ---------------- Paths & constants ----------------

# This file is in: ai_assist/pages/3_Allergy_Settings.py
# → BASE_DIR = ai_assist
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ALLERGY_CSV = DATA_DIR / "allergy_prefs.csv"

# UC22 – common allergen list
ALLERGENS = [
    "milk", "egg", "peanut", "tree_nut",
    "fish", "shellfish", "wheat", "soy",
    "sesame", "gluten", "corn", "chili",
]

# Role constants (same style as other pages)
ROLE_VISITOR = "VISITOR"
ROLE_CUSTOMER = "CUSTOMER"   # Registered customer
ROLE_VIP = "VIP"             # VIP customer
ROLE_MANAGER = "MANAGER"


# ---------------- User / role helpers ----------------

def init_user():
    """
    For the prototype, we simulate a logged-in user.
    In the real system, UC03 would set username + role.
    """
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        st.session_state.role = ROLE_CUSTOMER


def user_can_edit_allergies() -> bool:
    """
    UC22 actors: Registered and VIP customers.
    Only these can configure allergy preferences.
    """
    return st.session_state.role in (ROLE_CUSTOMER, ROLE_VIP)


# ---------------- Data helpers ----------------

def load_allergy_prefs(username: str):
    """
    Return list of allergens for this username.
    CSV format: username, allergens (comma-separated)
    """
    if not ALLERGY_CSV.exists():
        return []

    with open(ALLERGY_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["username"] == username:
                allergens = row.get("allergens", "").strip()
                if not allergens:
                    return []
                # Normalize to lower-case for consistent matching in UC06
                return [a.strip().lower() for a in allergens.split(",") if a.strip()]
    return []


def save_allergy_prefs(username: str, allergens):
    """
    Save/update allergy preferences for one user.
    allergens is a list like ["milk", "peanut"].
    """
    # Normalize to lower-case before saving
    allergens = [a.strip().lower() for a in allergens if a.strip()]

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


# ---------------- UI helpers ----------------

def render_header():
    st.markdown(
        """
        <div style="background-color:#111827;padding:10px 16px;border-radius:0 0 8px 8px;">
            <h2 style="color:white;margin:0;">Allergy Preferences</h2>
            <p style="color:#9ca3af;margin:2px 0 0 0;font-size:13px;">
                UC22 – Save allergies so the menu can be filtered later (UC06 / UC07)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------- Main UC22 Screen ----------------

def main():
    st.set_page_config(
        page_title="AI Restaurant – Allergy Settings",
        page_icon="⚕️",
        layout="centered",
    )
    init_user()
    render_header()

    st.write("")
    st.markdown(
        f"### Manage allergies for **{st.session_state.username}** "
        f"(_role: {st.session_state.role}_)"
    )

    # Role-based access (UC22 actors = Registered & VIP)
    if not user_can_edit_allergies():
        st.info(
            "Only **Registered** and **VIP** customers can configure allergy preferences.\n\n"
            "- Visitors should register and log in first (UC01 / UC03).\n"
            "- Managers, chefs, and drivers do not use this screen."
        )
        st.markdown("---")
        st.caption(
            "UC22 enforced: allergy preferences are customer-facing only, "
            "used later for menu filtering in UC06/UC07."
        )
        return

    current_allergies = load_allergy_prefs(st.session_state.username)

    selected = st.multiselect(
        "Select all allergens that apply to you:",
        options=ALLERGENS,
        default=current_allergies,
        help="These will be used later to hide unsafe dishes in the Menu screen.",
    )

    if st.button("Save Preferences"):
        save_allergy_prefs(st.session_state.username, selected)
        st.success("Your allergy preferences were saved successfully.")

    if selected:
        st.markdown("#### Currently blocked allergens")
        st.write(", ".join(selected))
    else:
        st.info("You have not selected any allergens. No filtering will be applied.")

    st.markdown("---")
    st.caption(
        "Implements UC22: Registered/VIP customers can save allergy preferences, "
        "which are stored in allergy_prefs.csv and consumed by Menu (UC06) "
        "for filtering unsafe dishes."
    )


if __name__ == "__main__":
    main()
