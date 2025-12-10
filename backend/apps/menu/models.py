import uuid
from django.db import models
from django.conf import settings
# from common.models import TimeStampedModel # Assuming common app import
# from accounts.models import Customer # Assuming Customer import

# Placeholder for TimeStampedModel
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

# Placeholder for Customer (used by CustomerAllergy)
class Customer(TimeStampedModel):
    customer_id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    class Meta:
        abstract = True


class Allergen(TimeStampedModel):
    allergen_id =  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

class CustomerAllergy(TimeStampedModel):
    # customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT) # Uncomment when Customer is proper model
    allergen_id = models.ForeignKey(Allergen, on_delete=models.PROTECT)

class Ingredient(TimeStampedModel):
    ingredient_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    allergens = models.OneToOneField(Allergen, blank=True, null=True, on_delete=models.PROTECT)

class Chef(TimeStampedModel):
    chef_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    demotion_count = models.PositiveIntegerField(default=0)

class Dish(TimeStampedModel):
    dish_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chef_id = models.ForeignKey(Chef, on_delete=models.PROTECT)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    picture = models.ImageField(upload_to='dishes/', blank=True, null=True)
    special_for_vip = models.BooleanField(default=False)  # FR-1.1.11
    is_active = models.BooleanField(default=True) # CRITICAL: Added for UC19/UC06/UC07 checks

class DishIngredient(TimeStampedModel):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)