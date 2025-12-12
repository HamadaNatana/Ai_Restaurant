from rest_framework import viewsets, status, permissions, decorators
from rest_framework.response import Response
from .models import Transactions
from .serializers import TransactionSerializer
from .services import PaymentService

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Transactions.objects.all().order_by('-created_at')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.AllowAny] # Open access for demo

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_param = self.request.query_params.get('customer_id')
        
        if customer_param:
            if not customer_param.isdigit():
                queryset = queryset.filter(customer_id__user__username=customer_param)
            else:
                queryset = queryset.filter(customer_id__pk=customer_param)
                
        return queryset

    @decorators.action(detail=False, methods=['post'])
    def deposit(self, request):
        customer_id = request.data.get('customer_id')
        amount = request.data.get('amount')

        if not customer_id or not amount:
            return Response({'error': 'Missing customer_id or amount'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = PaymentService.process_deposit(customer_id, amount)
        
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)