from django.db import models

class Allergen(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Ingredient(models.Model):
    name = models.CharField(max_length=120, unique=True)
    allergens = models.ManyToManyField(Allergen, blank=True)

class Chef(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    demotions = models.PositiveIntegerField(default=0)

class Dish(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    ingredients = models.ManyToManyField(Ingredient, through='DishIngredient')
    picture = models.ImageField(upload_to='dishes/', blank=True, null=True)
    special_for_vip = models.BooleanField(default=False)  # FR-1.1.11

class DishIngredient(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
