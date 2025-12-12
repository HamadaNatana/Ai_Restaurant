from rest_framework import serializers
from .models import Transactions

class TransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer_id.user.username', read_only=True)
    
    class Meta:
        model = Transactions
        fields = ['id', 'customer_id', 'customer_name', 'order_id', 'amount', 'type', 'created_at']