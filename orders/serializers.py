from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual items in the cart.
    """
    dish_name = serializers.CharField(source='dish_id.name', read_only=True)
    dish_image = serializers.ImageField(source='dish_id.picture', read_only=True)
    dish = serializers.IntegerField(source='dish_id.pk', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'dish', 'dish_name', 'dish_image', 'quantity', 'unit_price', 'subtotal']

    def get_subtotal(self, obj):
        """
        Calculates quantity * unit_price dynamically.
        """
        if obj.unit_price and obj.quantity:
            return obj.quantity * obj.unit_price
        return 0

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the full Order/Cart.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    
    customer_name = serializers.CharField(source='customer_id.user.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',               
            'customer_id',      
            'customer_name',    
            'status', 
            'total',            
            'created_at',         
            'items',
            'subtotal',
            'discount_amount'
        ]