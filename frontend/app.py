"""
AI Restaurant - Main Streamlit Application
Links all pages and handles the main navigation logic.
"""

import streamlit as st
import requests
from utils.session import init_session, logout, is_chef, is_vip
from pages import menu_page, cart_pages, chef_dishes_pages # Import pages module

# Initialize session state variables
init_session()

# Page config
st.set_page_config(
    page_title="AI Restaurant",
    page_icon="🍽️",
    layout="wide"
)

# --- Sidebar Content ---
with st.sidebar:
    st.title("🍽️ AI Restaurant")
    st.markdown("---")
    
    if not st.session_state.logged_in:
        # Login Form (UC03)
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submit:
                if not username or not password:
                    st.error("Please enter username and password.")
                else:
                    try:
                        # Direct call to the expected authentication endpoint
                        resp = requests.post(
                            "http://localhost:8000/api/users/login/", # Adjusted to common user login path
                            json={"username": username, "password": password},
                            timeout=10
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            
                            # Store user data (UC03 Postconditions)
                            st.session_state.logged_in = True
                            st.session_state.user = data.get('user', data)
                            
                            if 'customer' in data:
                                st.session_state.customer = data['customer']
                            
                            if 'chef' in data:
                                st.session_state.chef = data['chef']
                                
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            error_data = resp.json() if resp.content else {}
                            error_msg = error_data.get('error', error_data.get('detail', 'Invalid credentials'))
                            st.error(f"Login Failed: {error_msg}")
                            
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to server. Is the backend running?")
                    except requests.exceptions.Timeout:
                        st.error("Request timed out.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        st.markdown("---")
        st.caption("Don't have an account? Contact management.")
        
    else:
        # Logged In User Info
        user = st.session_state.user or {}
        username = user.get('username', 'User')
        user_type = user.get('user_type', 'customer')
        
        st.success(f"Welcome, {username}!")
        st.caption(f"Role: {user_type.title()}")
        
        if st.session_state.customer:
            balance = st.session_state.customer.get('balance', 0)
            st.info(f"Balance: **${float(balance):.2f}**")
            if is_vip():
                st.success("VIP Member")
        
        st.markdown("---")
        
        # Logout
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
        
        st.markdown("---")

    # --- Navigation ---
    st.subheader("Navigation")
    page_options = ["Menu"]
    
    if st.session_state.logged_in:
        page_options.append("Cart")
    
    # Add 'My Dishes' only for Chefs (UC19)
    if is_chef():
        page_options.append("My Dishes")
        
    # Set choice to the last visited page, defaulting to "Menu"
    if 'current_page' not in st.session_state or st.session_state.current_page not in page_options:
        st.session_state.current_page = "Menu"

    choice = st.radio("Go to", page_options, label_visibility="collapsed", index=page_options.index(st.session_state.current_page))
    st.session_state.current_page = choice

# --- Main Content Area ---

if st.session_state.current_page == "Menu":
    menu_page.render_menu_page()
elif st.session_state.current_page == "Cart":
    cart_pages.render_cart_page()
elif st.session_state.current_page == "My Dishes":
    chef_dishes_pages.render_chef_dishes_page()

# --- Footer ---
st.markdown("---")
st.caption("AI Restaurant Management System | Menu, Ordering, and Dish Management.")
