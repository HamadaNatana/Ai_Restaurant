"""
Orders Serializers - UC07: Placing Orders
Adapted for group's existing models
"""

from rest_framework import serializers
from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    dish_name = serializers.CharField(source='dish_id.name', read_only=True)
    dish_picture = serializers.ImageField(source='dish_id.picture', read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'order_item_id', 'dish_id', 'dish_name', 'dish_picture',
            'quantity', 'unit_price', 'subtotal'
        ]
    
    def get_subtotal(self, obj):
        return float(obj.unit_price * obj.quantity)


class OrderSerializer(serializers.ModelSerializer):
    """Full order serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'customer_id', 'status',
            'subtotal', 'discount_amount', 'total',
            'vip_discount_applied', 'free_delivery_applied',
            'items', 'created_at', 'updated_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Compact order serializer for listings"""
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'status', 'total', 'created_at', 'item_count'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding item to cart"""
    dish_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()


class UpdateQuantitySerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=0)


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout"""
    customer_id = serializers.UUIDField()
    