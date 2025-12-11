import streamlit as st
import requests

# CONFIGURATION
BASE_URL = "http://127.0.0.1:8000"

# --- UPDATED URLS FOR THE NEW "DAVID FORMAT" ---
API_URLS = {
    # 1. FIXED: Menu is now served by a Router at /dishes/ (Plural)
    "menu": f"{BASE_URL}/menu/api/dishes/",
    
    # 2. Cart is a single APIView handling GET (view) and POST (add)
    "cart": f"{BASE_URL}/orders/api/cart/",
    
    # 3. Checkout is its own APIView
    "checkout": f"{BASE_URL}/orders/api/checkout/"
}

st.set_page_config(page_title="Menu & Order", page_icon="🍔", layout="wide")
st.title("🍔 AI Restaurant Menu")

# ---------------------------------------------------------
# SIDEBAR: USER LOGIN & CART
# ---------------------------------------------------------
with st.sidebar:
    st.header("👤 Customer Info")
    
    # Try to get session info from the Account Portal (if used)
    if "username" in st.session_state and st.session_state["username"]:
        default_user = st.session_state["username"] 
    else:
        default_user = "Paste-UUID-Here"

    user_id = st.text_input("Customer ID / Username", value=default_user, help="Enter your Customer ID (UUID) or Username")
    user_type = st.selectbox("Status", ["Visitor", "Registered", "VIP", "Manager", "Chef"])
    
    st.divider()
    st.subheader("🛒 Your Cart")
    
    # REFRESH CART BUTTON
    if st.button("Refresh Cart"):
        if user_id and user_id != "Paste-UUID-Here":
            try:
                # NEW LOGIC: GET request to /orders/api/cart/
                res = requests.get(API_URLS['cart'], params={"customer_id": user_id})
                
                if res.status_code == 200:
                    cart_data = res.json()
                    st.session_state.cart_items = cart_data.get('items', [])
                    st.session_state.cart_total = cart_data.get('total', 0)
                else:
                    st.warning("Cart empty or not found.")
                    st.session_state.cart_items = []
            except Exception as e:
                st.error(f"Cart Error: {e}")

    # DISPLAY CART
    if 'cart_items' in st.session_state and st.session_state.cart_items:
        for item in st.session_state.cart_items:
            # Serializer uses 'dish_name', old view used 'name'
            d_name = item.get('dish_name') or item.get('name') or "Unknown Dish"
            st.write(f"- {d_name} x{item['quantity']} (${item.get('unit_price', 0)})")
            
        st.divider()
        st.write(f"**Total: ${st.session_state.get('cart_total', 0)}**")
        
        # CHECKOUT BUTTON
        if st.button("💳 Checkout Now"):
            try:
                # NEW LOGIC: POST request to /orders/api/checkout/
                res = requests.post(API_URLS['checkout'], json={"customer_id": user_id})
                
                if res.status_code == 200:
                    result = res.json()
                    st.success("Order Placed Successfully! 🚀")
                    st.balloons()
                    if 'new_balance' in result:
                        st.info(f"Remaining Balance: ${result['new_balance']}")
                    st.session_state.cart_items = [] # Clear UI cart
                else:
                    err = res.json().get('error', res.text)
                    st.error(f"Checkout Failed: {err}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# ---------------------------------------------------------
# MAIN AREA: MENU
# ---------------------------------------------------------
st.header("Our Selection")

# Filters
col1, col2 = st.columns(2)
search_query = col1.text_input("🔍 Search Dishes")
allergy_mode = col2.checkbox("Enable Allergy Filter (Safety Mode)")

# Fetch Menu from Backend
try:
    params = {
        "user_type": user_type,
        "search": search_query,
        "customer_id": user_id if allergy_mode else None
    }
    
    # NEW LOGIC: Hit the Router Endpoint
    response = requests.get(API_URLS['menu'], params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # Handle both list (standard DRF) and dict (custom response) formats
        dishes = data.get('dishes', []) if isinstance(data, dict) else data
        message = data.get('message', '') if isinstance(data, dict) else ''
        
        if message:
            st.info(message)
            
        if not dishes:
            st.warning("No dishes found matching your criteria.")
            
        # Display Dishes Grid
        for dish in dishes:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                c1.title("🍲") # Placeholder icon
                
                with c2:
                    st.subheader(dish['name'])
                    st.write(dish.get('description', ''))
                    
                    # VIP Badge
                    if dish.get('special_for_vip'):
                        st.caption("✨ **VIP Exclusive**")
                        
                    # Chef Info
                    chef_name = dish.get('chef_name', 'Unknown Chef')
                    st.caption(f"👨‍🍳 Chef: {chef_name}")
                
                with c3:
                    st.write(f"**${dish['price']}**")
                    if st.button("Add +", key=f"add_{dish['dish_id']}"):
                        if not user_id or user_id == "Paste-UUID-Here":
                            st.error("Please enter a Customer ID in the sidebar first.")
                        else:
                            # NEW LOGIC: Add to Cart (POST to Cart Endpoint)
                            try:
                                res = requests.post(API_URLS['cart'], json={
                                    "customer_id": user_id,
                                    "dish_id": dish['dish_id']
                                })
                                if res.status_code == 200 or res.status_code == 201:
                                    st.toast(f"Added {dish['name']} to cart!")
                                else:
                                    st.error(f"Failed: {res.json().get('error', res.text)}")
                            except Exception as e:
                                st.error("Connection Error")

    else:
        st.error(f"Failed to load menu. Status: {response.status_code}")

except Exception as e:
    st.error(f"Could not connect to Kitchen (Backend). Is Django running? {e}")