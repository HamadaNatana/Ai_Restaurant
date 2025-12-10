"""
Menu Serializers - UC06: Menu Access & UC19: CRUD Dishes
"""

from rest_framework import serializers
from menu.models import Dish, Chef, Allergen, DishIngredient, Ingredient


class ChefSerializer(serializers.ModelSerializer):
    """Chef serializer"""
    
    class Meta:
        model = Chef
        fields = ['chef_id', 'name', 'is_active']


class AllergenSerializer(serializers.ModelSerializer):
    """Allergen serializer"""
    
    class Meta:
        model = Allergen
        fields = ['allergen_id', 'name']


class MenuDishSerializer(serializers.ModelSerializer):
    """Serializer for menu display with all necessary info"""
    chef_name = serializers.CharField(source='chef_id.name', read_only=True)
    ingredients_list = serializers.SerializerMethodField()
    allergens_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Dish
        fields = [
            'dish_id', 'name', 'price', 'description', 'picture',
            'chef_name', 'special_for_vip', 'is_active',
            'ingredients_list', 'allergens_list'
        ]
    
    def get_ingredients_list(self, obj):
        """Get list of ingredient names for this dish"""
        dish_ingredients = DishIngredient.objects.filter(dish=obj).select_related('ingredient')
        return [di.ingredient.name for di in dish_ingredients]
    
    def get_allergens_list(self, obj):
        """Get list of allergens for this dish"""
        dish_ingredients = DishIngredient.objects.filter(
            dish=obj
        ).select_related('ingredient', 'ingredient__allergens').filter(
            ingredient__allergens__isnull=False
        )
        
        allergens = [di.ingredient.allergens.name for di in dish_ingredients]
        return list(set(allergens))


class MenuResponseSerializer(serializers.Serializer):
    """Response serializer for menu endpoint (UC06)"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    total_dishes = serializers.IntegerField()
    user_type = serializers.CharField()
    dishes = MenuDishSerializer(many=True)
    