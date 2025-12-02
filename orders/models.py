import uuid
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Customer
from menu.models import Dish

class Order(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_ASSIGNED = "assigned"
    STATUS_DELIVERING = "delivering"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_DELIVERING, "Delivering"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    vip_discount_applied = models.BooleanField(default=False)
    free_delivery_applied = models.BooleanField(default=False)

class OrderItem(TimeStampedModel):
    order_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish_id = models.ForeignKey(Dish, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
