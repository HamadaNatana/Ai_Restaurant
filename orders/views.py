from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import OrderService
from .serializers import OrderSerializer

class CartAPIView(APIView):
    """
    Handles General Cart Operations (Get Cart, Add Item)
    """
    def get(self, request):
        # UC07: Get Cart content
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        success, msg, data = OrderService.validate_and_format_cart(customer_id)
        if success:
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        # UC07: Add Item to Cart
        customer_id = request.data.get('customer_id')
        dish_id = request.data.get('dish_id')
        
        if not customer_id or not dish_id:
            return Response({'error': 'Missing customer_id or dish_id'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = OrderService.add_to_cart(customer_id, dish_id)
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

class CartItemAPIView(APIView):
    """
    Handles Operations on Specific Cart Items (Update, Remove)
    """
    def put(self, request):
        # UC07: Update Item Quantity
        customer_id = request.data.get('customer_id')
        item_id = request.data.get('item_id') # Note: This is the Dish ID in your service logic
        quantity = request.data.get('quantity')

        if not all([customer_id, item_id, quantity]):
            return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = OrderService.update_cart_item(customer_id, item_id, quantity)
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        # UC07: Remove Item
        customer_id = request.query_params.get('customer_id')
        item_id = request.query_params.get('item_id') # Dish ID

        if not customer_id or not item_id:
            return Response({'error': 'Missing IDs'}, status=status.HTTP_400_BAD_REQUEST)

        success, message = OrderService.remove_cart_item(customer_id, item_id)
        if success:
            return Response({'message': message}, status=status.HTTP_200_OK)
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

class CheckoutAPIView(APIView):
    """
    Handles Final Checkout
    """
    def post(self, request):
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg, result = OrderService.checkout(customer_id)
        
        if success:
            return Response(result, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)