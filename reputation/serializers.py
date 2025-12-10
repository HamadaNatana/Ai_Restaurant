from rest_framework import serializers
from .models import Feedback, WarningLog

class FeedbackSerializer(serializers.ModelSerializer):
    # These custom fields let the frontend see "John Doe" instead of just "null"
    filer_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'feedback_id', 
            'is_compliment', 
            'weight', 
            'status', 
            'message', 
            'filer_name', 
            'target_name',
            'created', # inherited from TimeStampedModel
        ]

    def get_filer_name(self, obj):
        # Checks which filer slot is used and returns that user's name
        if obj.filer_customer_id:
            return obj.filer_customer_id.username  # Adjust if your Customer model uses .user.username
        if obj.filer_driver_id:
            return obj.filer_driver_id.name
        return "Unknown"

    def get_target_name(self, obj):
        if obj.target_customer_id:
            return f"Customer: {obj.target_customer_id.username}"
        if obj.target_driver_id:
            return f"Driver: {obj.target_driver_id.name}"
        if obj.target_chef_id:
            return f"Chef: {obj.target_chef_id.name}"
        if obj.target_dish_id:
            return f"Dish: {obj.target_dish_id.name}"
        return "Unknown"

class WarningLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarningLog
        fields = '__all__'