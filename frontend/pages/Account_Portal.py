import streamlit as st
import os
import django
import sys
from pathlib import Path

# ---------------- Django Setup ----------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant.settings")

try:
    django.setup()
except Exception:
    pass

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from accounts.models import Customer, Manager

# Get the actual User model (common.User)
User = get_user_model()

# ---------------- Session State Helpers ----------------
def login_user(username, role):
    st.session_state["username"] = username
    st.session_state["role"] = role
    st.session_state["logged_in"] = True

def logout_user():
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["logged_in"] = False
    st.session_state["cart_items"] = []

# ---------------- UI Layout ----------------
st.set_page_config(page_title="Account Portal", page_icon="👤")
st.title("👤 Account Portal")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ==========================================
# VIEW 1: LOGGED IN PROFILE
# ==========================================
if st.session_state["logged_in"]:
    username = st.session_state["username"]
    role = st.session_state["role"]
    
    st.success(f"Welcome back, **{username}**!")
    st.info(f"Current Role: **{role}**")
    
    if role in ["CUSTOMER", "VIP"]:
        try:
            # FIX: Filter by the RELATED user's username
            cust = Customer.objects.get(user__username=username)
            col1, col2 = st.columns(2)
            col1.metric("Wallet Balance", f"${cust.balance}")
            col2.metric("Warnings", f"{cust.warnings}/3")
            
            if cust.status == 'vip':
                st.balloons()
                st.write("🌟 **You are a VIP Member!** Enjoy 5% off and free delivery.")
        except Customer.DoesNotExist:
            st.warning("Customer profile not found.")

    if st.button("Log Out"):
        logout_user()
        st.rerun()

# ==========================================
# VIEW 2: LOGIN / REGISTER TABS
# ==========================================
else:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    # --- TAB 1: LOGIN (UC 03) ---
    with tab1:
        st.subheader("Sign In")
        with st.form("login_form"):
            login_user_input = st.text_input("Username")
            login_pass_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
        
        if submit_login:
            user = authenticate(username=login_user_input, password=login_pass_input)
            
            if user is not None:
                role = "VISITOR"
                if hasattr(user, 'manager'):
                    role = "MANAGER"
                elif hasattr(user, 'driver'):
                    role = "DRIVER"
                else:
                    try:
                        # FIX: Check user.customer instead of querying by username directly
                        cust = Customer.objects.get(user=user)
                        role = "VIP" if cust.status == 'vip' else "CUSTOMER"
                    except Customer.DoesNotExist:
                        role = "VISITOR"

                login_user(user.username, role)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    # --- TAB 2: REGISTER (UC 01) ---
    with tab2:
        st.subheader("Create New Customer Account")
        with st.form("register_form"):
            new_user = st.text_input("Choose Username")
            new_email = st.text_input("Email Address")
            new_pass = st.text_input("Choose Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            deposit = st.number_input("Initial Deposit ($)", min_value=0.0, value=100.0)
            submit_reg = st.form_submit_button("Register")
        
        if submit_reg:
            if new_pass != confirm_pass:
                st.error("Passwords do not match.")
            elif not new_user:
                st.error("Username is required.")
            else:
                try:
                    # 1. Create Django User
                    user = User.objects.create_user(username=new_user, email=new_email, password=new_pass)
                    
                    # 2. Create Customer Profile
                    # FIX: Removed 'username=new_user' because the Model doesn't have it.
                    Customer.objects.create(
                        user=user,
                        balance=deposit,
                        status='regular'
                    )
                    
                    st.success("Account created! You can now log in.")
                except IntegrityError:
                    st.error("Username already taken.")
                except Exception as e:
                    st.error(f"Error creating account: {e}")