from rest_framework import viewsets, status, decorators, permissions, filters
from rest_framework.response import Response
from .models import Dish, Allergen
from .serializers import MenuDishSerializer, AllergenSerializer
from .services import MenuService

class DishViewSet(viewsets.ModelViewSet):
    """
    Unified Endpoint for Menu Operations (UC06, UC19).
    Combines all 'dish_views.py' logic into one standard ViewSet.
    """
    queryset = Dish.objects.all().select_related('chef')
    serializer_class = MenuDishSerializer
    permission_classes = [permissions.AllowAny] 
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def list(self, request, *args, **kwargs):
        """UC06: Display Menu (Read)"""
        user_type = request.query_params.get('user_type', 'Visitor')
        customer_id = request.query_params.get('customer_id')

        success, message, dishes = MenuService.display_menu(customer_id, user_type)
        
        serializer = self.get_serializer(dishes, many=True)
        return Response({
            "success": success,
            "message": message,
            "dishes": serializer.data
        })

    def create(self, request, *args, **kwargs):
        """UC19: Add Dish"""
        chef_id = request.data.get('chef_id')
        success, message, dish = MenuService.add_dish(chef_id, request.data)

        if success:
            return Response(
                {"success": True, "message": message, "dish": MenuDishSerializer(dish).data},
                status=status.HTTP_201_CREATED
            )
        return Response({"success": False, "error": message}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """UC19: Update Dish (Replaces update_dish from dish_views)"""
        dish = self.get_object()
        # In real app: chef_id = request.user.chef.pk
        chef_id = request.data.get('chef_id') 
        
        # We need to add an 'edit_dish' method to services.py if you want full logic,
        # otherwise we can use standard serializer save here.
        # For now, let's assume simple update or add edit_dish to MenuService if needed.
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """UC19: Safe Delete"""
        dish = self.get_object()
        chef_id = dish.chef.pk 
        success, message = MenuService.delete_dish(dish.pk, chef_id)

        if success:
            return Response({"success": True, "message": message}, status=status.HTTP_200_OK)
        return Response({"success": False, "error": message}, status=status.HTTP_400_BAD_REQUEST)

    # --- EXTRA ACTIONS (Moved from dish_views.py) ---

    @decorators.action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """
        UC19: Toggle dish status (Replaces toggle_dish_availability)
        """
        dish = self.get_object()
        # Toggle logic
        dish.is_active = not dish.is_active
        dish.save()
        
        status_msg = "available" if dish.is_active else "unavailable"
        return Response({
            "success": True, 
            "message": f"Dish marked as {status_msg}", 
            "dish": MenuDishSerializer(dish).data
        })

    @decorators.action(detail=False, methods=['get'])
    def chef_dishes(self, request):
        """
        Get dishes for a specific chef (Replaces get_chef_dishes)
        Usage: /menu/dishes/chef_dishes/?chef_id=...
        """
        chef_id = request.query_params.get('chef_id')
        if not chef_id:
            return Response({"error": "chef_id required"}, status=status.HTTP_400_BAD_REQUEST)
            
        dishes = self.get_queryset().filter(chef__pk=chef_id)
        serializer = self.get_serializer(dishes, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'])
    def allergens(self, request):
        """Helper for Settings page"""
        allergens = Allergen.objects.all()
        serializer = AllergenSerializer(allergens, many=True)
        return Response(serializer.data)