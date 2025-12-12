from decimal import Decimal
from django.db import transaction
from .models import Transactions
from accounts.models import Customer

class PaymentService:
    @staticmethod
    def process_deposit(customer_id, amount):
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return False, "Deposit must be positive."
            if amount >= 100000:
                return False, "Deposit limit exceeded."
        except (ValueError, TypeError):
             return False, "Invalid amount."

        try:
            customer = Customer.objects.get(user__username=str(customer_id))
        except Customer.DoesNotExist:
            try:
                customer = Customer.objects.get(pk=customer_id)
            except (Customer.DoesNotExist, ValueError):
                return False, f"Customer '{customer_id}' not found."

        try:
            with transaction.atomic():
                customer.balance += amount
                customer.save()

                Transactions.objects.create(
                    customer_id=customer,
                    type=Transactions.TYPE_DEPOSIT,
                    amount=amount
                )
                
                return True, f"Deposited ${amount}. New Balance: ${customer.balance}"
        except Exception as e:
            return False, f"Transaction failed: {str(e)}"