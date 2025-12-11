import streamlit as st

def generate_sidebar():
    # 1. Ensure the user has a role (default to Visitor)
    if "role" not in st.session_state:
        st.session_state["role"] = "VISITOR"
        st.session_state["logged_in"] = False

    role = st.session_state["role"]

    with st.sidebar:
        st.header(f"Role: {role}")
        
        # --- SHARED PAGES (Everyone sees these) ---
        st.page_link("pages/Account_Portal.py", label="👤 Account / Login", icon="🔓")
        
        # --- VISITOR & CUSTOMER ---
        if role in ["VISITOR", "CUSTOMER", "VIP", "CHEF"]:
             st.page_link("pages/Menu_&_Order.py", label="Menu & Order", icon="🍔")
             st.page_link("pages/AI_Assistant.py", label="AI Assistant", icon="🤖")
             st.page_link("pages/Discussion_Board.py", label="Discussion", icon="💬")

        # --- CUSTOMER ONLY ---
        if role in ["CUSTOMER", "VIP"]:
            st.page_link("pages/Allergy_Settings.py", label="Allergy Settings", icon="⚠️")

        # --- STAFF ONLY ---
        if role == "MANAGER":
            st.divider()
            st.page_link("pages/Manager_Portal.py", label="Manager Dashboard", icon="📈")
            
        if role == "DRIVER":
            st.divider()
            st.page_link("pages/Driver_Portal.py", label="Driver Dashboard", icon="🛵")

        # --- LOGOUT BUTTON ---
        if st.session_state["logged_in"]:
            st.divider()
            if st.button("Log Out", type="primary"):
                st.session_state["logged_in"] = False
                st.session_state["role"] = "VISITOR"
                st.session_state["username"] = None
                st.rerun()