import csv
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ALLERGY_CSV = DATA_DIR / "allergy_prefs.csv"

ALLERGENS = [
    "milk", "egg", "peanut", "tree_nut",
    "fish", "shellfish", "wheat", "soy",
    "sesame", "gluten", "corn", "chili",
]


def init_user():
    if "username" not in st.session_state:
        st.session_state.username = "demo_customer"
    if "role" not in st.session_state:
        st.session_state.role = "CUSTOMER"


def load_allergy_prefs(username: str):
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


def render_header():
    st.markdown(
        """
        <div style="background-color:#111827;padding:10px 16px;border-radius:0 0 8px 8px;">
            <h2 style="color:white;margin:0;">Allergy Preferences</h2>
            <p style="color:#9ca3af;margin:2px 0 0 0;font-size:13px;">
                UC22 – Save allergies so the menu can be filtered later
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        "Implements UC22: saving allergy preferences to a profile, ready for menu filtering (UC06/UC07)."
    )


if __name__ == "__main__":
    main()
