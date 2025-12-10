from rest_framework import serializers
from menu.models import Chef
from delivery.models import Driver
from accounts.models import Customer

class ChefHRSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Chef
        fields = ['chef_id', 'username', 'name', 'salary', 'demotion_count', 'is_active']

class DriverHRSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Driver
        # Note: Driver model uses 'pay', not 'salary'
        fields = ['driver_id', 'username', 'is_active', 'pay', 'warnings', 'demotion_count']

class CustomerHRSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Customer
        fields = ['customer_id', 'username', 'status', 'warnings', 'balance', 'is_blacklisted']