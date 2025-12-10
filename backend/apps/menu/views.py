"""
Menu Views - UC06: Menu Access API Endpoints
Handles filtering based on user type, search, and allergies.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q # For complex filtering
from menu.models import Dish, Chef, Allergen, DishIngredient
# from accounts.models import Customer # Assuming Customer import
from orders.models import Customer as CustomerPlaceholder # Use placeholder for type-checking

from .serializers import MenuDishSerializer, AllergenSerializer, MenuResponseSerializer


# --- Helper Functions for Filtering ---
def _get_customer_allergen_names(customer_id):
    """Helper to fetch a list of allergen names for a customer (UC22)."""
    # NOTE: This requires the Customer model to be correctly linked to CustomerAllergy
    try:
        # Placeholder assuming Customer model has a user object with a 'user_type' attribute
        customer = CustomerPlaceholder.objects.get(customer_id=customer_id)
        # Assuming Customer has a relation to CustomerAllergy which links to Allergen
        # Replace this with actual Customer/CustomerAllergy query if available
        
        # --- Simplified Placeholder Return ---
        return [] 
    except CustomerPlaceholder.DoesNotExist:
        return []

def _apply_user_type_filter(dishes, user_type):
    """Filter dishes based on VIP status, as per UC06/UC05 rules."""
    # Start with only active dishes from active chefs
    dishes = dishes.filter(is_active=True, chef_id__is_active=True)
    
    if user_type in ['VIP', 'Chef', 'Manager']:
        # VIPs/Chefs/Managers see all dishes including VIP-only
        return dishes
    else:
        # Customers/Visitors see only non-VIP dishes
        return dishes.filter(special_for_vip=False)

def _apply_allergy_filter(dishes, customer_id):
    """Filter out dishes that contain a customer's registered allergens (UC22)."""
    customer_allergen_names = _get_customer_allergen_names(customer_id)
    
    if not customer_allergen_names:
        return dishes

    # Find the IDs of all ingredients linked to the customer's allergens
    allergic_ingredient_ids = Ingredient.objects.filter(
        allergens__name__in=customer_allergen_names
    ).values_list('ingredient_id', flat=True)
    
    # Find the IDs of dishes that contain any of these allergic ingredients
    dishes_to_exclude = DishIngredient.objects.filter(
        ingredient_id__in=allergic_ingredient_ids
    ).values_list('dish_id', flat=True)
    
    # Exclude those dishes
    return dishes.exclude(dish_id__in=dishes_to_exclude)

# --- API Endpoints ---
@api_view(['GET'])
def get_menu(request):
    """
    UC06: Get filtered menu based on user type, search, and allergies.
    """
    user_type = request.query_params.get('user_type', 'Visitor')
    customer_id = request.query_params.get('customer_id')
    search = request.query_params.get('search')
    # category = request.query_params.get('category') # Not implemented yet

    # 1. Retrieve all dishes (optimizing for later filters)
    dishes = Dish.objects.all().select_related('chef_id')
    
    # 2. Apply user-type filter (VIP access and active status)
    dishes = _apply_user_type_filter(dishes, user_type)
    
    # 3. Apply search filter
    if search:
        # Search by dish name OR description (simple search)
        dishes = dishes.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # 4. Apply allergy filter (UC22)
    if customer_id and user_type != 'Visitor':
        dishes = _apply_allergy_filter(dishes, customer_id)
        
    # 5. Check for empty results (Exception 1/3)
    if not dishes.exists():
        message = "No dishes found matching your filters."
        # Refine message if empty due to allergy filter
        if customer_id and user_type != 'Visitor':
            message = "No dishes match your allergy settings."
            
        return Response({
            'success': True,
            'message': message,
            'total_dishes': 0,
            'dishes': []
        })

    # 6. Serialize and return
    serializer = MenuResponseSerializer(data={
        'success': True,
        'message': "Menu loaded successfully.",
        'total_dishes': dishes.count(),
        'user_type': user_type,
        'dishes': MenuDishSerializer(dishes, many=True).data 
    })
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_dish_detail(request, dish_id):
    """UC06: Get detailed dish information."""
    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        return Response({'error': 'Dish not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # In a real system, you'd re-validate access/allergy here.
    
    serializer = MenuDishSerializer(dish)
    return Response(serializer.data)

@api_view(['GET'])
def get_allergens(request):
    """Get all available allergens (UC22)."""
    allergens = Allergen.objects.all()
    serializer = AllergenSerializer(allergens, many=True)
    return Response(serializer.data)