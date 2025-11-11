from django.db import models
from django.conf import settings

class Complaint(models.Model):
    COMPLAINANT_TYPES = [('customer','Customer'), ('driver','Driver')]
    TARGET_TYPES = [('chef','Chef'), ('driver','Driver'), ('customer','Customer')]

    filed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='complaints_filed')
    filed_by_is_vip = models.BooleanField(default=False)  # double-weight handling
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='complaints_received', null=True, blank=True)
    target_chef = models.ForeignKey('menu.Chef', on_delete=models.PROTECT, null=True, blank=True)
    target_driver = models.ForeignKey('delivery.Driver', on_delete=models.PROTECT, null=True, blank=True)
    text = models.TextField()
    weight = models.PositiveIntegerField(default=1)  # VIP → 2
    status = models.CharField(max_length=20, default='pending')  # pending/kept/dismissed
    created_at = models.DateTimeField(auto_now_add=True)

class Dispute(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='disputes')
    disputed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
