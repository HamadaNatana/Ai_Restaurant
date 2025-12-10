from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from menu.models import Dish, Chef, Allergen, DishIngredient, Ingredient, CustomerAllergy
from accounts.models import Customer
from .serializers import MenuDishSerializer, AllergenSerializer, MenuResponseSerializer

# --- Helper Functions for Filtering ---

def _get_customer_allergen_names(customer_id):
  
    try:

        customer = Customer.objects.get(customer_id=customer_id)
        allergen_names = CustomerAllergy.objects.filter(
            customer_id=customer_id
        ).values_list('allergen__name', flat=True)
        
        return list(allergen_names)
        
    except Customer.DoesNotExist:
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

    # Find dishes that contain any of these ingredients
    dishes_to_exclude = DishIngredient.objects.filter(
        ingredient_id__in=allergic_ingredient_ids
    ).values_list('dish_id', flat=True)

    # Return only dishes NOT in that list
    return dishes.exclude(dish_id__in=dishes_to_exclude)


# --- UC06: CUSTOMER API ENDPOINTS (READ ONLY) ---

@api_view(['GET'])
def get_menu(request):
    """
    UC06: Get filtered menu based on user type, search, and allergies.
    """
    user_type = request.query_params.get('user_type', 'Visitor')
    customer_id = request.query_params.get('customer_id')
    search = request.query_params.get('search')
    
    # 1. Retrieve all dishes (optimizing for later filters)
    dishes = Dish.objects.all().select_related('chef_id')

    # 2. Apply user-type filter (VIP access and active status)
    dishes = _apply_user_type_filter(dishes, user_type)

    # 3. Apply search filter
    if search:
        dishes = dishes.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # 4. Apply allergy filter (UC22)
    if customer_id and user_type != 'Visitor':
        dishes = _apply_allergy_filter(dishes, customer_id)

    # 5. Check for empty results
    if not dishes.exists():
        message = "No dishes found matching your filters."
        # Refine message if empty due to allergy filter
        if customer_id and user_type != 'Visitor':
            # Check if dishes existed BEFORE allergy filter
            pre_allergy_count = _apply_user_type_filter(Dish.objects.all(), user_type).count()
            if pre_allergy_count > 0:
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
    
    # We validate=False here or skip validation since we constructed the dict manually
    # Or simply return the dict directly if MenuResponseSerializer causes issues
    return Response(serializer.initial_data)

@api_view(['GET'])
def get_dish_detail(request, dish_id):
    """UC06: Get detailed dish information."""
    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        return Response({'error': 'Dish not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = MenuDishSerializer(dish)
    return Response(serializer.data)

@api_view(['GET'])
def get_allergens(request):
    """Get all available allergens (UC22)."""
    allergens = Allergen.objects.all()
    serializer = AllergenSerializer(allergens, many=True)
    return Response(serializer.data)


# --- UC19: CHEF MENU MANAGEMENT (CREATE, UPDATE, DELETE) ---
# These were missing from your teammate's file.

@api_view(['POST'])
def create_dish(request):
    """
    UC19: Allow a Chef to add a new dish.
    """
    serializer = MenuDishSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def update_dish(request, dish_id):
    """
    UC19: Allow a Chef to edit an existing dish.
    """
    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        return Response({'error': 'Dish not found'}, status=status.HTTP_404_NOT_FOUND)
        
    serializer = MenuDishSerializer(dish, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_dish(request, dish_id):
    """
    UC19: Allow a Chef to remove a dish.
    IMPLEMENTS SAFE DELETE: Marks as inactive instead of deleting DB record.
    """
    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        return Response({'error': 'Dish not found'}, status=status.HTTP_404_NOT_FOUND)

    # Soft Delete Logic (Business Rule: Don't break active carts)
    dish.is_active = False
    dish.save()
    
    return Response({'message': 'Dish marked as unavailable (Soft Deleted)'}, status=status.HTTP_200_OK)