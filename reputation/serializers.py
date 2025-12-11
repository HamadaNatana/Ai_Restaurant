from rest_framework import serializers
from .models import FoodRating, DeliveryRating, Feedback, WarningLog

class FoodRatingSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish_id.name', read_only=True)
    customer_name = serializers.CharField(source='customer_id.user.username', read_only=True)

    class Meta:
        model = FoodRating
        fields = ['id', 'order_id', 'dish_id', 'dish_name', 'customer_id', 'customer_name', 'stars', 'created']

class DeliveryRatingSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver_id.user.username', read_only=True)
    customer_name = serializers.CharField(source='customer_id.user.username', read_only=True)

    class Meta:
        model = DeliveryRating
        fields = ['id', 'order_id', 'driver_id', 'driver_name', 'customer_id', 'customer_name', 'stars', 'created']

class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for Complaints/Compliments.
    """
    filer_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'id', 'status', 'is_compliment', 'message', 'weight',
            'filer_customer_id', 'filer_driver_id', 'filer_name',
            'target_customer_id', 'target_driver_id', 'target_chef_id', 'target_dish_id',
            'target_name', 'created'
        ]

    def get_filer_name(self, obj):
        if obj.filer_customer_id: return obj.filer_customer_id.user.username
        if obj.filer_driver_id: return obj.filer_driver_id.user.username
        return "Unknown"

    def get_target_name(self, obj):
        if obj.target_customer_id: return obj.target_customer_id.user.username
        if obj.target_driver_id: return obj.target_driver_id.user.username
        if obj.target_chef_id: return obj.target_chef_id.name
        if obj.target_dish_id: return obj.target_dish_id.name
        return "General"