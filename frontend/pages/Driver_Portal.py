import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"
st.title("🚚 Delivery Driver Hub")

tab1, tab2 = st.tabs(["Open Jobs (Bid)", "My Deliveries"])

with tab1:
    st.subheader("Available Orders")
    # In a real demo, you'd fetch "Ready" orders here
    # Placeholder for the presentation flow
    with st.expander("Order #992 - Downtown (Est. Tip: $5)"):
        bid_price = st.number_input("Your Bid ($)", min_value=3.0, value=5.0)
        if st.button("Submit Bid"):
            # You would call Sadeq's API here
            st.success(f"Bid of ${bid_price} submitted!")

with tab2:
    st.subheader("Current Assignments")
    st.info("No active deliveries.")
    