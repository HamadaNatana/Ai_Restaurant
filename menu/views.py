from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from django.db.models import Q
from .models import Dish, Allergen, AllergyPreference, Ingredient
from .serializers import MenuDishSerializer, AllergenSerializer

class DishViewSet(viewsets.ModelViewSet):
    """
    Unified Endpoint for Menu Operations (UC06, UC19, UC22).
    Standardizes to the 'David Format' (Class-Based ViewSet).
    """
    queryset = Dish.objects.all().select_related('chef')
    serializer_class = MenuDishSerializer

    # --- HELPER METHODS (Private) ---

    def _get_customer_allergen_names(self, customer_id):
        """Helper to fetch a list of allergen names for a customer (UC22)."""
        try:
            # Note: This checks the new AllergyPreference model Meherap built
            allergy_pref = AllergyPreference.objects.filter(customer__pk=customer_id).first()
            if allergy_pref:
                return allergy_pref.get_allergen_list()
            return []
        except Exception:
            return []

    def _apply_allergy_filter(self, queryset, customer_id):
        """Filter out dishes containing customer's allergens (Safety Mode)."""
        allergen_names = self._get_customer_allergen_names(customer_id)
        
        if not allergen_names:
            return queryset

        # Find ingredients that are linked to these allergens
        unsafe_ingredients = Ingredient.objects.filter(
            allergens__name__in=allergen_names
        )
        
        # Exclude dishes that contain these ingredients
        return queryset.exclude(ingredients__in=unsafe_ingredients)

    # --- MAIN LIST METHOD (The Menu) ---

    def list(self, request, *args, **kwargs):
        """
        UC06: Get filtered menu based on user type, search, and allergies.
        """
        user_type = request.query_params.get('user_type', 'Visitor')
        customer_id = request.query_params.get('customer_id')
        search_query = request.query_params.get('search', '')

        # 1. Start with Active Dishes (Active Chefs only)
        # Note: We filter is_active=True unless it's a Manager/Chef viewing
        queryset = self.get_queryset()
        if user_type not in ['Manager', 'Chef']:
            queryset = queryset.filter(is_active=True, chef_id__is_active=True)

        # 2. VIP Filter
        if user_type not in ['VIP', 'Chef', 'Manager']:
            # Regular users don't see VIP specials
            queryset = queryset.filter(special_for_vip=False)

        # 3. Search Filter
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )

        # 4. Allergy Filter (UC22)
        if customer_id and user_type != 'Visitor':
            queryset = self._apply_allergy_filter(queryset, customer_id)

        # Serialize
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": f"Menu loaded for {user_type}",
            "dishes": serializer.data
        })

    # --- CHEF OPERATIONS (UC19) ---

    def create(self, request, *args, **kwargs):
        """Chef adds a new dish."""
        # Standard DRF create logic
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        UC19: Soft Delete.
        Instead of removing the record, mark it as inactive.
        """
        dish = self.get_object()
        dish.is_active = False
        dish.save()
        return Response(
            {'message': 'Dish marked as unavailable (Soft Deleted)'}, 
            status=status.HTTP_200_OK
        )

    # --- EXTRA ACTIONS ---

    @decorators.action(detail=False, methods=['get'])
    def allergens(self, request):
        """Get all available allergens for the settings page."""
        allergens = Allergen.objects.all()
        serializer = AllergenSerializer(allergens, many=True)
        return Response(serializer.data)