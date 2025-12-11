from decimal import Decimal
from django.db import transaction
from .models import Transactions
from accounts.models import Customer
# We don't import Order here to avoid circular imports, usually not needed for deposits

class PaymentService:
    @staticmethod
    def process_deposit(customer_id, amount):
        """
        UC08: Process a deposit.
        """
        # 1. Validation
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return False, "Deposit must be positive."
            if amount >= 100000:
                return False, "Deposit limit exceeded."
        except (ValueError, TypeError):
             return False, "Invalid amount."

        # 2. Get Customer
        try:
            # We assume customer_id is the Primary Key (UUID/Int)
            # If you send a username, you'd need the 'smart resolver' logic here too.
            # For now, let's assume the frontend sends the correct ID.
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return False, "Customer not found."

        # 3. Process Transaction (Atomic)
        try:
            with transaction.atomic():
                # A. Update Balance
                customer.balance += amount
                customer.save()

                # B. Create Record
                # Note: order_id is NULL for deposits (we fixed the model earlier)
                Transactions.objects.create(
                    customer_id=customer,
                    type=Transactions.TYPE_DEPOSIT,
                    amount=amount
                )
                
                return True, f"Deposited ${amount}. New Balance: ${customer.balance}"
        except Exception as e:
            return False, f"Transaction failed: {str(e)}"