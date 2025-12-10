from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Transactions
from accounts.models import Customer 
class DepositAPIView(APIView):
    #UC8: Customer deposits money into account via API request (from Streamlit).
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # 1. Get amount from JSON request body
        amount = request.data.get("amount")
        
        # 2. Validation
        try:
            # We use float() here for validation, but may use Decimal() for real money
            amount = float(amount) 
        except (ValueError, TypeError):
            return Response({"error": "Invalid amount type or missing."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Business rules
        if amount <= 0:
            return Response({"error": "Deposit amount must be positive."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        if amount >= 100000:
            return Response({"error": "Deposit amount is too excessive."}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # 3. Process Transaction
        # Get the Customer object related to the authenticated user (One-to-One connection confirmed)
        try:
            customer: Customer = request.user.customer
        except Customer.DoesNotExist:
            return Response({"error": "Customer profile not found."}, 
                            status=status.HTTP_404_NOT_FOUND)

        # Update balance
        customer.balance += amount
        customer.save()

        # Create Transaction record
        Transactions.objects.create(
            customer=customer,
            type=Transactions.TYPE_DEPOSIT,
            amount=amount,
        )

        # 4. Success Response
        return Response({
            "message": "Deposit successful! Your new balance is.",
            "new_balance": customer.balance,
        }, status=status.HTTP_200_OK)