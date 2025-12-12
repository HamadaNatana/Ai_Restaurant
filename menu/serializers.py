from rest_framework import serializers
from menu.models import Dish, Chef, Allergen, Ingredient

class ChefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chef
        fields = ['id', 'name', 'is_active','salary']

class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = ['allergen_id', 'name']

class MenuDishSerializer(serializers.ModelSerializer):
    chef_name = serializers.CharField(source='chef_id.name', read_only=True)
    ingredients_list = serializers.SerializerMethodField()
    allergens_list = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'name', 'price', 'description', 'picture',
            'chef_name', 'special_for_vip', 'is_active',
            'ingredients_list', 'allergens_list'
        ]

    def get_ingredients_list(self, obj):
        """Get list of ingredient names for this dish"""
        try:
            return [i.name for i in obj.ingredient.all()]
        except AttributeError:
            return []

    def get_allergens_list(self, obj):
        """Get list of allergens for this dish"""
        allergens = set()
        try:
            for ing in obj.ingredient.all():
                for alg in ing.allergens.all():
                    allergens.add(alg.name)
        except AttributeError:
            pass
        return list(allergens)

class MenuResponseSerializer(serializers.Serializer):
    """Response serializer for menu endpoint (UC06)"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    total_dishes = serializers.IntegerField()
    user_type = serializers.CharField()
    dishes = MenuDishSerializer(many=True)