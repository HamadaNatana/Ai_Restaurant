"""
Order Views - UC07: Placing Orders API Endpoints
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import OrderService


# --- Cart Operations ---

@api_view(['POST'])
def add_to_cart(request):
    """UC07: Add item to cart (Phase 1)."""
    customer_id = request.data.get('customer_id')
    dish_id = request.data.get('dish_id')
    
    if not customer_id or not dish_id:
        return Response({'error': 'customer_id and dish_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        
    success, message = OrderService.add_to_cart(customer_id, dish_id)
    
    if success:
        return Response({'message': message}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_cart(request):
    """UC07: Get cart content with totals (Phase 2)."""
    customer_id = request.query_params.get('customer_id')
    
    if not customer_id:
        return Response({'error': 'customer_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    success, message, cart_data = OrderService.validate_and_format_cart(customer_id)
    
    if success:
        return Response(cart_data, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def update_cart_item(request):
    """UC07: Update cart item quantity."""
    customer_id = request.data.get('customer_id')
    item_id = request.data.get('item_id')
    quantity = request.data.get('quantity')
    
    if not customer_id or not item_id or quantity is None:
        return Response({'error': 'customer_id, item_id, and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        quantity = int(quantity)
    except ValueError:
        return Response({'error': 'quantity must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        
    success, message = OrderService.update_cart_item(customer_id, item_id, quantity)
    
    if success:
        return Response({'message': message}, status=status.HTTP_200_OK)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_cart_item(request, item_id):
    """UC07: Remove item from cart."""
    customer_id = request.query_params.get('customer_id') or request.data.get('customer_id')
    
    if not customer_id:
        return Response({'error': 'customer_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    success, message = OrderService.remove_cart_item(customer_id, item_id)
    
    if success:
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

# --- Checkout ---

@api_view(['POST'])
def checkout(request):
    """UC07: Process order and finalize payment (Phase 4)."""
    customer_id = request.data.get('customer_id')
    
    if not customer_id:
        return Response({'error': 'customer_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    success, message, result = OrderService.checkout(customer_id)
    
    if success:
        return Response(result, status=status.HTTP_200_OK)
    else:
        # Front-end looks for 'error' message, containing the reason including insufficient balance
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

# --- Order History (Simple Placeholders) ---

@api_view(['GET'])
def get_order(request, order_id):
    """Get specific order details."""
    return Response({'message': 'Endpoint not yet implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)

@api_view(['GET'])
def get_customer_orders(request):
    """Get customer's order history."""
    return Response({'message': 'Endpoint not yet implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)
