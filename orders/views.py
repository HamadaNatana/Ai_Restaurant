from rest_framework import viewsets, status, permissions, decorators
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
from .services import OrderService

class OrderViewSet(viewsets.ModelViewSet):
    """
    Unified Endpoint for Order Operations.
    Matches the 'David Format' (ViewSet + Router) and your specific Schema.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny] # Prevents 500 Permission Errors

    # --- STANDARD CRUD ---
    def get_queryset(self):
        """Allow filtering orders by customer_id for order history"""
        queryset = super().get_queryset()
        customer_id_param = self.request.query_params.get('customer_id')
        
        if customer_id_param:
            # FIX: Using 'customer_id__pk' because your model field is named 'customer_id'
            queryset = queryset.filter(customer_id__pk=customer_id_param)
        return queryset

    # --- CART ACTIONS ---

    @decorators.action(detail=False, methods=['get'])
    def cart(self, request):
        """Get the current pending cart for a customer."""
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calls your OrderService.validate_and_format_cart
        success, msg, data = OrderService.validate_and_format_cart(customer_id)
        if success:
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)

    @decorators.action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add an item to the cart."""
        customer_id = request.data.get('customer_id')
        dish_id = request.data.get('dish_id')
        
        if not customer_id or not dish_id:
            return Response({'error': 'Missing customer_id or dish_id'}, status=status.HTTP_400)