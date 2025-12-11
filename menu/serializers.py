from rest_framework import serializers
from menu.models import Dish, Chef, Allergen, Ingredient

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
    # Use chef_id.name to get the chef's name
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
        # FIXED: Directly access the 'ingredient' ManyToMany field on the Dish object
        try:
            return [i.name for i in obj.ingredient.all()]
        except AttributeError:
            return []

    def get_allergens_list(self, obj):
        """Get list of allergens for this dish"""
        # FIXED: Iterate through the ingredients to collect unique allergens
        allergens = set()
        try:
            for ing in obj.ingredient.all():
                # Assuming Ingredient has a ManyToMany field 'allergens'
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