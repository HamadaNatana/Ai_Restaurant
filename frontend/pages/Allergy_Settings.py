
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

BASE_DIR = Path(__file__).resolve().parent.parent

# Correct Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant.settings")

try:
    django.setup()
except Exception as e:
    st.error(f"Django setup failed: {e}")

from menu.models import AllergyPreference
from accounts.models import Customer, Manager

load_dotenv(BASE_DIR / ".env")

# UC22 – allergen list
ALLERGENS = [
    "milk", "egg", "peanut", "tree_nut",
    "fish", "shellfish", "wheat", "soy",
    "sesame", "gluten", "corn", "chili",
]

ROLE_VISITOR = "VISITOR"
ROLE_CUSTOMER = "CUSTOMER"
ROLE_VIP = "VIP"
ROLE_MANAGER = "MANAGER"


# ---------------------------------------------------------
# REAL LOGIN DETECTION (UC03)
# ---------------------------------------------------------

def resolve_logged_in_user():
    """
    Receives user info from Django redirect, e.g.:
      http://localhost:8506/allergy?username=john&role=CUSTOMER

    st.query_params returns lists: {"username": ["john"], "role": ["CUSTOMER"]}
    so we must use [0].
    """
    qp = st.query_params

    username = qp.get("username", [""])[0]
    role_qp = qp.get("role", ["VISITOR"])[0] or ROLE_VISITOR

    # If user opens directly (no query params), use demo customer for testing
    if not username:
        return "demo_customer", ROLE_CUSTOMER

    # Manager?
    if Manager.objects.filter(user__username=username).exists():
        return username, ROLE_MANAGER

    # Customer?
    cust = Customer.objects.filter(username=username).first()
    if cust:
        if cust.status == Customer.STATUS_VIP:
            return username, ROLE_VIP
        return username, ROLE_CUSTOMER

    # Default – visitor (username string but no matching record)
    return username, ROLE_VISITOR


# ---------------------------------------------------------
# Permissions
# ---------------------------------------------------------

def user_can_edit_allergies(role: str) -> bool:
    """Only Registered & VIP customers may edit UC22 preferences."""
    return role in (ROLE_CUSTOMER, ROLE_VIP)


def get_customer_for_username(username: str) -> Optional[Customer]:
    """
    Map username -> Customer.
    Your Customer extends AbstractUser, so username is on Customer,
    but we also check user__username just in case.
    """
    try:
        cust = Customer.objects.filter(username=username).first()
        if not cust:
            cust = Customer.objects.filter(user__username=username).first()
        return cust
    except Exception:
        return None


# ---------------------------------------------------------
# Allergy Preference Helpers (Django model)
# ---------------------------------------------------------

def load_allergy_prefs(username: str):
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
    customer = get_customer_for_username(username)
    if not customer:
        st.error("Customer record not found.")
        return

    try:
        pref, _ = AllergyPreference.objects.get_or_create(customer=customer)
        pref.set_allergen_list(allergens)
        pref.save()
    except Exception as e:
        st.error(f"Could not save allergy preferences: {e}")


# ---------------------------------------------------------
# UI Header
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# MAIN UC22 Screen
# ---------------------------------------------------------

def main():
    st.set_page_config(
        page_title="AI Restaurant – Allergy Settings",
        page_icon="⚕️",
        layout="centered",
    )

    # REAL login from Django
    username, role = resolve_logged_in_user()

    render_header()

    st.write("")
    st.markdown(
        f"### Manage allergies for **{username or 'Unknown'}** "
        f"(_role: {role}_)"
    )

    # Role-based access (UC22)
    if not user_can_edit_allergies(role):
        st.info(
            "Only **Registered** and **VIP** customers can configure allergy preferences.\n\n"
            "- Visitors must register and log in first (UC01 / UC03).\n"
            "- Managers and staff do not use this screen."
        )
        st.markdown("---")
        st.caption(
            "UC22 enforced: allergy preferences are customer-facing only."
        )
        return

    # Load existing allergies
    current_allergies = load_allergy_prefs(username)

    selected = st.multiselect(
        "Select all allergens that apply to you:",
        options=ALLERGENS,
        default=current_allergies,
        help="These allergens will be used to filter menu items (UC06 / UC07).",
    )

    if st.button("Save Preferences"):
        save_allergy_prefs(username, selected)

        if get_customer_for_username(username):
            st.success("Your allergy preferences were saved successfully.")

    if selected:
        st.markdown("#### Currently blocked allergens")
        st.write(", ".join(selected))
    else:
        st.info("You have not selected any allergens.")

    st.markdown("---")
    st.caption(
        "Implements UC22: Registered/VIP customers store allergy preferences in the Django model."
    )


if __name__ == "__main__":
    main()
