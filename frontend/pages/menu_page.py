"""
Menu Page - UC06: Menu Access, UC07: Add to Cart, UC22: Allergy Filtering
"""

import streamlit as st
from utils.api_client import APIClient
from utils.session import get_user_type_for_menu, get_customer_id, can_order, get_user_allergies

def render_menu_page():
    st.markdown("## Browse Our Menu")
    api = APIClient()
    customer_id = get_customer_id()
    user_type = get_user_type_for_menu()

    # --- Filters ---
    col1, col2 = st.columns([3, 1])
    with col1:
        # State management for search query
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
            
        search_query = st.text_input(
            "Search dishes",
            value=st.session_state.search_query,
            placeholder="e.g. pasta, spicy..."
        )
        st.session_state.search_query = search_query
        
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    # --- User Information ---
    if st.session_state.logged_in:
        user_allergies = get_user_allergies()
        if user_allergies:
            st.info(f"Filtering out dishes with: **{', '.join(user_allergies)}**")
        
        if user_type == 'VIP':
            st.success("VIP Access - You can see all dishes including VIP specials.")
        elif user_type == 'Customer':
            st.caption("Logged in as Registered Customer.")

    # --- Fetch Menu (UC06) ---
    params = {
        'customer_id': customer_id,
        'user_type': user_type,
        'search': search_query or None,
    }
    
    success, response = api.get_menu(**params)

    if not success:
        st.error(f"Failed to load menu: {response}")
        return

    dishes = response.get('dishes', [])
    
    if not dishes:
        st.info("No dishes found matching your filters.")
        return

    st.success(f"Found {len(dishes)} delicious dishes!")

    # --- Display Dishes ---
    for dish in dishes:
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            # Column 1: Picture
            with col1:
                picture = dish.get('picture')
                if picture:
                    try:
                        st.image(picture, use_column_width=True)
                    except:
                        st.image("https://via.placeholder.com/150", use_column_width=True, caption="Image failed to load")
                else:
                    st.image("https://via.placeholder.com/150", use_column_width=True, caption="No image available")

            # Column 2: Details
            with col2:
                name = dish.get('name', 'Unknown Dish')
                st.markdown(f"### {name}")
                
                # Price
                price = dish.get('price', 0)
                st.markdown(f"**${float(price):.2f}**")
                
                # VIP Status
                if dish.get('special_for_vip'):
                    st.caption("**VIP Special**")
                
                # Chef name
                chef_name = dish.get('chef_name', 'House Chef')
                st.caption(f"Chef: {chef_name}")
                
                # Description
                description = dish.get('description', "")
                if description:
                    st.write(description)
                
                # Ingredients
                ingredients = dish.get('ingredients_list', [])
                if ingredients:
                    display_ingredients = ingredients[:5]
                    suffix = '...' if len(ingredients) > 5 else ""
                    st.caption(f"Ingredients: {', '.join(display_ingredients)}{suffix}")
                
                # Allergens warning (UC22)
                allergens = dish.get('allergens_list', [])
                if allergens:
                    st.warning(f"Contains Allergens: **{', '.join(allergens)}**")
                
                # Add to Cart button (UC07)
                if can_order():
                    dish_id = str(dish.get('dish_id'))
                    if st.button("Add to Cart", key=f"add_{dish_id}", type="primary"):
                        if not customer_id:
                            st.warning("Please log in to order.")
                        else:
                            success, result = api.add_to_cart(customer_id, dish_id)
                            if success:
                                st.success(f"'{name}' added to cart successfully!")
                            else:
                                error_msg = result if isinstance(result, str) else result.get('error', 'Failed to add')
                                st.error(error_msg)
                elif not st.session_state.logged_in:
                    st.caption("Login to add to cart.")
        
        st.markdown("---")
