from rest_framework import viewsets, status, permissions, decorators
from rest_framework.response import Response
from .models import Transactions
from .serializers import TransactionSerializer
from .services import PaymentService

class PaymentViewSet(viewsets.ModelViewSet):
    """
    Unified Endpoint for Payment Operations.
    Matches the 'David Format' (ViewSet + Router).
    """
    queryset = Transactions.objects.all().order_by('-created_at')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.AllowAny] # Open access for demo

    # --- HISTORY ---
    def get_queryset(self):
        """Filter history by customer"""
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id__pk=customer_id)
        return queryset

    # --- ACTIONS ---
    @decorators.action(detail=False, methods=['post'])
    def deposit(self, request):
        """
        UC08: Deposit money.
        Input: { "customer_id": "...", "amount": 50.00 }
        """
        customer_id = request.data.get('customer_id')
        amount = request.data.get('amount')

        if not customer_id or not amount:
            return Response({'error': 'Missing customer_id or amount'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = PaymentService.process_deposit(customer_id, amount)
        
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)