import streamlit as st
import os
import django
import sys
from pathlib import Path
from utils.sidebar import generate_sidebar

generate_sidebar()

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
from django.db import IntegrityError
from accounts.models import Customer, Manager 
from menu.models import Chef
from delivery.models import Driver
from common.models import User
from hr.models import RegistrationApproval

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
    # Clear other session data specific to roles if needed

# ---------------- Page Views ----------------
def show_manager_dashboard(user):
    st.header("📈 Manager Dashboard")
    st.write(f"Hello, {user.username}. Here are today's stats.")
    # Add manager specific logic here (e.g., View Revenue, Manage Staff)
    st.info("System Status: Online")

def show_chef_interface(user):
    st.header("👨‍🍳 Chef Kitchen View")
    st.write("Current Orders Queue:")
    # Add chef logic here (e.g., List active orders, mark as cooked)
    st.warning("3 Orders Pending")

def show_driver_interface(user):
    st.header("🛵 Driver Portal")
    st.write("Available Deliveries:")
    # Add driver logic here (e.g., View delivery address, mark delivered)
    st.success("You are active for deliveries.")

def show_customer_profile(username):
    try:
        cust = Customer.objects.get(user__username=username)
        st.subheader(f"Welcome, {cust.user.first_name or username}")
        
        col1, col2 = st.columns(2)
        col1.metric("Wallet Balance", f"${cust.balance}")
        col2.metric("Warnings", f"{cust.warnings}/3")
        
        if cust.status == 'vip':
            st.balloons()
            st.success("🌟 **VIP Member** - 5% Discount Applied")
        else:
            st.info("Regular Membership")
            
    except Customer.DoesNotExist:
        st.error("Customer profile data is missing. Please contact support.")

# ---------------- UI Layout ----------------
st.set_page_config(page_title="Restaurant Portal", page_icon="🍽️")
st.title("🍽️ Restaurant Portal")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ==========================================
# VIEW: LOGGED IN (ROUTER)
# ==========================================
if st.session_state["logged_in"]:
    # Retrieve user object again to pass to sub-functions if needed
    # Or just use the session data
    current_username = st.session_state["username"]
    current_role = st.session_state["role"]
    
    # Logout button in sidebar to keep main area clean
    with st.sidebar:
        st.write(f"Logged in as: **{current_username}**")
        st.write(f"Role: **{current_role}**")
        if st.button("Log Out"):
            logout_user()
            st.rerun()

    # --- ROLE BASED ROUTING ---
    try:
        # We fetch the user object to pass to the dashboards
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
            st.error("Role not recognized. Please contact admin.")
            
    except User.DoesNotExist:
        st.error("User session invalid. Please log out and log in again.")

# ==========================================
# VIEW: LOGIN / REGISTER
# ==========================================
else:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 New Customer Register"])

    # --- TAB 1: LOGIN ---
    with tab1:
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
                    # Determine Role Priority
                    # This assumes OneToOne fields named 'manager', 'chef', 'driver', 'customer'
                    role = "VISITOR"
                    
                    if hasattr(user, 'manager'):
                        role = "MANAGER"
                    elif hasattr(user, 'chef'):  # Added Chef Check
                        role = "CHEF"
                    elif hasattr(user, 'driver'): # Added Driver Check
                        role = "DRIVER"
                    else:
                        try:
                            cust = Customer.objects.get(user=user)
                            if cust.is_blacklisted:
                                st.error("🚫 Access Denied: This account has been blacklisted due to numerous violations.")
                                st.stop()
                            role = "VIP" if cust.status == 'vip' else "CUSTOMER"
                        except Customer.DoesNotExist:
                            role = "VISITOR"

                    login_user(user.username, role)
                    st.success(f"Login successful! Redirecting to {role} dashboard...")
                    st.rerun()
            else:
                st.error("Invalid username or password.")

    # --- TAB 2: REGISTER ---
    with tab2:
        st.info("Only Visitors can register here. Staff must be added by a Manager.")
        with st.form("register_form"):
            first_name = st.text_input("Enter First Name").strip()
            last_name = st.text_input("Enter Last Name").strip()
            new_user = st.text_input("Choose Username").strip()
            new_email = st.text_input("Email Address").strip()
            new_pass = st.text_input("Choose Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            address = st.text_area("Delivery Address (Optional)").strip()
            #deposit = st.number_input("Initial Deposit ($)", min_value=0.0, value=0.0)
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
                        from django.contrib.auth.hashers import make_password
                        hashed_pw = make_password(new_pass)
                        
                        RegistrationApproval.objects.create(
                            username=new_user,
                            email=new_email,
                            first_name=first_name,
                            last_name=last_name,
                            password_hash=hashed_pw,
                            address=address,
                            status='pending'
                            # manager is left NULL automatically
                        )
                        st.success("✅ Application submitted! Please wait for a Manager to approve your account.")
                        
                except Exception as e:
                    st.error(f"Error submitting application: {e}")
