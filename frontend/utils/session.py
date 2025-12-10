"""
Session Management - Adapted for group's models
Uses UUID IDs and checks for Chef model
"""
import streamlit as st
from typing import Optional

def init_session():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.customer = None # Customer record if applicable
        st.session_state.chef = None # Chef record if applicable
        st.session_state.current_page = "Menu"

def get_customer_id() -> Optional[str]:
    """Get customer UUID (string) - for UC06, UC07"""
    if st.session_state.logged_in and st.session_state.customer:
        # Return UUID as string
        customer_id = st.session_state.customer.get('customer_id') or st.session_state.customer.get('id')
        return str(customer_id) if customer_id else None
    return None

def get_chef_id() -> Optional[str]:
    """Get chef UUID (string) - for UC19"""
    if st.session_state.logged_in and st.session_state.chef:
        chef_id = st.session_state.chef.get('chef_id') or st.session_state.chef.get('id')
        return str(chef_id) if chef_id else None
    return None

def is_chef() -> bool:
    """Check if logged in user is a chef (UC19)"""
    if not st.session_state.logged_in:
        return False
    # Check if chef record exists
    if st.session_state.chef:
        return True
    # Check user type
    if st.session_state.user:
        user_type = st.session_state.user.get('user_type', "")
        return user_type == 'chef'
    return False

def is_vip() -> bool:
    """Check if logged in user is VIP (UC06/UC07 discounts)"""
    if not st.session_state.logged_in:
        return False
    # Check customer record
    if st.session_state.customer:
        return st.session_state.customer.get('is_vip', False)
    # Check user type
    if st.session_state.user:
        return st.session_state.user.get('user_type', "") == 'vip'
    return False

def can_order() -> bool:
    """Check if user can place orders (customers and VIPs) (UC07)"""
    if not st.session_state.logged_in:
        return False
    # Must have a customer record to order
    if st.session_state.customer:
        return True
    # Check user type
    if st.session_state.user:
        user_type = st.session_state.user.get('user_type', 'visitor')
        return user_type in ['customer', 'vip']
    return False

def get_user_type_for_menu() -> str:
    """Get user type string for menu filtering (UC06)"""
    if not st.session_state.logged_in:
        return 'Visitor'
    
    # VIPs/Chefs see all dishes (UC06)
    if is_vip() or is_chef():
        return 'VIP'
    
    if st.session_state.user:
        user_type = st.session_state.user.get('user_type', 'visitor')
        mapping = {
            'visitor': 'Visitor',
            'customer': 'Customer',
            'vip': 'VIP',
            'chef': 'VIP', # Chefs see all dishes like VIPs
            'manager': 'VIP',
        }
        return mapping.get(user_type, 'Customer')
    return 'Customer'

def get_user_allergies() -> list:
    """Get user's allergies list - for UC06 display/filtering"""
    if not st.session_state.logged_in or not st.session_state.customer:
        return []
    
    # Allergies might be stored in customer record
    allergies = st.session_state.customer.get('allergies', [])
    if isinstance(allergies, list):
        return allergies
    elif isinstance(allergies, str):
        return [a.strip() for a in allergies.split(',') if a.strip()]
    return []

def refresh_user_data():
    """Placeholder for refreshing user data from API after major action (e.g., checkout)"""
    pass

def logout():
    """Clear session and logout (UC03)"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.customer = None
    st.session_state.chef = None
    st.session_state.current_page = "Menu"