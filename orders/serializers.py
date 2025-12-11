from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    dish_name = serializers.ReadOnlyField(source='dish.name')

    class Meta:
        model = OrderItem
        fields = ['id', 'dish_id', 'dish_name', 'quantity', 'unit_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['order_id', 'customer_id', 'status', 'total', 'items', 'subtotal', 'discount_amount']