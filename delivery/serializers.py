from rest_framework import serializers
from .models import Driver , Bids

class DriverSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source='user', read_only=True)
    
    class Meta:
        model = Driver
        fields = ['id', 'username', 'pay', 'warnings', 'demotion_count', 'is_active']

class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bids
        fields = ['order_id','driver_id','bid_price']