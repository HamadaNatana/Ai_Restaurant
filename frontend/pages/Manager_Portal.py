import streamlit as st
import requests
from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar
from django.db import IntegrityError
from hr.models import RegistrationApproval
from accounts.models import Customer,Manager
from common.models import User

generate_sidebar()
require_role(["MANAGER"])

BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Manager Portal", page_icon="👔", layout="wide")
st.title("👔 Restaurant Command Center")

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 HR & Staff", "⚖️ Reputation & Disputes", "🚚 Delivery Dispatch", 
                                        "➕ Hire Staff", "✅ Approve Registrations"])

# ==========================================
# TAB 1: HR MANAGEMENT
# ==========================================
with tab1:
    st.header("Human Resources Dashboard")

    # Safe separate fetches
    try:
        # We manually fetch the lists instead of a custom "dashboard" endpoint
        chefs_resp = requests.get(f"{BASE_URL}/chefs/")
        drivers_resp = requests.get(f"{BASE_URL}/drivers/")
        cust_resp = requests.get(f"{BASE_URL}/customers/")

        # Use empty list if the request failed or wasn't JSON
        chefs = chefs_resp.json() if chefs_resp.status_code == 200 else []
        drivers = drivers_resp.json() if drivers_resp.status_code == 200 else []
        customers = cust_resp.json() if cust_resp.status_code == 200 else []

    except Exception as e:
        st.error(f"Connection failed: {e}")
        chefs, drivers, customers = [], [], []

    # --- CHEFS SECTION ---
    st.subheader(f"👨‍🍳 Kitchen Staff ({len(chefs)})")
    for chef in chefs:
        # Serializer access: chef['user']['username']
        # We use .get() to avoid crashing if data is missing
        user_data = chef.get('user', {})
        username = user_data.get('username', 'Unknown')
        salary = chef.get('salary', 0.0)
        rating = chef.get('rating', 0.0)
        
        with st.expander(f"👨‍🍳 {username} | Rating: {rating}/5.0"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Salary", f"${salary}")
            c2.metric("Rating", f"{rating}")
            
            # ACTIONS
            if c3.button("💰 Give Bonus ($100)", key=f"bonus_chef_{chef['id']}"):
                try:
                    # Assumes a custom action @action(detail=True) in ViewSet
                    res = requests.post(f"{BASE_URL}/chefs/{chef['id']}/update_salary/", json={'amount': 100, 'action': 'bonus'})
                    if res.status_code == 200:
                        st.success(f"Bonus sent to {username}!")
                        st.rerun()
                    else:
                        st.error("Failed to send bonus.")
                except:
                    st.error("Connection error.")

            if c3.button("📉 Demote / Penalize", key=f"demote_chef_{chef['id']}"):
                st.warning("Demotion feature pending backend implementation.")

    st.divider()

    # --- DRIVERS SECTION ---
    st.subheader(f"🚚 Delivery Fleet ({len(drivers)})")
    for driver in drivers:
        user_data = driver.get('user', {})
        username = user_data.get('username', 'Unknown')
        salary = driver.get('salary', 0.0)
        rating = driver.get('rating', 0.0)
        
        with st.expander(f"🛵 {username} | Rating: {rating}/5.0"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Hourly Pay", f"${salary}")
            c2.metric("Deliveries", "N/A") 
            
            if c3.button("🔥 Terminate", key=f"fire_driver_{driver['id']}"):
                if st.checkbox(f"Confirm termination of {username}?", key=f"confirm_{driver['id']}"):
                    # Calls Standard DRF Delete
                    requests.delete(f"{BASE_URL}/drivers/{driver['id']}/")
                    st.success("Driver terminated.")
                    st.rerun()

    st.divider()

    # --- CUSTOMER WATCHLIST ---
    st.subheader("🚨 Customer Watchlist")
    for cust in customers:
        user_data = cust.get('user', {})
        username = user_data.get('username', 'Unknown')
        warnings = cust.get('warnings', 0)
        is_blacklisted = cust.get('is_blacklisted', False)
        balance = cust.get('balance', 0.0)

        # Only show problem customers
        if warnings > 0 or is_blacklisted:
            status_icon = "🛑" if is_blacklisted else "⚠️"
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{status_icon} {username}**")
                c2.write(f"Warnings: {warnings}/3")
                c3.write(f"Wallet: ${balance}")
                
                if not is_blacklisted:
                    if st.button("🚫 Blacklist & Seize Funds", key=f"kick_{cust['id']}"):
                        requests.post(f"{BASE_URL}/customers/{cust['id']}/blacklist/")
                        st.rerun()

# ==========================================
# TAB 2: REPUTATION
# ==========================================
with tab2:
    st.header("Dispute Resolution Center")
    # Placeholder: Retrieve pending complaints
    st.info("No active disputes requiring manager intervention.")

# ==========================================
# TAB 3: DELIVERY DISPATCH
# ==========================================
with tab3:
    st.header("🚚 Live Dispatch")
    st.write("Monitor active orders and assign drivers.")
    # You would fetch 'Order' models here
    st.info("Waiting for orders...")

# ==========================================
# TAB 4: HIRE STAFF 
# ==========================================
with tab4:
    st.header("➕ Hire New Staff")
    st.info("Create new accounts for Chefs and Drivers here.")
    
    hire_type = st.selectbox("Role to Hire", ["Chef", "Driver"])
    
    with st.form("hiring_form"):
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Temporary Password", type="password")
        starting_salary = st.number_input("Starting Salary", min_value=10.0, value=20.0)
        submitted = st.form_submit_button("Create Account")
        
        if submitted:
            if not new_username or not new_password:
                st.error("Username and Password are required.")
            else:
                # Construct payload matching the Nested Serializer
                payload = {
                    "user": {
                        "username": new_username,
                        "email": new_email,
                        "password": new_password
                    },
                    "salary": starting_salary
                }
                
                # Determine endpoint
                endpoint = "chefs" if hire_type == "Chef" else "drivers"
                
                try:
                    res = requests.post(f"{BASE_URL}/{endpoint}/", json=payload)
                    if res.status_code == 201:
                        st.success(f"Successfully hired {hire_type}: {new_username}")
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection Failed: {e}")

# ==========================================
# TAB 5: APPROVE REGISTRATIONS
# ==========================================

with tab5:
    st.header("✅ Registration Approvals")
    
    pending_apps = RegistrationApproval.objects.filter(status='pending')
    
    if not pending_apps.exists():
        st.success("No pending applications.")
    else:
        for app in pending_apps:
            with st.container(border=True):
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.subheader(f"👤 {app.username}")
                    st.write(f"**Name:** {app.first_name} {app.last_name}")
                    st.write(f"**Email:** {app.email}")
                    st.write(f"**Address:** {app.address}") 
                    st.caption(f"Applied: {app.created_at}")

                with col2:
                    if st.button("✅ Approve", key=f"app_{app.id}", use_container_width=True):
                        # --- SAFETY CHECK 1: DOES USER EXIST? ---
                        if User.objects.filter(username=app.username).exists():
                            st.error(f"⚠️ Error: A user named '{app.username}' already exists!")
                            st.warning("You cannot create a duplicate. Please Reject this application or delete the existing user in Admin.")
                        else:
                            try:
                                # 1. Create User
                                new_user = User(
                                    username=app.username,
                                    email=app.email,
                                    first_name=app.first_name,
                                    last_name=app.last_name,
                                    is_active=True
                                )
                                new_user.password = app.password_hash 
                                new_user.save()
                                
                                # 2. Create Customer Profile
                                Customer.objects.create(
                                    user=new_user, 
                                    balance=0.0, 
                                    status='regular',
                                    address=app.address
                                )
                                
                                # 3. Mark Approved
                                app.status = 'approved'
                                app.save()
                                
                                st.success(f"Approved {app.username}!")
                                st.rerun()
                                
                            except IntegrityError:
                                st.error("Database Error: Username taken (caught by integrity check).")
                            except Exception as e:
                                st.error(f"Unexpected Error: {e}")

                    st.divider()

                    # REJECT SECTION
                    reason = st.text_input("Rejection Reason", placeholder="e.g., Duplicate account", key=f"reason_{app.id}")
                    
                    if st.button("❌ Reject", key=f"rej_{app.id}", use_container_width=True):
                        if not reason:
                            st.error("Please enter a reason.")
                        else:
                            app.status = 'rejected'
                            app.rejection_reason = reason
                            app.active = False
                            app.save()
                            st.warning(f"Rejected {app.username}.")
                            st.rerun()