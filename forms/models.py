from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Customer
from menu.models import Chef, Dish
from delivery.models import Driver

# -----------------------------------------------------------
#   UC16: Discussion Board (Topics + Posts)
# -----------------------------------------------------------
class DiscussionThread(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("chef", "Chef"),
        ("dish", "Dish"),
        ("delivery", "Delivery"),
        ("general", "General"),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)

    dish_id = models.ForeignKey(Dish, null=True, blank=True, on_delete=models.SET_NULL, related_name="threads")
    chef_id = models.ForeignKey(Chef, null=True, blank=True, on_delete=models.SET_NULL, related_name="threads")
    driver_id = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="threads")

    is_locked = models.BooleanField(default=False)
    last_activity_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Topic #{self.pk}: {self.title[:40]}"

class DiscussionPost(TimeStampedModel):
    thread_id = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='posts')
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    body = models.TextField()

    def __str__(self):
        return f"Post #{self.pk} on Topic #{self.topic_id}"