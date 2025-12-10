"""
User Models - Defines the Custom User model (Customer).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

# Re-establishing the TimeStampedModel structure used elsewhere
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Customer(AbstractUser, TimeStampedModel):
    """
    The main User model, inheriting from AbstractUser (includes username, password, email, etc.)
    and adding customer-specific fields for UC04/UC07.
    """
    
    # --- Fields from your previous context/use cases ---
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('vip', 'VIP'),
        # Note: Using lowercase status values for consistency with services.py logic
    ]
    
    # Required for UC04 (Promotion/Demotion) and UC07 (Checkout/Discounts)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    warnings = models.PositiveIntegerField(default=0)
    is_blacklisted = models.BooleanField(default=False)
    
    # Required for UC04/UC07 VIP promotion criteria/benefits tracking
    order_count = models.PositiveIntegerField(default=0) 
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0) # For UC04 $100 spending threshold

    # Custom field to act as the primary key/ID for consistency, though AbstractUser provides 'id'
    customer_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Additional fields that might be used by other apps:
    user_type = models.CharField(max_length=20, default='customer') # Maps role for access checks
    
    class Meta:
        # Define default table name if needed
        db_table = 'users_customer'

    def __str__(self):
        return self.username
    
    # Helper method to match logic used in order services (Customer.get_user_type())
    def get_user_type(self):
        return self.user_type
    