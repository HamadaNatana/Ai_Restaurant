from django.conf import settings
from django.db import models
from common.models import TimeStampedModel

class Customer(TimeStampedModel):
    STATUS_REGISTERED = "registered"
    STATUS_VIP = "vip"
    STATUS_CHOICES = [
        (STATUS_REGISTERED, "Registered"),
        (STATUS_VIP, "VIP"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True)
    address = models.TextField(unique=True)
    is_blacklisted = models.BooleanField(default=False)
    warnings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    orders_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REGISTERED)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def can_place_order(self):
        return not self.is_blacklisted
# UC4: VIP promotion/demotion
    def consider_vip_promotion(self):
        # BRR-2.1: spend > $100 OR 3 orders without outstanding complaints
        if (self.total_spent > 100) or (self.orders_count >= 3 and self.warnings == 0):
            self.status = self.STATUS_VIP
            self.save()

    def consider_vip_demotion(self):
        # BRR-2.5: VIP demoted at 2 warnings (warnings cleared)
        if self.status == self.STATUS_VIP and self.warnings >= 2:
            self.status = self.STATUS_REGISTERED
            self.warnings = 0
            self.save()

    def enforce_deregistration(self):
        # BRR-2.4: Registered Customer closed at 3 warnings
        if self.status == self.STATUS_REGISTERED and self.warnings >= 3:
            self.is_blacklisted = True
            self.save()

    def __str__(self):
        return self.user.get_full_name()

class Manager(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,unique=True)

    def __str__(self):
        return self.user.get_full_name()