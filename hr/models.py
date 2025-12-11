from django.db import models
from common.models import TimeStampedModel
from menu.models import Chef
from accounts.models import Customer,Manager
from delivery.models import Driver, OrderAssignment

class RegistrationApproval(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]
    manager = models.ForeignKey(Manager, on_delete=models.PROTECT, null=True, blank=True)
    username = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, blank=True)      
    first_name = models.CharField(max_length=150, blank=True)  
    last_name = models.CharField(max_length=150, blank=True)
    password_hash = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

class HRAction(TimeStampedModel):
    ACTOR_CHEF = "chef"
    ACTOR_DRIVER = "driver"
    ACTOR_CUSTOMER = "customer"

    ACTOR_TYPE_CHOICES = [
        (ACTOR_CHEF, "Chef"),
        (ACTOR_DRIVER, "Delivery Driver"),
        (ACTOR_CUSTOMER, "Customer"),
    ]

    ACTION_DEMOTE = "demote"
    ACTION_FIRE = "fire"
    ACTION_BONUS = "bonus"
    ACTION_RAISE = "raise"
    ACTION_CUT = "cut"
    ACTION_BLACKLIST = "blacklist"

    ACTION_CHOICES = [
        (ACTION_DEMOTE, "Demote"),
        (ACTION_FIRE, "Fire"),
        (ACTION_BONUS, "Bonus"),
        (ACTION_RAISE, "Raise Salary"),
        (ACTION_CUT, "Cut Salary"),
        (ACTION_BLACKLIST, "Blacklist Customer"),
    ]

    manager_id = models.ForeignKey(Manager, on_delete=models.PROTECT, related_name="hr_actions")
    actor_type = models.CharField(max_length=20, choices=ACTOR_TYPE_CHOICES)

    chef_id = models.ForeignKey(Chef, null=True, blank=True, on_delete=models.CASCADE)
    driver_id = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE)
    customer_id = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE)

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)

class AssignmentMemo(TimeStampedModel):
    assignment = models.OneToOneField(OrderAssignment, on_delete=models.CASCADE, related_name="memo")
    text = models.TextField()