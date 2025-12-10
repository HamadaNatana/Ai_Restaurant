from rest_framework import serializers
from .models import Customer, Manager

class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    average_order_value = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = Customer
        fields = ['user','address','is_blacklisted','warnings','total_spent','orders_count',
                  'status','balance','status', 'status_display', 'average_order_value']
        read_only_fields = ('total_spent', 'orders_count', 'balance')

class ManagerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Manager
        fields = ['user']