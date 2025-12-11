import streamlit as st
import requests
from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar

generate_sidebar()
require_role(["MANAGER"])
# CONFIGURATION
BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Manager Portal", page_icon="👔", layout="wide")
st.title("👔 Restaurant Command Center")

# TABS FOR EVERY DOMAIN
tab1, tab2, tab3 = st.tabs(["👥 HR & Staff", "⚖️ Reputation & Disputes", "🚚 Delivery Dispatch"])

# ==========================================
# TAB 1: HR MANAGEMENT (Isaac's Domain)
# ==========================================
with tab1:
    st.header("Human Resources")
    
    try:
        data = requests.get(f"{BASE_URL}/hr/api/dashboard/").json()
        chefs = data.get('chefs', [])
        drivers = data.get('drivers', [])
        customers = data.get('customers', [])
    except:
        st.error("Backend offline. Is Django running?")
        chefs, drivers, customers = [], [], []

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"👨‍🍳 Chefs ({len(chefs)})")
        for chef in chefs:
            status_color = "green" if chef['is_active'] else "red"
            with st.expander(f":{status_color}[{chef['name']}] (Salary: ${chef['salary']})"):
                st.write(f"**Demotions:** {chef['demotion_count']}")
                if chef['is_active']:
                    c1, c2 = st.columns(2)
                    if c1.button("📉 Demote", key=f"d_{chef['chef_id']}"):
                        requests.post(f"{BASE_URL}/hr/api/chef/{chef['chef_id']}/", json={'action': 'demote'})
                        st.rerun()
                    if c2.button("💰 Bonus", key=f"b_{chef['chef_id']}"):
                        requests.post(f"{BASE_URL}/hr/api/chef/{chef['chef_id']}/", json={'action': 'bonus'})
                        st.success("Bonus sent!")
                        st.rerun()
                else:
                    st.error("FIRED due to incompetence.")

    with col2:
        st.subheader(f"🚚 Drivers ({len(drivers)})")
        for driver in drivers:
            with st.expander(f"{driver['username']} (Pay: ${driver['pay']})"):
                if driver['is_active']:
                    if st.button("🔥 Fire Driver", key=f"fd_{driver['driver_id']}"):
                        requests.post(f"{BASE_URL}/hr/api/driver/{driver['driver_id']}/", json={'action': 'fire'})
                        st.rerun()
                else:
                    st.error("Terminated.")

    st.divider()
    st.subheader("🚨 Customer Watchlist")
    for cust in customers:
        if cust['warnings'] > 0 or cust['is_blacklisted']:
            icon = "🛑" if cust['is_blacklisted'] else "⚠️"
            st.warning(f"{icon} **{cust['username']}** | Warnings: {cust['warnings']} | Balance: ${cust['balance']}")
            if not cust['is_blacklisted']:
                if st.button(f"Kick & Seize Funds", key=f"kick_{cust['customer_id']}"):
                    requests.post(f"{BASE_URL}/hr/api/customer/kick/{cust['customer_id']}/")
                    st.rerun()

# ==========================================
# TAB 2: REPUTATION (Isaac's Domain)
# ==========================================
with tab2:
    st.header("Dispute Resolution")
    try:
        disputes = requests.get(f"{BASE_URL}/reputation/api/pending/").json()
    except:
        disputes = []

    if not disputes:
        st.success("No pending disputes.")
    
    for d in disputes:
        with st.container(border=True):
            cols = st.columns([0.5, 4])
            cols[0].title("⚖️")
            with cols[1]:
                type_label = "❤️ Compliment" if d['is_compliment'] else "😡 Complaint"
                st.subheader(f"{type_label} (Weight: {d['weight']})")
                st.write(f"**{d['filer_name']}** reported **{d['target_name']}**")
                st.info(f"\"{d['message']}\"")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ Accept (Valid)", key=f"acc_{d['feedback_id']}"):
                    requests.post(f"{BASE_URL}/reputation/api/resolve/{d['feedback_id']}/", json={'decision': 'accepted'})
                    st.rerun()
                if c2.button("❌ Dismiss (Frivolous)", key=f"dis_{d['feedback_id']}"):
                    requests.post(f"{BASE_URL}/reputation/api/resolve/{d['feedback_id']}/", json={'decision': 'dismissed'})
                    st.rerun()

# ==========================================
# TAB 3: DELIVERY DISPATCH (Sadeq's Domain)
# ==========================================
with tab3:
    st.header("🚚 Delivery Dispatch")
    st.info("System is waiting for orders ready for delivery...")
    
    # Placeholder for presentation flow
    with st.expander("Order #1024 - Downtown (Est. Tip: $5)"):
        st.write("**Bids Received:**")
        st.write("1. Driver John - Bid: $4.50")
        st.write("2. Driver Sarah - Bid: $5.00")
        if st.button("Assign to John ($4.50)"):
            st.success("Order #1024 assigned to Driver John.")