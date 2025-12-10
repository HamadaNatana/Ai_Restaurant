"""
Order Services - UC07: Cart & Checkout Business Logic
Implements logic from UC07 pseudocode (Phase 1-5).
"""

from typing import Tuple, Optional, Dict
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model

from menu.models import Dish 
from orders.models import Order, OrderItem, Customer # Use Customer from orders.models for placeholders

# Get User model for type checking
User = get_user_model()


class OrderService:
    # Business Rules from UC04/UC05/settings
    VIP_DISCOUNT_RATE = 0.05
    STANDARD_DELIVERY_FEE = 5.00
    FREE_DELIVERY_THRESHOLD = 3 

    @classmethod
    def get_or_create_pending_order(cls, customer_id) -> Tuple[bool, str, Optional[Order]]:
        """Retrieves or creates the user's active shopping cart (pending order)."""
        try:
            customer = Customer.objects.get(customer_id=customer_id) 
        except Customer.DoesNotExist:
            return (False, "Customer not found.", None)

        order, created = Order.objects.get_or_create(
            customer_id=customer,
            status=Order.STATUS_PENDING,
            defaults={'subtotal': 0, 'total': 0, 'discount_amount': 0}
        )
        return (True, "Cart retrieved" if not created else "New cart created", order)


    @classmethod
    def add_to_cart(cls, customer_id: str, dish_id: str) -> Tuple[bool, str]:
        """UC07: Add dish to cart (Phase 1 logic)."""
        
        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except Dish.DoesNotExist:
            return (False, "Dish not found or unavailable.")
        
        if not dish.is_active:
             return (False, f"{dish.name} is currently unavailable.")
        
        success, msg, order = cls.get_or_create_pending_order(customer_id)
        if not success:
            return (False, msg)

        try:
            cart_item = OrderItem.objects.get(order_id=order, dish_id=dish)
            cart_item.quantity = F('quantity') + 1
            cart_item.save()
            return (True, f"{dish.name} quantity increased in cart.")
        except OrderItem.DoesNotExist:
            OrderItem.objects.create(
                order_id=order,
                dish_id=dish,
                quantity=1,
                unit_price=dish.price
            )
            return (True, f"{dish.name} added to cart.")
        except Exception as e:
            return (False, f"Failed to add to cart: {str(e)}")


    @classmethod
    def validate_and_format_cart(cls, customer_id: str) -> Tuple[bool, str, Dict]:
        """UC07: Validates cart, removes unavailable dishes (Exception 2), and calculates totals."""
        success, msg, order = cls.get_or_create_pending_order(customer_id)
        if not success: return (False, msg, {})
        
        items = list(order.items.all().select_related('dish_id', 'dish_id__chef_id', 'customer_id'))
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            is_vip = customer.get_user_type().lower() == 'vip'
        except Customer.DoesNotExist:
            return (False, "Customer not found.", {})

        unavailable_items_removed = []
        with transaction.atomic():
            for item in items:
                dish = item.dish_id
                is_available = dish.is_active and dish.chef_id.is_active
                
                if dish.special_for_vip and not is_vip:
                    is_available = False
                
                if not is_available:
                    unavailable_items_removed.append(dish.name)
                    item.delete() 
            
            items = list(order.items.all().select_related('dish_id')) 
        
        if not items:
            return (True, "Your cart is empty!", {'items': []})

        # --- Phase 3: Calculate Totals ---
        subtotal = sum(float(item.unit_price) * item.quantity for item in items)
        discount_amount = 0.0
        vip_discount_applied = False
        free_delivery_applied = False
        delivery_fee = cls.STANDARD_DELIVERY_FEE
        
        if is_vip:
            discount_amount = round(subtotal * cls.VIP_DISCOUNT_RATE, 2)
            vip_discount_applied = True
            
            if (customer.order_count + 1) % cls.FREE_DELIVERY_THRESHOLD == 0:
                delivery_fee = 0.0
                free_delivery_applied = True
            
        total = subtotal - discount_amount + delivery_fee
        
        # Update Order totals in DB 
        order.subtotal = subtotal
        order.discount_amount = discount_amount
        order.total = total
        order.vip_discount_applied = vip_discount_applied
        order.free_delivery_applied = free_delivery_applied
        order.save()

        # Prepare response data
        formatted_items = [{
            'item_id': str(item.order_item_id),
            'dish_name': item.dish_id.name,
            'price': round(float(item.unit_price), 2),
            'quantity': item.quantity,
            'subtotal': round(float(item.unit_price) * item.quantity, 2)
        } for item in items]
        
        response_data = {
            'items': formatted_items,
            'subtotal': round(subtotal, 2),
            'discount': round(discount_amount, 2),
            'delivery_fee': round(delivery_fee, 2),
            'total': round(total, 2),
            'vip_discount_applied': vip_discount_applied,
            'free_delivery_applied': free_delivery_applied,
        }
        
        if unavailable_items_removed:
            names = ', '.join(unavailable_items_removed)
            response_data['message'] = f"Some items were removed from your cart: {names}"

        return (True, "Cart loaded successfully", response_data)


    @classmethod
    def checkout(cls, customer_id: str) -> Tuple[bool, str, Dict]:
        """UC07: Phase 4 logic - Final order processing, balance check, and creation."""
        success, msg, cart_data = cls.validate_and_format_cart(customer_id)
        if not success or not cart_data.get('items'):
            return (False, "Cannot checkout: Cart is empty or validation failed.", {})
        
        final_total = cart_data['total']
        
        try:
            with transaction.atomic():
                customer = Customer.objects.get(customer_id=customer_id)

                # 2. Check Insufficient Balance (Exception 3)
                if float(customer.balance) < final_total:
                    cls._handle_insufficient_balance(customer, final_total)
                    return (False, "Order failed - Insufficient balance. Please add funds.", {})

                # 3. Finalize Order (Phase 4, Step 14)
                order = Order.objects.get(customer_id=customer, status=Order.STATUS_PENDING)
                order.status = Order.STATUS_PAID 
                order.save()
                
                # 4. Reduce Customer Balance (Phase 4, Step 15)
                customer.balance = F('balance') - final_total
                
                # 5. Update VIP order count (Phase 4, Step 16)
                if customer.get_user_type().lower() == 'vip':
                    customer.order_count = F('order_count') + 1
                
                customer.save()
                
                # 7. Clear Cart by creating a new pending order (Phase 5, Step 20)
                Order.objects.create(customer_id=customer, status=Order.STATUS_PENDING)

                return (True, "Order placed successfully!", {'order_id': str(order.order_id)})
            
        except Customer.DoesNotExist:
            return (False, "Customer not found.", {})
        except Exception as e:
            return (False, f"An unexpected error occurred during checkout: {str(e)}", {})


    @staticmethod
    def _handle_insufficient_balance(customer: Customer, required_amount: float):
        """UC07: Exception 3 - Issues warning and triggers deregistration check."""
        customer.warnings = F('warnings') + 1
        customer.save()
        customer.refresh_from_db() 
        
        if customer.warnings >= 3:
            pass # KickCustomer logic (UC10) triggered here 
        
        pass 


    @classmethod
    def update_cart_item(cls, customer_id: str, item_id: str, quantity: int) -> Tuple[bool, str]:
        """UC07: Update quantity of an item in the cart."""
        try:
            order_item = OrderItem.objects.get(
                order_item_id=item_id, 
                order_id__customer_id=customer_id, 
                order_id__status=Order.STATUS_PENDING
            )
        except OrderItem.DoesNotExist:
            return (False, "Cart item not found in your pending order.")
        
        if quantity <= 0:
            return (False, "Quantity must be greater than 0.")
            
        order_item.quantity = quantity
        order_item.save()
        
        return (True, "Cart item quantity updated.")

    @classmethod
    def remove_cart_item(cls, customer_id: str, item_id: str) -> Tuple[bool, str]:
        """UC07: Remove item from cart."""
        try:
            order_item = OrderItem.objects.get(
                order_item_id=item_id, 
                order_id__customer_id=customer_id, 
                order_id__status=Order.STATUS_PENDING
            )
            dish_name = order_item.dish_id.name
            order_item.delete()
            return (True, f"'{dish_name}' removed from cart.")
        except OrderItem.DoesNotExist:
            return (False, "Cart item not found in your pending order.")