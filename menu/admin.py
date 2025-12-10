from django.contrib import admin
from .models import Chef, Dish, Ingredient, Allergen

admin.site.register(Chef)
admin.site.register(Dish)
admin.site.register(Ingredient)
admin.site.register(Allergen)
