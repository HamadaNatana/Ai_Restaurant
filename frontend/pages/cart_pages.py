"""
Cart Page - UC07: Placing Orders
Handles cart review, updates, and final checkout.
"""

import streamlit as st
from utils.api_client import APIClient
from utils.session import get_customer_id, can_order, refresh_user_data, is_vip

def render_cart_page():
    st.markdown("## Your Shopping Cart")
    
    if not st.session_state.logged_in:
        st.warning("Please log in to view your cart.")
        return
    
    if not can_order():
        st.error("Your account cannot place orders.")
        return
    
    api = APIClient()
    customer_id = get_customer_id()
    
    if not customer_id:
        st.error("Customer ID not found. Please log in again.")
        return

    # --- Fetch Cart (UC07 Phase 2) ---
    success, cart_data = api.get_cart(customer_id)
    
    if not success:
        error_msg = cart_data if isinstance(cart_data, str) else "Failed to load cart"
        st.error(f"Error: {error_msg}")
        return

    items = cart_data.get('items', [])
    
    if not items:
        st.info("Your cart is empty!")
        col1, _ = st.columns(2)
        with col1:
            if st.button("Browse Menu", use_container_width=True, key="browse_empty"):
                st.session_state.current_page = "Menu"
                st.rerun()
        return

    # Display message if items were removed (Cart Validation/Exception 2)
    message = cart_data.get('message', "")
    if message and 'removed' in message.lower():
        st.warning(f"Warning: {message}")

    # --- Display Cart Items ---
    st.markdown("### Items in Cart")
    
    # Header Row
    st.columns([3, 1, 1, 1, 1])[0].markdown("**Item**") 
    
    for item in items:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        item_id = str(item.get('item_id'))
        dish_name = item.get('dish_name', 'Unknown')
        price = float(item.get('price', 0))
        quantity = item.get('quantity', 1)
        subtotal = float(item.get('subtotal', price * quantity))
        
        with col1:
            st.write(f"**{dish_name}**")
        with col2:
            st.write(f"${price:.2f}")
        with col3:
            # Quantity Input
            new_qty = st.number_input(
                "Qty",
                min_value=1,
                max_value=99,
                value=quantity,
                key=f"qty_{item_id}",
                label_visibility="collapsed"
            )
            # Update quantity logic
            if new_qty != quantity:
                # Need customer_id for updating cart item
                success_update, _ = api.update_cart_item(item_id, new_qty, customer_id) 
                if success_update:
                    st.rerun()

        with col4:
            # Remove Button
            if st.button("Remove", key=f"rm_{item_id}", help="Remove item"):
                success_remove, _ = api.remove_cart_item(item_id, customer_id)
                if success_remove:
                    st.rerun()

        with col5:
            st.write(f"**${subtotal:.2f}**")
        
        st.markdown("---")

    # --- Order Summary ---
    st.markdown("### Order Summary")
    subtotal_display = cart_data.get('subtotal', 0)
    discount = cart_data.get('discount', 0)
    delivery_fee = cart_data.get('delivery_fee', 0)
    total = cart_data.get('total', 0)
    vip_discount_applied = cart_data.get('vip_discount_applied', False)
    free_delivery_applied = cart_data.get('free_delivery_applied', False)

    col_name, col_value = st.columns([2, 1])
    
    col_name.write("Subtotal:")
    col_value.write(f"${subtotal_display:.2f}")
    
    if vip_discount_applied:
        col_name.write("VIP Discount (5%):")
        col_value.write(f"-${discount:.2f}")
    elif discount > 0: # For non-VIP, manual/coupon discounts (if applicable)
        col_name.write("Discount:")
        col_value.write(f"-${discount:.2f}")

    col_name.write("Delivery Fee:")
    if free_delivery_applied:
        col_value.write(f"~~${5.00:.2f}~~ **FREE**")
    else:
        col_value.write(f"${delivery_fee:.2f}")
    
    st.markdown("---")
    col_name.markdown("**Total:**")
    col_value.markdown(f"**${total:.2f}**")
    
    if is_vip():
        st.info("VIP Benefits Applied: 5% discount and/or free delivery.")
    
    st.markdown("---")

    # --- Checkout Button (UC07 Phase 3/4) ---
    if st.button("Proceed to Checkout", type="primary", use_container_width=True):
        with st.spinner("Processing your order..."):
            success_checkout, result = api.checkout(customer_id)
            
            if success_checkout:
                st.success("Order placed successfully!")
                order_id = result.get('order_id', 'N/A')
                st.info(f"Order ID: {order_id}")
                
                # Refresh user data, especially balance and order count
                refresh_user_data() 
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View My Orders", use_container_width=True, key="view_orders"):
                        st.session_state.current_page = "My Orders"
                        st.rerun()
                with col2:
                    if st.button("Continue Shopping", use_container_width=True, key="continue_shop"):
                        st.session_state.current_page = "Menu"
                        st.rerun()
            else:
                error_msg = result if isinstance(result, str) else result.get('error', 'Checkout failed')
                st.error(f"Checkout Failed: {error_msg}")
                
                # Check for insufficient balance warning (UC07 Exception 3)
                if 'Insufficient balance' in error_msg:
                    st.warning("Please add funds to your account to avoid further warnings.")
