from django.db import models
from common.models import TimeStampedModel
from accounts.models import Customer
from orders.models import Order

class Transactions(TimeStampedModel):
    TYPE_DEPOSIT = "deposit"
    TYPE_CHARGE = "charge"
    TYPE_REFUND = "refund"

    TYPE_CHOICES = [
        (TYPE_DEPOSIT, "Deposit"),
        (TYPE_CHARGE, "Charge"),
        (TYPE_REFUND, "Refund"),
    ]

    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    
    order_id = models.ForeignKey(Order, on_delete=models.PROTECT, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.type.upper()} - ${self.amount} ({self.customer_id.user.username})"