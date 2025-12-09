import uuid
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Manager
from orders.models import Order


class Driver(TimeStampedModel):
    driver_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  # Can still deliver or not
    pay = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    warnings = models.PositiveIntegerField(default=0)
    demotion_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Driver: {self.user.username}"


class Bids(TimeStampedModel):
    bid_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='bids')
    driver_id = models.ForeignKey(Driver, on_delete=models.CASCADE)
    bid_price = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Bid ${self.bid_price} by {self.driver_id.user.username} on Order {self.order_id.id}"


class OrderAssignment(TimeStampedModel):
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.OneToOneField(Order, on_delete=models.CASCADE)
    driver_id = models.ForeignKey(Driver, on_delete=models.CASCADE)
    manager_id = models.ForeignKey(Manager, on_delete=models.CASCADE)
    choosen_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("ON_THE_WAY", "On the way"),
        ("DELIVERED", "Delivered"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    def __str__(self):
        return f"Assignment for Order {self.order_id.id} → Driver: {self.driver_id.user.username}"

