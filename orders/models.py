import uuid
from django.db import models
from django.conf import settings
from menu.models import Dish # Import Dish from menu app

# Placeholder for TimeStampedModel
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

# Placeholder Customer Model (Contains essential fields for UC04/UC07 checks)
class Customer(TimeStampedModel):
    customer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    warnings = models.PositiveIntegerField(default=0)
    order_count = models.PositiveIntegerField(default=0)
    # user is needed for user_type checks (VIP/Registered)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True) 
    # Add other fields as necessary from accounts/models.py

    class Meta:
        abstract = True
        
    def get_user_type(self):
        # Placeholder for fetching user type (e.g., 'vip', 'customer', 'chef')
        return getattr(self.user, 'user_type', 'customer')

class Order(TimeStampedModel):
    # Order Statuses
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
    # Link to Customer model (using placeholder until actual model is available)
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT) 
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default=STATUS_PENDING)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    vip_discount_applied = models.BooleanField(default=False)
    free_delivery_applied = models.BooleanField(default=False)

    class Meta:
        # Constraint to ensure only one pending order (cart) per customer
        constraints = [
            models.UniqueConstraint(fields=['customer_id'], condition=models.Q(status=STATUS_PENDING), name='unique_pending_order_per_customer')
        ]
    
class OrderItem(TimeStampedModel):
    order_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items') 
    dish_id = models.ForeignKey(Dish, on_delete=models.PROTECT) 
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
