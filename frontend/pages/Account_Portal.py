import requests
import streamlit as st
import os
import django
import sys
from pathlib import Path
from utils.sidebar import generate_sidebar

# ---------------- Django Setup ----------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant.settings")

try:
    django.setup()
except Exception:
    pass

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from accounts.models import Customer
from common.models import User
from hr.models import RegistrationApproval
from accounts.views import build_warning_message

User = get_user_model()
BASE_URL = "http://127.0.0.1:8000"

# ---------------- Session State Helpers ----------------
def login_user(username, role):
    st.session_state["username"] = username
    st.session_state["role"] = role
    st.session_state["logged_in"] = True

def logout_user():
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["logged_in"] = False

# ---------------- Page Views ----------------

def show_feedback_form(customer_id):
    """UC12: Submit Compliment/Complaint"""
    st.markdown("---")
    st.subheader("📢 File Feedback (UC12)")
    st.caption("Submit a compliment or complaint regarding a dish, chef, or driver.")

    with st.form("feedback_form"):
        col1, col2 = st.columns(2)
        category = col1.selectbox("Category", ["Complaint", "Compliment"])
        target_type = col2.selectbox("Target Type", ["chef", "driver", "dish", "customer"])
        target_id = st.text_input(f"Enter {target_type.title()} ID or Name")
        message = st.text_area("Details", max_chars=500)
        
        if st.form_submit_button("Submit Feedback"):
            if not target_id or not message:
                st.error("Target ID and message are required.")
            else:
                try:
                    payload = {
                        "customer_id": str(customer_id),
                        "target_type": target_type,
                        "target_id": target_id,
                        "message": message,
                        "category": category
                    }
                    # Ensure this URL matches your Reputation App URL
                    res = requests.post(f"{BASE_URL}/reputation/file_feedback/", json=payload)
                    if res.status_code == 200:
                        st.success(res.json().get('message', 'Feedback submitted!'))
                    else:
                        st.error(f"Failed: {res.json().get('error', res.text)}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

def show_customer_profile(username):
    try:
        cust = Customer.objects.get(user__username=username)
        st.subheader(f"Welcome, {cust.user.first_name or username}")
        
        # 1. Dashboard Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Wallet Balance", f"${cust.balance}")
        
        if cust.status == 'vip':
            col2.metric("Warnings", f"{cust.warnings}/2")
            col3.success("🌟 **VIP Member**")
        else:
            col2.metric("Warnings", f"{cust.warnings}/3")
            col3.info("Regular Membership")
            
        # 2. UC15: Warning Messages
        warning_msg = build_warning_message(cust)
        if warning_msg:
            st.warning(f"⚠️ {warning_msg}")
            
        # 3. UC12: Feedback Form
        show_feedback_form(cust.pk)

    except Customer.DoesNotExist:
        st.error("Customer profile data is missing. Please contact support.")

def show_manager_dashboard(user):
    st.header("📈 Manager Dashboard")
    st.info("System Status: Online")

def show_chef_interface(user):
    st.header("👨‍🍳 Kitchen View")
    st.warning("Orders Pending")

def show_driver_interface(user):
    st.header("🛵 Driver Portal")
    st.success("Active for Deliveries")

# ---------------- UI Layout ----------------
st.set_page_config(page_title="Restaurant Portal", page_icon="🍽️", layout="wide")
generate_sidebar()
st.title("🍽️ Restaurant Portal")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ==========================================
# GLOBAL TABS (Fixes disappearing tabs)
# ==========================================
# Tab 1 name changes dynamically
tab1_label = "👤 Dashboard" if st.session_state["logged_in"] else "🔑 Login"
tab1, tab2, tab3 = st.tabs([tab1_label, "📝 New Customer Register", "💰 Wallet"])

# ==========================================
# TAB 1: LOGIN / DASHBOARD ROUTER
# ==========================================
with tab1:
    if st.session_state["logged_in"]:
        # --- LOGGED IN VIEW ---
        current_username = st.session_state["username"]
        current_role = st.session_state["role"]
        
        # Logout in Sidebar
        with st.sidebar:
            if st.button("Log Out"):
                logout_user()
                st.rerun()

        # Role Routing
        try:
            active_user = User.objects.get(username=current_username)
            
            if current_role == "MANAGER":
                show_manager_dashboard(active_user)
            elif current_role == "CHEF":
                show_chef_interface(active_user)
            elif current_role == "DRIVER":
                show_driver_interface(active_user)
            elif current_role in ["CUSTOMER", "VIP"]:
                show_customer_profile(current_username)
            else:
                st.error("Role not recognized.")
        except User.DoesNotExist:
            st.error("Session invalid. Please log in again.")

    else:
        # --- GUEST LOGIN VIEW ---
        st.subheader("Sign In")
        with st.form("login_form"):
            login_user_input = st.text_input("Username").strip() 
            login_pass_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
        
        if submit_login:
            user = authenticate(username=login_user_input, password=login_pass_input)
            
            if user is not None:
                if not user.is_active:
                    st.error("This account is inactive.")
                else:
                    role = "VISITOR"
                    if hasattr(user, 'manager'): role = "MANAGER"
                    elif hasattr(user, 'chef'): role = "CHEF"
                    elif hasattr(user, 'driver'): role = "DRIVER"
                    else:
                        try:
                            cust = Customer.objects.get(user=user)
                            if cust.is_blacklisted:
                                st.error("🚫 Access Denied: Account Blacklisted.")
                                st.stop()
                            role = "VIP" if cust.status == 'vip' else "CUSTOMER"
                        except Customer.DoesNotExist:
                            role = "VISITOR"

                    login_user(user.username, role)
                    st.success(f"Login successful! Loading {role} dashboard...")
                    st.rerun()
            else:
                st.error("Invalid username or password.")

# ==========================================
# TAB 2: REGISTER (LOGIC PRESERVED)
# ==========================================
with tab2:
    if st.session_state.get("logged_in"):
        st.info("You are already registered.")
    else:
        st.info("Only Visitors can register here. Staff must be added by a Manager.")
        with st.form("register_form"):
            first_name = st.text_input("Enter First Name").strip()
            last_name = st.text_input("Enter Last Name").strip()
            new_user = st.text_input("Choose Username").strip()
            new_email = st.text_input("Email Address").strip()
            new_pass = st.text_input("Choose Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            address = st.text_area("Delivery Address (Optional)").strip()
            submit_reg = st.form_submit_button("Register")
        
        if submit_reg:
            if new_pass != confirm_pass:
                st.error("Passwords do not match.")
            elif not new_user:
                st.error("Username is required.")
            else:
                try:
                    # 1. Check if they already exist in the REAL system
                    if User.objects.filter(username=new_user).exists():
                        st.error("Username already taken.")
                        
                    # 2. Check if they are already waiting in the PENDING list
                    elif RegistrationApproval.objects.filter(username=new_user, status='pending').exists():
                        st.error("An application for this username is already pending.")
                        
                    # 3. Create the "Waiting Room" Entry ONLY
                    else:
                        # We hash the password now so we can save it safely in the temporary table
                        hashed_pw = make_password(new_pass)
                        
                        RegistrationApproval.objects.create(
                            username=new_user,
                            email=new_email,
                            first_name=first_name,
                            last_name=last_name,
                            password_hash=hashed_pw,
                            address=address,
                            status='pending'
                        )
                        st.success("✅ Application submitted! Please wait for a Manager to approve your account.")
                        
                except Exception as e:
                    st.error(f"Error submitting application: {e}")

# ==========================================
# TAB 3: WALLET & DEPOSIT
# ==========================================
with tab3:
    st.header("My Wallet")
    
    # Wallet requires login
    if not st.session_state.get("logged_in"):
        st.warning("Please Log In (Tab 1) to manage your funds.")
    else:
        current_user = st.session_state["username"]
        
        # --- SECTION A: DEPOSIT FUNDS ---
        with st.container(border=True):
            st.subheader("➕ Add Funds")
            amount = st.number_input("Amount ($)", min_value=1.0, max_value=5000.0, step=10.0, value=50.0)
            
            if st.button("Deposit Now", type="primary"):
                try:
                    # Endpoint: /payments/transactions/deposit/
                    url = f"{BASE_URL}/payments/transactions/deposit/"
                    payload = {"customer_id": current_user, "amount": amount}
                    res = requests.post(url, json=payload)
                    
                    if res.status_code == 200:
                        st.balloons()
                        st.success(res.json().get('message'))
                    else:
                        st.error(res.json().get('error', res.text))
                except Exception as e:
                    st.error(f"Connection Error: {e}")

        st.divider()

        # --- SECTION B: TRANSACTION HISTORY ---
        st.subheader("📜 Transaction History")
        
        if st.button("Refresh History"):
            try:
                url = f"{BASE_URL}/payments/transactions/"
                res = requests.get(url, params={"customer_id": current_user})
                
                if res.status_code == 200:
                    data = res.json()
                    # Handle pagination if DRF sends 'results'
                    history = data.get('results', data) if isinstance(data, dict) else data
                    
                    if not history:
                        st.info("No transactions found.")
                    else:
                        for tx in history:
                            t_type = tx.get('type', 'unknown').upper()
                            t_amt = tx.get('amount', 0)
                            t_date = tx.get('created_at', '')[:10]
                            
                            icon = "💰" if t_type == 'DEPOSIT' else "💸"
                            color = "green" if t_type == 'DEPOSIT' else "red"
                            
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 1, 1])
                                c1.markdown(f"**{icon} {t_type}**")
                                c2.markdown(f":{color}[${t_amt}]")
                                c3.caption(t_date)
                else:
                    st.error("Could not fetch history.")
            except Exception as e:
                st.error(f"Error: {e}")