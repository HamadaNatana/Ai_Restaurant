"""
API Client - Communicates with Django Backend
Handles all API requests for UC06, UC07, UC19
"""
import requests
import streamlit as st
from typing import Tuple, Optional, Dict, Any

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000/api")

class APIClient:
    """API Client for Django Backend Communication"""
    def __init__(self):
        self.base_url = API_BASE_URL

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Tuple[bool, Any]:
        """Make API request"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, timeout=10)
            elif method == 'DELETE':
                # DELETE requests may pass parameters via URL or query string
                response = requests.delete(url, params=params, timeout=10)
            else:
                return (False, "Invalid method")

            if response.status_code in [200, 201]:
                return (True, response.json())
            elif response.status_code == 204: # For successful DELETE with no content
                return (True, {})
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', error_data.get('detail', 'Request failed'))
                return (False, error_msg)
        except requests.exceptions.ConnectionError:
            return (False, "Cannot connect to server. Is the backend running?")
        except requests.exceptions.Timeout:
            return (False, "Request timed out")
        except Exception as e:
            return (False, str(e))

    # ============ Menu Endpoints (UC06) ============
    def get_menu(
        self,
        customer_id: Optional[str] = None,
        user_type: str = 'Visitor',
        search: Optional[str] = None,
        category: Optional[str] = None
    ) -> Tuple[bool, Any]:
        """UC06: Get filtered menu"""
        params = {'user_type': user_type}
        if customer_id:
            params['customer_id'] = customer_id
        if search:
            params['search'] = search
        if category:
            params['category'] = category
        # Endpoint: apps.menu.urls -> '' (views.get_menu)
        return self._request('GET', 'menu/', params=params)

    # ======== Cart Endpoints (UC07) ============
    def add_to_cart(self, customer_id: str, dish_id: str) -> Tuple[bool, Any]:
        """UC07: Add item to cart"""
        # Endpoint: apps.orders.urls -> 'cart/add/' (orders.views.add_to_cart)
        return self._request('POST', 'orders/cart/add/', data={
            'customer_id': customer_id,
            'dish_id': dish_id
        })

    def get_cart(self, customer_id: str) -> Tuple[bool, Any]:
        """UC07: Get cart with totals"""
        # Endpoint: apps.orders.urls -> 'cart/' (orders.views.get_cart)
        return self._request('GET', 'orders/cart/', params={
            'customer_id': customer_id
        })

    def update_cart_item(self, item_id: str, quantity: int, customer_id: str) -> Tuple[bool, Any]:
        """UC07: Update cart item quantity"""
        # Endpoint: apps.orders.urls -> 'cart/update/' (orders.views.update_cart_item)
        return self._request('POST', 'orders/cart/update/', data={
            'item_id': item_id,
            'quantity': quantity,
            'customer_id': customer_id
        })

    def remove_cart_item(self, item_id: str, customer_id: str) -> Tuple[bool, Any]:
        """UC07: Remove item from cart"""
        # Endpoint: apps.orders.urls -> 'cart/remove/<uuid:item_id>/' (orders.views.remove_cart_item)
        return self._request('DELETE', f'orders/cart/remove/{item_id}/', params={
             'customer_id': customer_id
        })

    def checkout(self, customer_id: str) -> Tuple[bool, Any]:
        """UC07: Process order"""
        # Endpoint: apps.orders.urls -> 'checkout/' (orders.views.checkout)
        return self._request('POST', 'orders/checkout/', data={
            'customer_id': customer_id
        })

    # ============ Dishes Endpoints (UC19) ============
    def get_chef_dishes(self, chef_id: str) -> Tuple[bool, Any]:
        """UC19: Get all dishes by chef"""
        # Endpoint: apps.menu.urls -> 'dishes/by-chef/' (menu.dish_views.get_chef_dishes)
        return self._request('GET', 'menu/dishes/by-chef/', params={
             'chef_id': chef_id
        })

    def add_dish(self, chef_id: str, dish_data: Dict) -> Tuple[bool, Any]:
        """UC19: Add new dish"""
        dish_data['chef_id'] = chef_id
        # Endpoint: apps.menu.urls -> 'dishes/' (menu.dish_views.create_dish)
        return self._request('POST', 'menu/dishes/', data=dish_data)

    def update_dish(self, dish_id: str, chef_id: str, dish_data: Dict) -> Tuple[bool, Any]:
        """UC19: Update dish"""
        dish_data['chef_id'] = chef_id
        # Endpoint: apps.menu.urls -> 'dishes/<uuid:dish_id>/' (menu.dish_views.update_dish)
        return self._request('PUT', f'menu/dishes/{dish_id}/', data=dish_data)

    def delete_dish(self, dish_id: str, chef_id: str) -> Tuple[bool, Any]:
        """UC19: Delete dish"""
        # Endpoint: apps.menu.urls -> 'dishes/<uuid:dish_id>/delete/' (menu.dish_views.delete_dish)
        return self._request('DELETE', f'menu/dishes/{dish_id}/delete/', params={
             'chef_id': chef_id
        })

    def toggle_dish_availability(self, dish_id: str, chef_id: str) -> Tuple[bool, Any]:
        """UC19: Toggle dish availability (is_active)"""
        # Endpoint: apps.menu.urls -> 'dishes/<uuid:dish_id>/toggle/' (menu.dish_views.toggle_dish_availability)
        return self._request('POST', f'menu/dishes/{dish_id}/toggle/', data={
             'chef_id': chef_id
        })
