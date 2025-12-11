from rest_framework import serializers
from .models import RegistrationApproval, HRAction, AssignmentMemo

# --- Registration Approval Serializers ---

class RegistrationApprovalSerializer(serializers.ModelSerializer):
    # manager_id field will handle the Manager foreign key
    class Meta:
        model = RegistrationApproval
        fields = [
            'id', 'manager', 'username', 'password_hash', 'address', 
            'status', 'rejection_reason', 'created_at', 'processed_at'
        ]
        read_only_fields = ['status', 'processed_at', 'rejection_reason'] # Manager handles status update via a specific action

class RegistrationApprovalUpdateSerializer(serializers.Serializer):
    """Serializer used for the custom action to approve/reject a registration."""
    status = serializers.ChoiceField(
        choices=RegistrationApproval.STATUS_CHOICES[1:], # Only 'approved' or 'rejected'
        required=True
    )
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


# --- HR Action Serializers ---

class HRActionSerializer(serializers.ModelSerializer):
    # This serializer handles the complex foreign key structure for actors
    class Meta:
        model = HRAction
        fields = '__all__'


# --- Assignment Memo Serializers ---

class AssignmentMemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentMemo
        fields = '__all__'