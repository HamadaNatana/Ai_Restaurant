from django.contrib import admin
from .models import Dish, Chef, Allergen, Ingredient, DishIngredient

# Register your models here.

@admin.register(Chef)
class ChefAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'salary', 'demotion_count')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'chef_id', 'special_for_vip', 'is_active')
    list_filter = ('is_active', 'special_for_vip', 'chef_id')
    search_fields = ('name', 'description')
    inlines = [DishIngredientInline] # Assuming DishIngredientInline exists/is defined

@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'allergens') 
    search_fields = ('name',)