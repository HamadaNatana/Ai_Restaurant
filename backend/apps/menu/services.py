"""
Menu Services - UC06: Menu Access Business Logic
Adapted to work with existing group models (Dish, Chef, Allergen, CustomerAllergy, etc.)
"""

from typing import Tuple, List, Dict, Optional
from menu.models import Dish, Chef, Allergen, CustomerAllergy, DishIngredient
from accounts.models import Customer


class MenuService:
    """
    UC06: Menu Access Service
    Handles menu filtering based on user type and allergies
    """
    
    @staticmethod
    def retrieve_active_dishes() -> List[Dish]:
        """
        UC06: retrieveActiveDishes()
        Get all active dishes from database
        """
        # Filter dishes where chef is active
        return list(Dish.objects.filter(
            chef_id__is_active=True
        ).select_related('chef_id'))
    
    @staticmethod
    def get_allergy_preferences(customer_id) -> List[str]:
        """
        UC06: getAllergyPreferences(customerId)
        Get customer's allergy list from CustomerAllergy model
        """
        try:
            # Get all allergens for this customer
            customer_allergies = CustomerAllergy.objects.filter(
                customer_id=customer_id
            ).select_related('allergen_id')
            
            return [ca.allergen_id.name.lower() for ca in customer_allergies]
        except Exception:
            return []
    
    @staticmethod
    def apply_user_type_filter(dishes: List[Dish], user_type: str) -> List[Dish]:
        """
        UC06: applyUserTypeFilter(dishes, userType)
        Filter dishes based on user access level:
        - VIP: sees all dishes (including special_for_vip)
        - Customer: sees non-VIP dishes only
        - Visitor: sees only non-VIP dishes
        """
        filtered_list = []
        
        for dish in dishes:
            if user_type == 'VIP':
                # VIP sees all dishes
                filtered_list.append(dish)
            elif user_type == 'Customer':
                # Customer sees non-VIP dishes
                if not dish.special_for_vip:
                    filtered_list.append(dish)
            elif user_type == 'Visitor':
                # Visitor sees only non-VIP dishes
                if not dish.special_for_vip:
                    filtered_list.append(dish)
        
        return filtered_list
    
    @staticmethod
    def get_dish_ingredients(dish) -> List[str]:
        """Get ingredients for a dish from DishIngredient model"""
        dish_ingredients = DishIngredient.objects.filter(
            dish=dish
        ).select_related('ingredient')
        
        return [di.ingredient.name.lower() for di in dish_ingredients]
    
    @staticmethod
    def get_dish_allergens(dish) -> List[str]:
        """Get allergens for a dish through ingredients"""
        dish_ingredients = DishIngredient.objects.filter(
            dish=dish
        ).select_related('ingredient', 'ingredient__allergens')
        
        allergens = []
        for di in dish_ingredients:
            if di.ingredient.allergens:
                allergens.append(di.ingredient.allergens.name.lower())
        
        return allergens
    
    @classmethod
    def apply_allergy_filter(cls, dishes: List[Dish], allergy_list: List[str]) -> List[Dish]:
        """
        UC06: applyAllergyFilter(dishes, allergyList)
        Remove dishes containing user's allergens
        """
        if not allergy_list:
            return dishes
        
        safe_dishes = []
        
        for dish in dishes:
            # Get allergens for this dish
            dish_allergens = cls.get_dish_allergens(dish)
            
            has_dangerous_allergen = False
            for user_allergen in allergy_list:
                if user_allergen.lower() in dish_allergens:
                    has_dangerous_allergen = True
                    break
            
            if not has_dangerous_allergen:
                safe_dishes.append(dish)
        
        return safe_dishes
    
    @staticmethod
    def sort_by_name(dishes: List[Dish]) -> List[Dish]:
        """
        UC06: sortByCategory(filteredDishes)
        Sort dishes by name (no category in current model)
        """
        return sorted(dishes, key=lambda d: d.name)
    
    @classmethod
    def display_menu(cls, customer_id, user_type: str) -> Tuple[bool, str, List[Dish]]:
        """
        UC06: displayMenu(customerId, userType)
        Main function to display filtered menu
        Returns: (success, message, dishes)
        """
        # Step 1: Retrieve all active dishes
        dishes = cls.retrieve_active_dishes()
        
        if not dishes:
            return (True, "No dishes available at this time", [])
        
        # Step 2: Apply user type filter
        filtered_dishes = cls.apply_user_type_filter(dishes, user_type)
        
        # Step 3: Apply allergy filter if customer has preferences
        if customer_id:
            customer_allergies = cls.get_allergy_preferences(customer_id)
            if customer_allergies:
                filtered_dishes = cls.apply_allergy_filter(filtered_dishes, customer_allergies)
        
        # Check if all dishes filtered out by allergies
        if not filtered_dishes:
            return (True, "No dishes match your allergy settings", [])
        
        # Step 4: Sort by name
        sorted_dishes = cls.sort_by_name(filtered_dishes)
        
        return (True, f"Found {len(sorted_dishes)} dishes", sorted_dishes)
    
    @staticmethod
    def get_user_type_from_customer(customer) -> str:
        """
        Get user type string for menu filtering
        Maps customer to UC06 categories
        """
        if not customer:
            return 'Visitor'
        
        # Check if customer is VIP (you may need to adjust based on your Customer model)
        if hasattr(customer, 'is_vip') and customer.is_vip:
            return 'VIP'
        elif hasattr(customer, 'user_type'):
            type_mapping = {
                'visitor': 'Visitor',
                'customer': 'Customer',
                'vip': 'VIP',
            }
            return type_mapping.get(customer.user_type, 'Customer')
        
        return 'Customer'
    
    @staticmethod
    def search_dishes(dishes: List[Dish], query: str) -> List[Dish]:
        """Search dishes by name or description"""
        if not query or not query.strip():
            return dishes
        
        query_lower = query.lower().strip()
        return [
            dish for dish in dishes
            if query_lower in dish.name.lower() or query_lower in dish.description.lower()
        ]