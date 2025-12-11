import streamlit as st

def require_role(allowed_roles):
    """
    Enforces role-based access control.
    """
    # 1. Initialize default state if user goes directly to a page without logging in
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["role"] = "VISITOR"
        st.session_state["username"] = None

    # 2. Check the role
    current_role = st.session_state["role"]
    
    # If the user's role is not in the allowed list
    if current_role not in allowed_roles:
        # Clear the page
        st.error(f"⛔ Access Denied: You are logged in as '{current_role}', but this page is for {allowed_roles} only.")
        
        # Add a button to go back to login
        if st.button("Go to Login Page"):
            st.switch_page("pages/Account_Portal.py") # Adjust filename if needed
            
        st.stop()  # HALT execution immediately so no other code runs