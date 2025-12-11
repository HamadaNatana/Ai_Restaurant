from django.db import models
from django.conf import settings
from common.models import TimeStampedModel 
from accounts.models import Customer 

class Allergen(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
class AllergyPreference(TimeStampedModel):
    customer = models.OneToOneField(Customer,on_delete=models.CASCADE,related_name="allergy_preference")
    allergens = models.ManyToManyField(Allergen, blank=True)

    def get_allergen_list(self):
        if not self.allergens:
            return []
        return [
            a.strip().lower()
            for a in self.allergens.split(",")
            if a.strip()
        ]

    def set_allergen_list(self, allergen_list):
        cleaned = [a.strip().lower() for a in allergen_list if a.strip()]
        self.allergens = ",".join(cleaned)

    def __str__(self):
        return f"Allergies({self.customer}: {self.allergens})"


class Ingredient(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    allergens = models.OneToOneField(Allergen, blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

class Chef(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, unique=True)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    demotion_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Dish(TimeStampedModel):
    chef = models.ForeignKey(Chef, on_delete=models.PROTECT)
    ingredient = models.ManyToManyField(Ingredient)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    picture = models.ImageField(upload_to='dishes/', blank=True, null=True)
    special_for_vip = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
'''
class DishIngredient(TimeStampedModel):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
'''
