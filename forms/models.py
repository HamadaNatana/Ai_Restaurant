import uuid
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Customer
from menu.models import Chef, Dish
from delivery.models import Driver

class DiscussionThread(TimeStampedModel):
    thread_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)

    dish_id = models.ForeignKey(Dish, null=True, blank=True, on_delete=models.SET_NULL, related_name="threads")
    chef_id = models.ForeignKey(Chef, null=True, blank=True, on_delete=models.SET_NULL, related_name="threads")
    driver_id = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="threads")

class DiscussionPost(TimeStampedModel):
    post_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_id = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='posts')
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    body = models.TextField()
