import streamlit as st
import requests
import json 
from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar

generate_sidebar()
require_role(["DRIVER"])

BASE_URL = "http://127.0.0.1:8000"
st.title("🚚 Delivery Driver Hub")

# --- Helper Function for UC12 Complaint Form (Driver's Version) ---

def show_feedback_form_driver(driver_id):
    st.markdown("---")
    st.subheader("📢 File Feedback (UC12)")
    st.caption("Submit a compliment or complaint against a Customer, Chef, or Dish.")

    with st.form("driver_feedback_form"):
        col1, col2 = st.columns(2)
        
        # 1. Category (Complaint or Compliment)
        category = col1.selectbox("Category of Feedback", ["Complaint", "Compliment"])
        
        # 2. Target Type (Drivers only file against specific targets)
        target_type = col2.selectbox(
            "Target Type", 
            ["customer", "chef", "dish"],
            help="Who or what is this feedback about?"
        )
        
        # 3. Target ID
        target_id = st.text_input(
            f"Enter {target_type.title()} ID or Username", 
            help=f"Example: Username of the customer or ID of the dish."
        )
        
        # 4. Message
        message = st.text_area("Your Feedback Details", max_chars=500)
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            if not target_id or not message:
                st.error("Target ID and message are required.")
            else:
                payload = {
                    "filer_id": str(driver_id), # Driver ID is the filer
                    "target_type": target_type,
                    "target_id": target_id,
                    "message": message,
                    "category": category # Passed to backend service
                }
                
                # --- Call the file_feedback API ---
                try:
                    # Assuming your backend can map driver_id to customer_id if needed
                    res = requests.post(f"{BASE_URL}/reputation/file_feedback/", json=payload)
                    
                    if res.status_code == 200:
                        st.success(res.json().get('message', 'Feedback submitted successfully!'))
                    else:
                        error_msg = res.json().get('error', res.text)
                        st.error(f"Filing Failed: {error_msg}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

# --- Main Driver Portal Layout ---

# Assuming 'username' is the driver's unique identifier (the 'id' used in the API calls)
driver_id = st.session_state.get("username", "GUEST_DRIVER_001") 

tab1, tab2, tab3 = st.tabs(["Open Jobs (Bid)", "My Deliveries", "Reputation & Feedback"])

with tab1:
    st.subheader("Available Orders (UC17)")
    # In a real demo, you'd fetch "Ready" orders here
    # Placeholder for the presentation flow
    with st.expander("Order #992 - Downtown (Est. Tip: $5)"):
        bid_price = st.number_input("Your Bid ($)", min_value=3.0, value=5.0)
        if st.button("Submit Bid"):
            # You would call the bidding API here
            st.success(f"Bid of ${bid_price} submitted!")

with tab2:
    st.subheader("Current Assignments (UC18)")
    st.info("No active deliveries.")

with tab3:
    st.header("Driver Status & Reputation")
    
    # 1. Status Check (UC15/UC09/UC11 Integration)
    try:
        # Assuming you have an endpoint to get detailed driver status/warnings
        status_resp = requests.get(f"{BASE_URL}/delivery/drivers/{driver_id}/status/")
        
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            warnings = status_data.get('warnings', 0)
            employee_status = status_data.get('status', 'active')
            
            st.metric("Warnings", f"{warnings}/3")
            
            if employee_status == 'Pending Demotion':
                st.error("🛑 **ACTION REQUIRED**: You have been flagged for demotion review by the Manager (UC09/UC11).")
            elif warnings >= 1:
                st.warning(f"Accumulating 3 warnings will flag your account for demotion review.")
            else:
                st.success("Clean Record. Keep up the great work!")
        else:
            st.error("Could not fetch driver status.")
            
    except Exception:
        st.error("API Connection Failed for status check.")
        
    st.markdown("---")
    
    # 2. File Feedback Form (UC12)
    show_feedback_form_driver(driver_id)