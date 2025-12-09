import os
from pathlib import Path
from typing import Optional

import streamlit as st

# Optional dotenv
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return

# ---------------- Django setup ----------------

import django

BASE_DIR = Path(__file__).resolve().parent.parent  # project root

# TODO: CHANGE THIS to your actual project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant_project.settings")

try:
    django.setup()
except Exception as e:
    st.error(f"Django setup failed: {e}")

from ai_assist.models import AllergyPreference
from accounts.models import Customer

load_dotenv(BASE_DIR / ".env")

# UC22 – common allergen list
ALLERGENS = [
    "milk", "egg", "peanut", "tree_nut",
    "fish", "shellfish", "wheat", "soy",
    "sesame", "gluten", "corn", "chili",
]

ROLE_VISITOR = "VISITOR"
ROLE_CUSTOMER = "CUSTOMER"
ROLE_VIP = "VIP"
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


def get_customer_for_username(username: str) -> Optional[Customer]:
    try:
        cust = Customer.objects.filter(user__username=username).first()
        if not cust:
            cust = Customer.objects.filter(username=username).first()
        return cust
    except Exception:
        return None


# ---------------- Data helpers (Django model) ----------------

def load_allergy_prefs(username: str):
    """
    Return list of allergens for this username, using AllergyPreference model.
    """
    customer = get_customer_for_username(username)
    if not customer:
        return []

    try:
        pref = AllergyPreference.objects.filter(customer=customer).first()
    except Exception:
        return []

    if not pref:
        return []
    return pref.get_allergen_list()


def save_allergy_prefs(username: str, allergens):
    """
    Save/update allergy preferences for one user via AllergyPreference model.
    allergens is a list like ["milk", "peanut"].
    """
    customer = get_customer_for_username(username)
    if not customer:
        st.error(
            "No Customer record found for this username. "
            "Make sure the Django Customer model is set up correctly."
        )
        return

    try:
        pref, _ = AllergyPreference.objects.get_or_create(customer=customer)
        pref.set_allergen_list(allergens)
        pref.save()
    except Exception as e:
        st.error(f"Could not save allergy preferences: {e}")


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
        if get_customer_for_username(st.session_state.username):
            st.success("Your allergy preferences were saved successfully.")

    if selected:
        st.markdown("#### Currently blocked allergens")
        st.write(", ".join(selected))
    else:
        st.info("You have not selected any allergens. No filtering will be applied.")

    st.markdown("---")
    st.caption(
        "Implements UC22: Registered/VIP customers can save allergy preferences, "
        "which are stored in the Django model AllergyPreference and consumed by Menu (UC06/UC07) "
        "for filtering unsafe dishes."
    )


if __name__ == "__main__":
    main()
