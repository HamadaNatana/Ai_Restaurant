from rest_framework import viewsets, status, permissions, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
from .services import OrderService
from accounts.models import Customer  
from menu.models import Dish          

class OrderViewSet(viewsets.ModelViewSet):
    """
    Unified Endpoint for Order Operations.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny] 

    def get_queryset(self):
        """Allow filtering orders by customer_id"""
        queryset = super().get_queryset()
        customer_id_param = self.request.query_params.get('customer_id')
        if customer_id_param:
            queryset = queryset.filter(customer_id__user__username=customer_id_param) | \
                       queryset.filter(customer_id__pk=customer_id_param) 
            
        return queryset

    @decorators.action(detail=False, methods=['get', 'post'])
    def cart(self, request):
        """
        GET:  Retrieve the pending cart.
        POST: Add a dish to the pending cart.
        """

        c_id = request.query_params.get('customer_id') or request.data.get('customer_id')
        
        if not c_id:
            return Response({'error': 'customer_id is required'}, status=status.HTTP_400_BAD_REQUEST)


        try:
            
            customer = Customer.objects.get(user__username=c_id)
        except (Customer.DoesNotExist, ValueError):
            try:
                
                customer = Customer.objects.get(pk=c_id)
            except Customer.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            success, msg, data = OrderService.validate_and_format_cart(customer.pk)
            if success:
                return Response(data, status=status.HTTP_200_OK)
            return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            dish_id = request.data.get('dish_id')
            if not dish_id:
                return Response({'error': 'dish_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            order, created = Order.objects.get_or_create(
                customer_id=customer,
                status='Pending',
                defaults={'total': 0.0, 'subtotal': 0.0}
            )

            try:
                dish = Dish.objects.get(pk=dish_id)
                item, created = OrderItem.objects.get_or_create(
                    order_id=order,
                    dish_id=dish,
                    defaults={'unit_price': dish.price, 'quantity': 0}
                )
                item.quantity += 1
                item.unit_price = dish.price #Update the price in case it changed
                item.save()

                # Recalculate Totals (Simple version)
                new_total = 0
                for i in order.items.all():
                    new_total += (i.unit_price * i.quantity)
                order.subtotal = new_total
                order.total = new_total
                order.save()

                return Response({'message': f"Added {dish.name}", 'cart_total': order.total}, status=status.HTTP_200_OK)
            except Dish.DoesNotExist:
                return Response({'error': 'Dish not found'}, status=status.HTTP_404_NOT_FOUND)

    @decorators.action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        Finalize the order and run Promotion Rules.
        """
        #Validate Customer
        c_id = request.data.get('customer_id')
        if not c_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)

        #Get the Pending Order
        order = Order.objects.filter(customer_id__user__username=c_id, status='Pending').first()
        if not order:
            order = Order.objects.filter(customer_id__pk=c_id, status='Pending').first()
            
        if not order or order.items.count() == 0:
            return Response({'error': 'Cart is empty or not found'}, status=status.HTTP_400_BAD_REQUEST)

        #The promotion logic
        customer = order.customer_id
        promoted = False
        
        #Rule: Spend > $100 OR > 3 orders
        past_orders = Order.objects.filter(customer_id=customer, status='Completed').count()
        
        if customer.status == 'regular':
            if order.total > 100.00 or (past_orders >= 3 and customer.warnings == 0):
                customer.status = 'vip'
                customer.save()
                promoted = True

        if customer.balance >= order.total:
            customer.balance -= order.total
            customer.save()
            order.status = 'Completed'
            order.save()
            
            return Response({
                'message': 'Order placed!',
                'new_balance': customer.balance,
                'promoted': promoted,
                'new_status': customer.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)