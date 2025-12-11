from typing import Tuple, List, Dict, Optional
from django.db import transaction
from django.db.models import Q
from .models import Dish, Chef, Allergen, AllergyPreference, Ingredient

# Import Order models lazily inside methods if needed to avoid circular imports, 
# or at top if your structure allows.
from orders.models import Order, OrderItem 

class MenuService:
    """
    Unified Service Layer for Menu App.
    Combines:
      - Reader Logic (UC06: Displaying/Filtering Menu)
      - Writer Logic (UC19: Managing Dishes/Ingredients)
    """

    # =========================================================================
    #  SECTION 1: READER LOGIC (For Customers/Visitors - UC06)
    # =========================================================================

    @staticmethod
    def display_menu(customer_id, user_type: str) -> Tuple[bool, str, List[Dish]]:
        """
        Main entry point for fetching the menu.
        Applies Availability -> User Type Filter -> Allergy Safety Filter.
        """
        # 1. Retrieve all active dishes (base pool)
        # Note: We fetch ALL dishes initially, then filter based on user_type below
        # to allow Chefs/Managers to see inactive dishes if needed.
        dishes = Dish.objects.all().select_related('chef').prefetch_related('ingredient')

        # 2. Apply User Type Visibility Rules
        # Visitor/Customer: Only see Active Dishes & Active Chefs
        if user_type not in ['Manager', 'Chef']:
            dishes = dishes.filter(is_active=True, chef__is_active=True)
        
        # Visitor: Cannot see VIP specials
        if user_type == 'Visitor':
            dishes = dishes.filter(special_for_vip=False)
        
        # 3. Apply Allergy Safety Filter (The "Safety Mode")
        if customer_id and user_type != 'Visitor':
            dishes = MenuService._apply_allergy_filter(dishes, customer_id)

        # 4. Sort by Name
        final_list = dishes.order_by('name')

        if not final_list.exists():
            return True, "No dishes available.", []

        return True, f"Found {final_list.count()} dishes", final_list

    @staticmethod
    def _apply_allergy_filter(queryset, customer_id):
        """Helper to exclude dishes containing customer's allergens."""
        try:
            pref = AllergyPreference.objects.filter(customer__pk=customer_id).first()
            if not pref:
                return queryset
            
            # Find ingredients that match the customer's allergens
            # (Assuming Allergen model link is set up correctly)
            unsafe_ingredients = Ingredient.objects.filter(allergens__in=pref.allergens.all())
            return queryset.exclude(ingredient__in=unsafe_ingredients)
        except Exception:
            return queryset

    # =========================================================================
    #  SECTION 2: WRITER LOGIC (For Chefs/Managers - UC19)
    # =========================================================================

    @staticmethod
    def add_dish(chef_id, dish_data: Dict) -> Tuple[bool, str, Optional[Dish]]:
        """
        Creates a new dish with validation and ingredient handling.
        """
        # 1. Validation
        is_valid, error_msg = MenuService._validate_dish_data(dish_data)
        if not is_valid: return False, error_msg, None

        if not MenuService._check_dish_name_unique(dish_data['name']):
            return False, "Dish name already exists", None

        # 2. Check Chef Status
        try:
            # Handle case where chef_id might be the Chef object itself or an ID
            if hasattr(chef_id, 'pk'):
                chef = chef_id
            else:
                chef = Chef.objects.get(pk=chef_id)
                
            if not chef.is_active:
                return False, "Chef account is not active", None
        except Chef.DoesNotExist:
            return False, "Chef not found", None

        # 3. Create Dish
        try:
            with transaction.atomic():
                dish = Dish.objects.create(
                    name=dish_data['name'].strip(),
                    price=dish_data['price'],
                    description=dish_data.get('description', '').strip(),
                    chef=chef, # Using 'chef' field name
                    special_for_vip=dish_data.get('special_for_vip', False),
                    is_active=True
                )
                
                # Handle Image if present
                if 'picture' in dish_data:
                    dish.picture = dish_data['picture']
                    dish.save()

                # Handle Ingredients
                if 'ingredients' in dish_data:
                    MenuService._add_ingredients_to_dish(dish, dish_data['ingredients'])
                
                return True, "Dish created successfully", dish
                
        except Exception as e:
            return False, f"Failed to create dish: {str(e)}", None

    @staticmethod
    def delete_dish(dish_id, chef_id) -> Tuple[bool, str]:
        """
        Handles Safe Deletion (Soft Delete if in active carts).
        """
        try:
            dish = Dish.objects.get(pk=dish_id)
        except Dish.DoesNotExist:
            return False, "Dish not found"

        # Check Ownership (Optional depending on your auth strictness)
        if str(dish.chef.pk) != str(chef_id):
            return False, "Unauthorized: You can only delete your own dishes"

        # Check if anyone is currently ordering it
        is_in_cart = OrderItem.objects.filter(
            dish=dish, 
            order__status='pending'
        ).exists()

        if is_in_cart:
            # Soft Delete
            dish.is_active = False
            dish.save()
            return True, "Dish marked as unavailable (Soft Deleted) because it is in active carts."
        else:
            # Hard Delete
            dish.delete()
            return True, "Dish permanently deleted."

    # =========================================================================
    #  SECTION 3: HELPER METHODS (Private/Internal)
    # =========================================================================

    @staticmethod
    def _validate_dish_data(data: Dict) -> Tuple[bool, str]:
        if not data.get('name'): return False, "Name is required"
        try:
            price = float(data.get('price', 0))
            if price <= 0: return False, "Price must be positive"
        except ValueError:
            return False, "Invalid price format"
        return True, ""

    @staticmethod
    def _check_dish_name_unique(name: str) -> bool:
        return not Dish.objects.filter(name__iexact=name.strip()).exists()

    @staticmethod
    def _add_ingredients_to_dish(dish, ingredients_input):
        """
        Parses a string "Tomato, Basil" OR a list ['Tomato', 'Basil']
        and links/creates ingredients.
        """
        if isinstance(ingredients_input, str):
            names = [x.strip() for x in ingredients_input.split(',') if x.strip()]
        elif isinstance(ingredients_input, list):
            names = [str(x).strip() for x in ingredients_input if x]
        else:
            return

        for name in names:
            # Get or Create the Ingredient
            ingredient_obj, _ = Ingredient.objects.get_or_create(
                name__iexact=name,
                defaults={'name': name}
            )
            # Link it to the Dish
            dish.ingredient.add(ingredient_obj)