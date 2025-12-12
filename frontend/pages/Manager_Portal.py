import streamlit as st
import requests
import json 
from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar
from django.db import IntegrityError
from hr.models import RegistrationApproval
from accounts.models import Customer, Manager
from common.models import User

generate_sidebar()
require_role(["MANAGER"])

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Manager Portal", page_icon="👔", layout="wide")
st.title("👔 Restaurant Command Center")

# TABS 
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 HR & Staff Management", "⚖️ Reputation & Disputes", "🚚 Delivery Dispatch", 
                                        "➕ Hire Staff", "✅ Approve Registrations"])

def fetch_pending_feedback():
    """Fetches all feedback awaiting manager review (UC13)."""
    try:
        resp = requests.get(f"{BASE_URL}/reputation/pending/")
        if resp.status_code == 200:
            return resp.json()
        st.error(f"Error fetching pending feedback: {resp.status_code}")
        return []
    except Exception as e:
        st.error(f"API Connection Failed for reputation data: {e}")
        return []

def send_feedback_resolution(feedback_id, decision_type):
    """
    Sends manager's resolution to the backend service.
    Decision_type can be 'resolve_complaint' or 'accept_compliment'.
    """
    try:
        if decision_type == 'accept_compliment':
            endpoint = f"{BASE_URL}/reputation/feedback/{feedback_id}/accept_compliment/"
            res = requests.post(endpoint, json={})
        else: # resolve_complaint (accept/dismiss)
            endpoint = f"{BASE_URL}/reputation/feedback/{feedback_id}/resolve_complaint/"
            res = requests.post(endpoint, json={'decision': decision_type})

        if res.status_code == 200:
            return True, res.json().get('message', 'Resolution successful.')
        else:
            return False, res.json().get('error', f"Server error: {res.text}")
    except Exception as e:
        return False, f"Connection error: {e}"

def kick_customer_api(customer_id):
    """UC10: Manually initiates the customer kick-out process."""
    try:
        # Assuming an accounts endpoint handles the full UC10 logic (blacklist, clear balance, deactivate)
        endpoint = f"{BASE_URL}/accounts/customers/{customer_id}/kick_out/"
        res = requests.post(endpoint, json={}) 

        if res.status_code == 200:
            return True, res.json().get('message', 'Customer processing complete.')
        else:
            return False, res.json().get('error', f"Server error: {res.text}")
    except Exception as e:
        return False, f"Connection error: {e}"


# ==========================================
# TAB 1: HR MANAGEMENT
# ==========================================
with tab1:
    st.header("Human Resources Dashboard")


    try:
        chefs_resp = requests.get(f"{BASE_URL}/menu/chefs/")       
        drivers_resp = requests.get(f"{BASE_URL}/delivery/drivers/") 
        cust_resp = requests.get(f"{BASE_URL}/accounts/customers/") 

        chefs = chefs_resp.json() if chefs_resp.status_code == 200 else []
        drivers = drivers_resp.json() if drivers_resp.status_code == 200 else []
        customers = cust_resp.json() if cust_resp.status_code == 200 else []

    except Exception as e:
        st.error(f"API Connection Failed: {e}")
        chefs, drivers, customers = [], [], []

    col1, col2 = st.columns(2)
    
    # --- CHEFS SECTION ---
    with col1:
        st.subheader(f"👨‍🍳 Kitchen Staff ({len(chefs)})")
        for chef in chefs:
            c_name = chef.get('name', 'Unknown')
            c_id = chef.get('id') 
            c_pay = chef.get('salary')
            is_active = chef.get('is_active', False)
            flagged_status = chef.get('status','')
            
            color = "green" if is_active else "red"
            
            with st.expander(f"👨‍🍳 :{color}[{c_name}] | Pay: ${c_pay}"):
                if flagged_status == 'Pending Demotion':
                    st.warning("SYSTEM FLAG: Pending Demotion (3 Warnings)")
                    if st.button("✅ Confirm Demotion", key=f"confirm_demotion_chef_{c_id}"):
                         st.info("UC09/UC11 Demotion logic pending...")
                
                if is_active:
                    if st.button("📉 Demote / Adjust Pay", key=f"demote_chef_{c_id}"):
                        st.info("Demotion logic not yet implemented.")
                else:
                    st.error("Inactive")
                    if st.button("♻️ Reactivate", key=f"rehire_chef_{c_id}"):
                        requests.patch(f"{BASE_URL}/menu/chefs/{c_id}/", json={'is_active': True})
                        st.rerun()

    # --- DRIVERS SECTION ---
    with col2:
        st.subheader(f"🚚 Delivery Fleet ({len(drivers)})")
        for driver in drivers:
            d_name = driver.get('username', 'Unknown')
            d_id = driver.get('id')
            d_pay = driver.get('pay', 0.0) 
            d_warnings = driver.get('warnings', 0)
            d_active = driver.get('is_active', False)
            d_status = driver.get('status', 'active')
            
            color = "green" if d_active else "red"
            flagged_status = d_status if d_status != 'active' else ''

            with st.expander(f"🛵 :{color}[{d_name}] | Pay: ${d_pay}"):
                st.write(f"⚠️ Warnings: {d_warnings}")

                if flagged_status == 'Pending Demotion':
                    st.warning("SYSTEM FLAG: Pending Demotion (3 Warnings)")
                    if st.button("✅ Confirm Demotion Driver", key=f"confirm_demotion_driver_{d_id}"):
                         st.info("UC09/UC11 Demotion logic pending...")
                
                if d_active:
                    if st.button("🔥 Terminate", key=f"fire_driver_{d_id}"):
                        requests.delete(f"{BASE_URL}/delivery/drivers/{d_id}/")
                        st.success("Driver terminated.")
                        st.rerun()

    st.divider()

    st.subheader("🚨 Customer Watchlist (UC10 Triggered Accounts)")
    
    # Filter: Show only if warnings > 0 OR blacklisted
    problem_customers = [
        c for c in customers 
        if c.get('warnings', 0) > 0 or c.get('is_blacklisted')
    ]
        
    for cust in problem_customers:
        c_name = cust.get('user', 'Unknown')
        c_id = cust.get('id')
        c_warnings = cust.get('warnings', 0)
        c_blacklisted = cust.get('is_blacklisted', False)
        c_status = cust.get('status')
        
        icon = "🛑" if c_blacklisted or c_status == 'Deactivated' else "⚠️"
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(f"**{icon} {c_name}** ({c_status})")
            c2.caption(f"Warn: {c_warnings}")
            c3.caption(f"Blacklisted: {c_blacklisted}")
            
            # UC10 Manual Override/Processing
            if c_status != 'Deactivated':
                if c4.button("❌ Process Kick-Out (UC10)", key=f"kick_{c_id}", use_container_width=True):
                    success, msg = kick_customer_api(c_id)
                    if success:
                        st.success(f"UC10 Success: {msg}")
                    else:
                        st.error(f"UC10 Failed: {msg}")
                    st.rerun()
            else:
                c4.caption("Account is Deactivated")


# ==========================================
# TAB 2: REPUTATION & DISPUTES (UC13, UC14)
# ==========================================
with tab2:
    st.header("⚖️ Dispute Resolution Center (UC13 / UC14)")
    pending_feedback = fetch_pending_feedback()
    
    if not pending_feedback:
        st.success("No active disputes requiring manager intervention.")
        
    for feedback in pending_feedback:
        fb_id = feedback.get('id')
        filer = feedback.get('filer_customer')
        target = feedback.get('target_user') # Assuming this returns a user struct or ID
        message = feedback.get('message', 'No details provided.')
        category = "COMPLIMENT" if feedback.get('is_compliment') else "COMPLAINT"
        weight = feedback.get('weight')
        
        container_color = "green" if category == "COMPLIMENT" else "red"
        
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            
            with c1:
                st.markdown(f"**:{container_color}[{category}]** | Weight: {weight}")
                st.write(f"**Filer:** {filer} | **Target:** {target}")
                st.caption(f"Details: {message}")
                
            with c2:
                if category == "COMPLAINT":
                    # UC13: Manager accepts -> Target penalized
                    if st.button("✅ Accept Complaint (Warn Target)", key=f"acc_comp_{fb_id}", type="primary", use_container_width=True):
                        success, msg = send_feedback_resolution(fb_id, 'accepted')
                        if success: st.success(msg); st.rerun()
                        else: st.error(msg)
                    
                    # UC14: Manager dismisses -> Filer penalized
                    if st.button("❌ Dismiss (Warn Filer)", key=f"dism_comp_{fb_id}", use_container_width=True):
                        success, msg = send_feedback_resolution(fb_id, 'dismissed')
                        if success: st.success(msg); st.rerun()
                        else: st.error(msg)
                        
                else: # COMPLIMENT
                    # UC13: Manager accepts -> Used for cancellation
                    if st.button("⭐ Accept Compliment", key=f"acc_complim_{fb_id}", type="primary", use_container_width=True):
                        success, msg = send_feedback_resolution(fb_id, 'accept_compliment')
                        if success: st.success(msg); st.rerun()
                        else: st.error(msg)


# [--- Tabs 3, 4, 5 remain largely unchanged ---]
# (Included below for completeness, but core changes were in Tabs 1 & 2)

# ==========================================
# TAB 3: DELIVERY DISPATCH
# ==========================================
with tab3:
    st.header("🚚 Live Dispatch (UC18 Integration)")
    st.write("Monitor active orders and assign drivers.")
    st.info("Waiting for orders...")

# ==========================================
# TAB 4: HIRE STAFF 
# ==========================================
with tab4:
    st.header("➕ Hire New Staff ")
    st.info("Create new accounts for Chefs and Drivers here.")
    
    hire_type = st.selectbox("Role to Hire", ["Chef", "Driver"])
    
    with st.form("hiring_form"):
        new_first_name = st.text_input("First name")
        new_last_name = st.text_input("Last name")
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
                        "password": new_password,
                        "first_name": new_first_name,
                        "last_name": new_last_name
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
                        if User.objects.filter(username=app.username).exists():
                            st.error(f"⚠️ Error: A user named '{app.username}' already exists!")
                            st.warning("You cannot create a duplicate. Please Reject this application or delete the existing user in Admin.")
                        else:
                            try:
                                # 1. Create User & Customer Profile
                                new_user = User(
                                    username=app.username,
                                    email=app.email,
                                    first_name=app.first_name,
                                    last_name=app.last_name,
                                    is_active=True
                                )
                                new_user.password = app.password_hash
                                new_user.save()
                                
                                Customer.objects.create(
                                    user=new_user, 
                                    balance=0.0, 
                                    status=Customer.STATUS_REGISTERED, 
                                    address=app.address
                                )
                                
                                # 2. Mark Approved
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