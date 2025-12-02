import uuid
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Manager
from orders.models import Order

class Driver(TimeStampedModel):
    driver_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True) # Can still deliver or not
    pay = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    warnings = models.PositiveIntegerField(default=0)
    demotion_count = models.PositiveIntegerField(default=0)

class Bids(TimeStampedModel):
    bid_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='bids')
    driver_id = models.ForeignKey(Driver, on_delete=models.CASCADE)
    bid_price = models.DecimalField(max_digits=5, decimal_places=2)

class OrderAssignment(TimeStampedModel):
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.OneToOneField(Order, on_delete=models.CASCADE)
    driver_id = models.ForeignKey(Driver, on_delete=models.CASCADE)
    manager_id = models.ForeignKey(Manager, on_delete=models.CASCADE)
    choosen_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
