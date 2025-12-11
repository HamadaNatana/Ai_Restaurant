import streamlit as st
import requests
import ollama
from utils.auth_helper import require_role
from utils.sidebar import generate_sidebar

# 1. SETUP
st.set_page_config(page_title="Menu & Order", page_icon="🍔", layout="wide")
generate_sidebar()
require_role(["VISITOR", "CUSTOMER", "VIP", "CHEF"])

# 2. CONFIGURATION
BASE_URL = "http://127.0.0.1:8000"
API_URLS = {
    "menu": f"{BASE_URL}/menu/dishes/", 
    "cart": f"{BASE_URL}/orders/cart/",
    # POINT TO 'cart/' (The endpoint that handles POST)
    "add_item": f"{BASE_URL}/orders/cart/",  
    "checkout": f"{BASE_URL}/orders/checkout/"
}

# ---------------------------------------------------------
# AI WAITER (Local)
# ---------------------------------------------------------
def ask_local_ai(question):
    try:
        system_instruction = "You are a helpful waiter. Keep answers brief."
        response = ollama.chat(model='mistral', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': question},
        ])
        return response['message']['content']
    except Exception as e:
        return f"⚠️ AI Offline: {e}"

# ---------------------------------------------------------
# HELPER: FETCH CART
# ---------------------------------------------------------
def fetch_cart(user_identifier):
    try:
        res = requests.get(API_URLS['cart'], params={"customer_id": user_identifier})
        if res.status_code == 200:
            data = res.json()
            st.session_state.cart_items = data.get('items', [])
            st.session_state.cart_total = data.get('total', 0)
        else:
            st.session_state.cart_items = []
            st.session_state.cart_total = 0
    except Exception:
        st.session_state.cart_items = []

# 3. SIDEBAR
with st.sidebar:
    st.header("👤 Ordering As")
    if st.session_state.get("logged_in"):
        active_user = st.session_state["username"]
        role = st.session_state.get("role", "CUSTOMER")
        st.success(f"✅ **{active_user}** ({role})")
        user_identifier = active_user
    else:
        st.warning("Guest Mode")
        user_identifier = st.text_input("Enter Guest ID", value="Guest")
        role = "Visitor"

    st.divider()
    
    # AI CHAT
    with st.expander("🤖 Ask AI Waiter", expanded=True):
        if "menu_chat_history" not in st.session_state: st.session_state.menu_chat_history = []
        for msg in st.session_state.menu_chat_history[-3:]:
            if msg["role"] == "user": st.markdown(f"**You:** {msg['content']}")
            else: st.info(f"**Waiter:** {msg['content']}")

        with st.form("chat_form"):
            q = st.text_input("Question:")
            if st.form_submit_button("Ask") and q:
                st.session_state.menu_chat_history.append({"role": "user", "content": q})
                with st.spinner("..."):
                    ans = ask_local_ai(q)
                st.session_state.menu_chat_history.append({"role": "assistant", "content": ans})
                st.rerun()
        if st.button("Clear Chat"):
            st.session_state.menu_chat_history = []
            st.rerun()

    st.divider()
    
    # CART
    st.subheader(f"🛒 Cart (${st.session_state.get('cart_total', 0)})")
    if "cart_items" not in st.session_state: fetch_cart(user_identifier)
    
    if st.session_state.get("cart_items"):
        for item in st.session_state.cart_items:
            d_name = item.get('dish_name') or item.get('name') or "Item"
            st.write(f"• {d_name} x{item.get('quantity', 1)}")
        
        if st.button("💳 Checkout", type="primary", use_container_width=True):
            try:
                res = requests.post(API_URLS['checkout'], json={"customer_id": user_identifier})
                if res.status_code == 200:
                    st.balloons()
                    st.success("Order Placed!")
                    st.session_state.cart_items = [] 
                    st.session_state.cart_total = 0
                    st.rerun()
                else:
                    st.error(f"Checkout Failed: {res.text}")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.caption("Empty")
        if st.button("Refresh"): fetch_cart(user_identifier)

# 4. MAIN MENU
st.title("🍔 AI Restaurant Menu")
with st.container(border=True):
    c1, c2 = st.columns([3, 1])
    search_query = c1.text_input("🔍 Search Menu")
    allergy_mode = c2.toggle("🛡️ Safety Mode")

try:
    current_role = st.session_state.get("role", "Visitor")
    params = {
        "search": search_query,
        "customer_id": user_identifier if allergy_mode else None,
        "user_type": current_role 
    }
    
    response = requests.get(API_URLS['menu'], params=params)
    
    if response.status_code == 200:
        data = response.json()
        dishes = data.get('dishes', []) if isinstance(data, dict) else data
        
        if not dishes:
            st.info("No dishes found.")
        else:
            cols = st.columns(3)
            for index, dish in enumerate(dishes):
                with cols[index % 3]: 
                    with st.container(border=True):
                        # Safe Price
                        try: price_val = float(dish.get('price', 0))
                        except: price_val = 0.0

                        # Image
                        if str(dish.get('picture', '')).startswith('http'):
                             st.image(dish['picture'], use_column_width=True)
                        else:
                             st.markdown(f"<div style='text-align: center; font-size: 50px;'>🍲</div>", unsafe_allow_html=True)
                        
                        st.subheader(dish.get('name', 'Unnamed'))
                        st.write(f"**${price_val:.2f}**")
                        st.caption(dish.get('description', ''))
                        
                        # --- ADD ITEM LOGIC ---
                        if st.button("Add +", key=f"add_{index}", use_container_width=True):
                            # ROBUST ID FINDER: Try 'id', then 'pk', then 'dish_id'
                            real_dish_id = dish.get('id') or dish.get('pk') or dish.get('dish_id')
                            
                            payload = {
                                "customer_id": user_identifier,
                                "dish_id": real_dish_id 
                            }
                            
                            st.write(f"Debug: Sending {payload}") # <--- Temporary Debug
                            
                            try:
                                res = requests.post(API_URLS['add_item'], json=payload)
                                if res.status_code in [200, 201]:
                                    st.toast(f"Added!", icon="✅")
                                    fetch_cart(user_identifier)
                                    st.rerun()
                                else:
                                    # SHOW THE EXACT SERVER ERROR
                                    st.error(f"Server Error (400): {res.json()}") 
                            except Exception as e:
                                st.error(f"Conn Error: {e}")

    else:
        st.error(f"Kitchen Offline: {response.status_code}")

except Exception as e:
    st.error(f"App Error: {e}")