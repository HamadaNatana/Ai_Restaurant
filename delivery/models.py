from django.db import models
from django.conf import settings

class Driver(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    demotions = models.PositiveIntegerField(default=0)

class DeliveryBid(models.Model):
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='bids')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class AssignmentMemo(models.Model):
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE)
    memo = models.TextField()  # justification if non-lowest bid chosen
    created_at = models.DateTimeField(auto_now_add=True)
