from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import RegistrationApproval, HRAction, AssignmentMemo
from .serializers import RegistrationApprovalSerializer, RegistrationApprovalUpdateSerializer, HRActionSerializer, AssignmentMemoSerializer

class RegistrationApprovalViewSet(viewsets.ModelViewSet):
    """
    Manages the list of pending, approved, and rejected user registrations.
    Provides custom actions for managers to process approvals.
    """
    queryset = RegistrationApproval.objects.all().order_by('created_at')
    serializer_class = RegistrationApprovalSerializer
    # Only Managers should be able to access this. Authentication/Permissions are assumed.

    # 1. Custom Action: Get Pending Registrations
    # Route: /api/hr/registrations/pending/
    @action(detail=False, methods=['get'])
    def pending(self, request):
        pending_registrations = self.get_queryset().filter(
            status=RegistrationApproval.STATUS_PENDING
        )
        serializer = self.get_serializer(pending_registrations, many=True)
        return Response(serializer.data)

    # 2. Custom Action: Approve or Reject a specific registration
    # Route: /api/hr/registrations/{pk}/process_request/
    @action(detail=True, methods=['post'])
    def process_request(self, request, pk=None):
        registration = self.get_object()
        serializer = RegistrationApprovalUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        if registration.status != RegistrationApproval.STATUS_PENDING:
            return Response(
                {"error": f"Registration is already {registration.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        registration.status = new_status
        registration.processed_at = timezone.now()
        
        if new_status == RegistrationApproval.STATUS_REJECTED:
            registration.rejection_reason = rejection_reason
        
        # --- Actual account creation/manipulation logic would go here ---
        # e.g., if approved, call a service function to create the actual User/Chef/Driver account
        # if new_status == RegistrationApproval.STATUS_APPROVED:
        #     create_actual_account(registration)
        # ---------------------------------------------------------------

        registration.save()
        
        return Response(self.get_serializer(registration).data)


class HRActionViewSet(viewsets.ModelViewSet):
    """
    Handles the creation and listing of personnel actions (fire, demote, bonus, etc.).
    """
    queryset = HRAction.objects.all().order_by('created_at')
    serializer_class = HRActionSerializer

class AssignmentMemoViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD operations for Assignment Memos related to specific orders.
    """
    queryset = AssignmentMemo.objects.all().order_by('created_at')
    serializer_class = AssignmentMemoSerializer