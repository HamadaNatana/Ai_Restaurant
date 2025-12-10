"""
Chef Dishes Page - UC19: CRUD Dishes
Handles dish creation, editing, deletion, and availability toggling.
"""

import streamlit as st
from utils.api_client import APIClient
from utils.session import get_chef_id, is_chef

# --- Form Renderer ---
def render_dish_form(api: APIClient, chef_id: str):
    """Render the add/edit dish form"""
    editing = st.session_state.editing_dish_id is not None
    title = "Edit Dish" if editing else "Add New Dish"
    st.markdown(f"### {title}")
    
    # Retrieve current values from session state for pre-filling/persistence
    dish_name_val = st.session_state.get('dish_name', "")
    dish_price_val = st.session_state.get('dish_price', 10.0)
    dish_description_val = st.session_state.get('dish_description', "")
    dish_picture_val = st.session_state.get('dish_picture', "")
    dish_ingredients_val = st.session_state.get('dish_ingredients', "")
    dish_vip_only_val = st.session_state.get('dish_vip_only', False)

    with st.form("dish_form"):
        # Inputs
        name = st.text_input("Dish Name *", value=dish_name_val, placeholder="e.g., Grilled Salmon")
        price = st.number_input("Price ($) *", min_value=0.01, max_value=1000.0, value=dish_price_val, step=0.50)
        description = st.text_area("Description *", value=dish_description_val, placeholder="Describe your dish...")
        picture = st.text_input("Picture URL", value=dish_picture_val, placeholder="https://example.com/image.jpg")
        ingredients = st.text_input("Ingredients (comma-separated)", value=dish_ingredients_val, placeholder="salmon, lemon, butter, herbs")
        vip_only = st.checkbox("VIP Only (special dish for VIP customers)", value=dish_vip_only_val)
        
        # Form buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save Dish", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if submitted:
            # Save current values to session state immediately upon submission attempt
            st.session_state.dish_name = name
            st.session_state.dish_price = price
            st.session_state.dish_description = description
            st.session_state.dish_picture = picture
            st.session_state.dish_ingredients = ingredients
            st.session_state.dish_vip_only = vip_only

            # Validate
            if not name or not name.strip():
                st.error("Dish name is required.")
            elif not description or not description.strip():
                st.error("Description is required.")
            elif price <= 0:
                st.error("Price must be greater than $0.")
            else:
                # Prepare data
                dish_data = {
                    'name': name.strip(),
                    'price': price,
                    'description': description.strip(),
                    'picture': picture.strip() if picture else "",
                    'ingredients': ingredients.strip() if ingredients else "",
                    'special_for_vip': vip_only,
                }
                
                if editing:
                    # Update existing dish (UC19)
                    success, result, dish_obj = api.update_dish(st.session_state.editing_dish_id, chef_id, dish_data)
                else:
                    # Create new dish (UC19)
                    success, result, dish_obj = api.add_dish(chef_id, dish_data)
                
                if success:
                    st.success("Dish saved successfully!")
                    st.session_state.show_dish_form = False
                    st.session_state.editing_dish_id = None
                    st.rerun()
                else:
                    error_msg = result if isinstance(result, str) else result.get('error', 'Failed to save')
                    st.error(f"Error: {error_msg}")

        if cancelled:
            st.session_state.show_dish_form = False
            st.session_state.editing_dish_id = None
            st.rerun()

# --- Main Page Renderer ---
def render_chef_dishes_page():
    st.markdown("## My Dishes Management")
    
    # Check authorization
    if not st.session_state.logged_in:
        st.error("Please log in to access this page.")
        return
    if not is_chef():
        st.error("Access denied. This page is for chefs only.")
        return
    
    api = APIClient()
    chef_id = get_chef_id()
    
    if not chef_id:
        st.error("Chef ID not found. Please log in again.")
        return

    # Initialize session state for form control
    if 'show_dish_form' not in st.session_state: st.session_state.show_dish_form = False
    if 'editing_dish_id' not in st.session_state: st.session_state.editing_dish_id = None

    # Add New Dish button
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("➕ Add New Dish", type="primary", use_container_width=True):
            st.session_state.show_dish_form = True
            st.session_state.editing_dish_id = None
            # Clear form fields in session state
            st.session_state.dish_name = ""
            st.session_state.dish_price = 10.0
            st.session_state.dish_description = ""
            st.session_state.dish_picture = ""
            st.session_state.dish_ingredients = ""
            st.session_state.dish_vip_only = False
            st.rerun()

    # Show form if active
    if st.session_state.show_dish_form:
        render_dish_form(api, chef_id)
        st.markdown("---")

    # --- Fetch chef's dishes (UC19) ---
    success, dishes_data = api.get_chef_dishes(chef_id)
    
    if not success:
        error_msg = dishes_data if isinstance(dishes_data, str) else "Failed to load dishes"
        st.error(f"Error: {error_msg}")
        return

    if not dishes_data:
        st.info("You haven't created any dishes yet. Click 'Add New Dish' to get started!")
        return

    st.markdown(f"### Your Dishes ({len(dishes_data)})")

    # --- Display Dishes for Management ---
    for dish in dishes_data:
        dish_id = str(dish.get('dish_id'))
        name = dish.get('name', 'Unknown')
        price = float(dish.get('price', 0))
        is_vip = dish.get('special_for_vip', False)
        is_active = dish.get('is_active', True)
        
        # Determine expander label based on status
        status_label = " (Unavailable)" if not is_active else (" (VIP Only)" if is_vip else "")
        expander_label = f"{name} - ${price:.2f}{status_label}"
        
        with st.expander(expander_label):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                picture = dish.get('picture')
                if picture:
                    try:
                        st.image(picture, width=150)
                    except:
                        st.image("https://via.placeholder.com/150", width=150, caption="Image failed to load")
                else:
                    st.image("https://via.placeholder.com/150", width=150, caption="No image available")
            
            with col2:
                # Description
                description = dish.get('description', 'No description')
                st.write(description)
                
                # Ingredients & Allergens
                ingredients_list = dish.get('ingredients_list', [])
                allergens_list = dish.get('allergens_list', [])
                
                if ingredients_list:
                    st.caption(f"Ingredients: {', '.join(ingredients_list)}")
                if allergens_list:
                    st.warning(f"Allergens: {', '.join(allergens_list)}")
                
                # Status
                if not is_active:
                    st.error("STATUS: UNAVAILABLE")
                elif is_vip:
                    st.success("STATUS: VIP Only")
                else:
                    st.caption("STATUS: Available to all customers")
            
            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Edit Button
                if st.button("✏️ Edit", key=f"edit_{dish_id}", use_container_width=True):
                    st.session_state.show_dish_form = True
                    st.session_state.editing_dish_id = dish_id
                    
                    # Pre-fill form fields
                    st.session_state.dish_name = name
                    st.session_state.dish_price = price
                    st.session_state.dish_description = dish.get('description', "")
                    st.session_state.dish_picture = dish.get('picture', "") or ""
                    st.session_state.dish_ingredients = ', '.join(ingredients_list)
                    st.session_state.dish_vip_only = is_vip
                    st.rerun()
            
            with col2:
                # Toggle Availability Button
                toggle_label = "Make Available" if not is_active else "Set Unavailable"
                if st.button(f"🔄 {toggle_label}", key=f"tog_{dish_id}", use_container_width=True):
                    success_toggle, result = api.toggle_dish_availability(dish_id, chef_id)
                    if success_toggle:
                        st.success(result.get('message', 'Status updated!'))
                        st.rerun()
                    else:
                        error_msg = result if isinstance(result, str) else result.get('error', 'Failed')
                        st.error(error_msg)
            
            with col3:
                # Delete Button
                if st.button("🗑️ Delete", key=f"del_{dish_id}", use_container_width=True):
                    success_delete, result = api.delete_dish(dish_id, chef_id)
                    if success_delete:
                        st.success(result.get('message', 'Dish deleted!'))
                        st.rerun()
                    else:
                        error_msg = result if isinstance(result, str) else result.get('error', 'Failed')
                        st.error(error_msg)
