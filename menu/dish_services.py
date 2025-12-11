"""
Dish Services - UC19: CRUD Dishes Business Logic
Updated to use Dish.is_active field for availability and deletion/unavailability handling.
"""

from typing import Tuple, Optional, Dict, List
from django.db import transaction
from django.db.models import F
from menu.models import Dish, Chef, Ingredient
from orders.models import OrderItem, Order # Assume successful import


class DishService:
    @staticmethod
    def validate_dish_data(dish_data: Dict) -> Tuple[bool, str]:
        """UC19: Validate all required dish fields are present."""
        required_fields = ['name', 'price', 'description']
        
        for field in required_fields:
            if field not in dish_data or not dish_data.get(field):
                return (False, f"{field} is required")
        
        try:
            price = float(dish_data['price'])
            if price <= 0:
                return (False, "Price must be greater than 0")
        except (ValueError, TypeError):
            return (False, "Invalid price format")
        
        return (True, "")

    @staticmethod
    def check_dish_name_unique(dish_name: str, exclude_dish_id=None) -> bool:
        """UC19: Check if dish name is unique in database."""
        queryset = Dish.objects.filter(name__iexact=dish_name.strip())
        
        if exclude_dish_id:
            queryset = queryset.exclude(dish_id=exclude_dish_id)
        
        return not queryset.exists()

    @staticmethod
    def check_dish_in_carts(dish_id) -> bool:
        """UC19: Check if dish exists in any active customer cart (pending orders)."""
        return OrderItem.objects.filter(
            dish_id=dish_id,
            order_id__status=Order.STATUS_PENDING
        ).exists()
    
    @classmethod
    def add_dish(cls, chef_id, dish_data: Dict) -> Tuple[bool, str, Optional[Dish]]:
        """UC19: Add new dish to menu."""
        is_valid, error_msg = cls.validate_dish_data(dish_data)
        if not is_valid: return (False, error_msg, None)
        if not cls.check_dish_name_unique(dish_data['name']): return (False, "Dish name already exists", None)
        
        try:
            chef = Chef.objects.get(chef_id=chef_id)
        except Chef.DoesNotExist: return (False, "Chef not found", None)
        if not chef.is_active: return (False, "Chef account is not active", None)

        try:
            dish = Dish.objects.create(
                name=dish_data['name'].strip(),
                price=dish_data['price'],
                description=dish_data.get('description', '').strip(),
                chef_id=chef,
                special_for_vip=dish_data.get('special_for_vip', False),
                is_active=True 
            )
            
            if 'picture' in dish_data and dish_data['picture']:
                dish.picture = dish_data['picture']
                dish.save()
            if 'ingredients' in dish_data and dish_data['ingredients']:
                cls._add_ingredients_to_dish(dish, dish_data['ingredients'])
            
            return (True, "Dish successfully added to the menu", dish)
        except Exception as e:
            return (False, f"Failed to create dish: {str(e)}", None)
    
    @staticmethod
    def _add_ingredients_to_dish(dish: Dish, ingredients_data):
        """Add ingredients to dish."""
        if isinstance(ingredients_data, str):
            ingredient_names = [i.strip() for i in ingredients_data.split(',') if i.strip()]
            for name in ingredient_names:
                ingredient, _ = Ingredient.objects.get_or_create(name=name)
                DishIngredient.objects.get_or_create(dish=dish, ingredient=ingredient)
        elif isinstance(ingredients_data, list):
            for item in ingredients_data:
                if isinstance(item, str):
                    ingredient, _ = Ingredient.objects.get_or_create(name=item)
                    DishIngredient.objects.get_or_create(dish=dish, ingredient=ingredient)
                elif isinstance(item, dict) and 'ingredient_id' in item:
                    try:
                        ingredient = Ingredient.objects.get(ingredient_id=item['ingredient_id'])
                        DishIngredient.objects.get_or_create(dish=dish, ingredient=ingredient)
                    except Ingredient.DoesNotExist:
                        pass

    @classmethod
    def edit_dish(cls, dish_id, chef_id, updated_data: Dict) -> Tuple[bool, str, Optional[Dish]]:
        """UC19: Update existing dish."""
        try: dish = Dish.objects.get(dish_id=dish_id)
        except Dish.DoesNotExist: return (False, "Dish not found", None)
        
        if str(dish.chef_id.chef_id) != str(chef_id): return (False, "Unauthorized - You can only edit your own dishes", None)
        
        is_valid, error_msg = cls.validate_dish_data(updated_data)
        if not is_valid: return (False, error_msg, None)
        
        new_name = updated_data['name'].strip()
        if new_name.lower() != dish.name.lower():
            if not cls.check_dish_name_unique(new_name, dish_id): return (False, "Dish name already exists", None)
        
        try:
            dish.name = new_name
            dish.price = updated_data['price']
            dish.description = updated_data.get('description', '').strip()
            
            if 'special_for_vip' in updated_data: dish.special_for_vip = updated_data['special_for_vip']
            if 'is_active' in updated_data: dish.is_active = updated_data['is_active']
            if 'picture' in updated_data: dish.picture = updated_data['picture']
            
            dish.save()
            
            if 'ingredients' in updated_data:
                DishIngredient.objects.filter(dish=dish).delete()
                cls._add_ingredients_to_dish(dish, updated_data['ingredients'])
            
            return (True, "Dish details updated successfully", dish)
        except Exception as e:
            return (False, f"Failed to update dish: {str(e)}", None)
    
    @classmethod
    def delete_dish(cls, dish_id, chef_id) -> Tuple[bool, str]:
        """UC19: Delete dish or mark as unavailable if in carts."""
        try: dish = Dish.objects.get(dish_id=dish_id)
        except Dish.DoesNotExist: return (False, "Dish not found")
        
        if str(dish.chef_id.chef_id) != str(chef_id): return (False, "Unauthorized - You can only delete your own dishes")
        
        in_carts = cls.check_dish_in_carts(dish_id)
        
        if not in_carts:
            # Safe to delete (UC19, Normal Scenario 3)
            DishIngredient.objects.filter(dish=dish).delete()
            dish.delete()
            return (True, "Dish deleted successfully")
        else:
            # Mark as unavailable (UC19, Exceptional Scenario 3)
            dish.is_active = False
            dish.save()
            return (True, "Dish marked unavailable. Cannot be deleted while in active customer carts.")
    
    @staticmethod
    def get_chef_dishes(chef_id) -> List[Dish]:
        """Get all dishes created by a specific chef."""
        return list(Dish.objects.filter(chef_id=chef_id).order_by('-created_at'))
    
    @classmethod
    def toggle_dish_availability(cls, dish_id, chef_id) -> Tuple[bool, str, Optional[Dish]]:
        """Toggle dish's is_active status."""
        try: dish = Dish.objects.get(dish_id=dish_id)
        except Dish.DoesNotExist: return (False, "Dish not found", None)
        
        if str(dish.chef_id.chef_id) != str(chef_id): return (False, "Unauthorized", None)
        
        new_status = not dish.is_active
        
        # If toggling OFF while in cart, ensure it's allowed but provide context (for later systems/notifications)
        if new_status == False and cls.check_dish_in_carts(dish_id):
             pass # Logic here might send notification to affected customers
        
        dish.is_active = new_status
        dish.save()
        
        status_msg = "available" if new_status else "unavailable"
        return (True, f"Dish marked as {status_msg}", dish)
