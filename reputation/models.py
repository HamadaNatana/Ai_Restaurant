from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Customer
from menu.models import Chef, Dish
from delivery.models import Driver
from orders.models import Order
class WarningLog(TimeStampedModel):
    TARGET_CUSTOMER = "customer"
    TARGET_DRIVER = "driver"
    TARGET_CHEF = "chef"

    TARGET_CHOICES = [
        (TARGET_CUSTOMER, "Customer"),
        (TARGET_DRIVER, "Delivery Driver"),
        (TARGET_CHEF, "Chef"),
    ]

    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    customer_id = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE)
    driver_id = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE)
    chef_id = models.ForeignKey(Chef, null=True, blank=True, on_delete=models.CASCADE)
    reason = models.TextField()

class Feedback(TimeStampedModel):
    STATUS_KEPT = 'kept'
    STATUS_PENDING = 'pending'
    STATUS_DISMISSED = 'dismissed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_KEPT,'kept'),
        (STATUS_PENDING,'pending'),
        (STATUS_DISMISSED,'dismissed'),
        (STATUS_CANCELLED, 'cancelled')
    ]

    filer_customer_id = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name="feedback_filed")
    filer_driver_id = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE, related_name="feedback_filed")

    target_customer_id = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name="feedback_received")
    target_driver_id = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE, related_name="feedback_received")
    target_chef_id = models.ForeignKey(Chef, null=True, blank=True, on_delete=models.CASCADE, related_name="feedback_received")
    target_dish_id = models.ForeignKey(Dish, null=True, blank=True, on_delete=models.CASCADE, related_name="feedback_about")

    is_compliment = models.BooleanField(default=False) # False → Complaint / True → Compliment
    weight = models.PositiveIntegerField(default=1)  # VIP → 2
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

class Dispute(models.Model):
    complaint = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='disputes')
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    reason = models.TextField()

class FeedbackDecision(TimeStampedModel):
    OUTCOME_CHOICES = [
        ("accepted", "Accepted"),
        ("dismissed", "Dismissed"),
    ]
    feedback = models.OneToOneField(Feedback, on_delete=models.CASCADE, related_name="decision")
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    note = models.TextField(blank=True)


class FoodRating(TimeStampedModel):
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="food_ratings")
    dish_id = models.ForeignKey(Dish, on_delete=models.PROTECT, related_name="ratings")
    order_id = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="food_ratings")
    stars = models.PositiveSmallIntegerField()  # 1–5

class DeliveryRating(TimeStampedModel):
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="delivery_ratings")
    driver_id = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="ratings")
    order_id = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="delivery_ratings")
    stars = models.PositiveSmallIntegerField()