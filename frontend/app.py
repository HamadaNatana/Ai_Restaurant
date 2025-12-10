import streamlit as st
import os
import django
import sys

# 1. SETUP DJANGO (Crucial: This connects Streamlit to your Database)
# Add project root to system path so we can import 'restaurant'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings')
django.setup()

# 2. PAGE CONFIG
st.set_page_config(
    page_title="AI Restaurant System",
    page_icon="🍽️",
    layout="wide"
)

# 3. WELCOME SCREEN
st.title("🍽️ AI-Enabled Restaurant System")
st.image("https://cdn.dribbble.com/users/1012566/screenshots/4187820/media/985748436085f06bb2bd63686ff491a5.jpg", use_column_width=True)

st.markdown("""
### Welcome to the Future of Dining
Select a module from the **sidebar** to begin:

* **🍔 Menu & Order**: Browse dishes, filter by allergy, and checkout (VIP discounts applied!).
* **🤖 AI Assistant**: Chat with our smart bot about hours, vegan options, or policies.
* **👔 Manager Portal**: Manage staff, resolve disputes, and oversee the kitchen.
* **🚚 Driver Portal**: Bid on delivery jobs and track orders.
""")

# 4. SESSION STATE INIT (Global Variables)
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Guest'