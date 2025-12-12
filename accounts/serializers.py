from rest_framework import serializers, decorators, status
from rest_framework.response import Response
from .models import Customer, Manager

class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    average_order_value = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    @decorators.action(detail=True, methods=['post'])
    def issue_warning(self, request, pk=None):
        customer = self.get_object()

        customer.warnings += 1
        customer.save()

        customer.consider_vip_demotion()
        customer.enforce_deregistration()
        
        return Response({
            'status': 'warning issued',
            'current_warnings': customer.warnings,
            'customer_status': customer.status,
            'is_blacklisted': customer.is_blacklisted
        })

    @decorators.action(detail=True, methods=['post'])
    def check_vip(self, request, pk=None):
        customer = self.get_object()

        old_status = customer.status
        customer.consider_vip_promotion()
        
        if customer.status != old_status:
            msg = "Promoted to VIP!"
        else:
            msg = "Not eligible for promotion yet."

        return Response({'message': msg, 'new_status': customer.status})
    class Meta:
        model = Customer
        fields = ['id','user','address','is_blacklisted','warnings','total_spent','orders_count',
                  'status','balance','status', 'status_display', 'average_order_value']

class ManagerSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Manager
        fields = ['user']