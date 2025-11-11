from django.contrib.auth.models import AbstractUser, Group
from django.db import models

class User(AbstractUser):
    is_blacklisted = models.BooleanField(default=False)
    warnings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    orders_count = models.PositiveIntegerField(default=0)
    is_vip = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allergies = models.ManyToManyField('menu.Allergen', blank=True, related_name='users')

    def can_place_order(self):
        return not self.is_blacklisted

    def consider_vip_promotion(self):
        # BRR-2.1: spend > $100 OR 3 orders without outstanding complaints
        if (self.total_spent > 100) or (self.orders_count >= 3 and self.warnings == 0):
            self.is_vip = True
            self.save()

    def consider_vip_demotion(self):
        # BRR-2.5: VIP demoted at 2 warnings (warnings cleared)
        if self.is_vip and self.warnings >= 2:
            self.is_vip = False
            self.warnings = 0
            self.save()

    def enforce_deregistration(self):
        # BRR-2.4: Registered Customer closed at 3 warnings
        if not self.is_vip and self.warnings >= 3:
            self.is_blacklisted = True
            self.save()
