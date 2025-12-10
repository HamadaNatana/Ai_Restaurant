import streamlit as st
import requests

# CONFIGURATION
BASE_URL = "http://127.0.0.1:8000"
# Adjust these paths to match Hassan's urls.py exactly!
API_URLS = {
    "menu": f"{BASE_URL}/menu/api/list/",        # Or /api/get_menu/
    "add_cart": f"{BASE_URL}/orders/api/add/",   # Or /api/add_to_cart/
    "get_cart": f"{BASE_URL}/orders/api/cart/",
    "checkout": f"{BASE_URL}/orders/api/checkout/"
}

st.set_page_config(page_title="Menu & Order", page_icon="🍔", layout="wide")
st.title("🍔 AI Restaurant Menu")

# --- SIDEBAR: User Settings (Simulates Login) ---
with st.sidebar:
    st.header("👤 Customer Info")
    # For demo purposes, we manually set the user ID. 
    # In production, this would come from a real login.
    user_id = st.text_input("Customer ID (UUID)", value="Paste-UUID-Here")
    user_type = st.selectbox("Status", ["Visitor", "Registered", "VIP"])
    
    st.subheader("🛒 Your Cart")
    if st.button("Refresh Cart"):
        try:
            cart = requests.get(f"{API_URLS['get_cart']}?customer_id={user_id}").json()
            if 'items' in cart:
                st.session_state.cart_total = cart.get('total', 0)
                st.session_state.cart_items = cart.get('items', [])
            else:
                st.warning("Cart empty")
        except:
            st.error("Cart Error")

    if 'cart_items' in st.session_state and st.session_state.cart_items:
        for item in st.session_state.cart_items:
            st.write(f"- {item['name']} x{item['qty']} (${item['price']})")
        st.divider()
        st.write(f"**Total: ${st.session_state.get('cart_total', 0)}**")
        
        if st.button("💳 Checkout Now"):
            try:
                res = requests.post(API_URLS['checkout'], json={"customer_id": user_id})
                if res.status_code == 200:
                    st.success("Order Placed! 🚀")
                    st.balloons()
                    # Clear cart display
                    st.session_state.cart_items = []
                else:
                    st.error(f"Failed: {res.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# --- MAIN MENU AREA ---
st.header("Our Selection")

# Filters
col1, col2 = st.columns(2)
search_query = col1.text_input("🔍 Search Dishes")
allergy_mode = col2.checkbox("Enable Allergy Filter (Safety Mode)")

# Fetch Menu from Backend
try:
    # We pass the user_type and customer_id so the BACKEND does the filtering (UC 06/22)
    params = {
        "user_type": user_type,
        "search": search_query,
        "customer_id": user_id if allergy_mode else None
    }
    response = requests.get(API_URLS['menu'], params=params)
    
    if response.status_code == 200:
        data = response.json()
        dishes = data.get('dishes', [])
        message = data.get('message', '')
        
        if message:
            st.info(message)
            
        if not dishes:
            st.warning("No dishes found.")
            
        # Display Dishes in a Grid
        for dish in dishes:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                # Image placeholder or real image if available
                c1.write("🍲") 
                
                with c2:
                    st.subheader(dish['name'])
                    st.write(dish.get('description', 'Delicious food.'))
                    if dish.get('special_for_vip'):
                        st.caption("✨ VIP Exclusive")
                
                with c3:
                    st.write(f"**${dish['price']}**")
                    if st.button("Add +", key=f"add_{dish['dish_id']}"):
                        if not user_id or user_id == "Paste-UUID-Here":
                            st.error("Please enter a Customer ID in the sidebar first.")
                        else:
                            # Call Backend to Add to Cart (UC 07)
                            res = requests.post(API_URLS['add_cart'], json={
                                "customer_id": user_id,
                                "dish_id": dish['dish_id']
                            })
                            if res.status_code == 200:
                                st.toast(f"Added {dish['name']} to cart!")
                            else:
                                st.error("Failed to add.")
    else:
        st.error(f"Failed to load menu. Status: {response.status_code}")

except Exception as e:
    st.error(f"Could not connect to Kitchen (Backend). Is Django running? {e}")