from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual items in the cart.
    """
    # 1. Map 'dish_name' from the related 'dish_id' object
    dish_name = serializers.CharField(source='dish_id.name', read_only=True)
    
    # 2. Return the UUID of the dish (using the field 'dish_id')
    dish = serializers.UUIDField(source='dish_id.pk', read_only=True)
    
    # 3. Calculate subtotal on the fly (price * quantity)
    #    (Or use the field from the model if you store it)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        # Note: We use 'id' for the item's own ID unless you have a specific 'order_item_id' field
        fields = ['id', 'dish', 'dish_name', 'quantity', 'unit_price', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the full Order/Cart.
    """
    # 1. Use the related_name='items' from your model
    items = OrderItemSerializer(many=True, read_only=True)
    
    # 2. Get customer username safely through 'customer_id' field
    customer_name = serializers.CharField(source='customer_id.user.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',               # Order ID
            'customer_id',      # The raw customer ID
            'customer_name',    # The readable name
            'status', 
            'total',            # Matches your model field 'total'
            'created',          # From TimeStampedModel
            'items',
            'subtotal',
            'discount_amount'
        ]