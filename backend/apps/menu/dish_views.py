"""
Dish Views - UC19: CRUD Dishes API Endpoints
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from menu.models import Dish
from .serializers import MenuDishSerializer
from .dish_services import DishService


@api_view(['POST'])
def create_dish(request):
    """UC19: addDish - Create new dish."""
    chef_id = request.data.get('chef_id')
    if not chef_id: return Response({'error': 'chef_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    success, message, dish = DishService.add_dish(chef_id=chef_id, dish_data=request.data)
    
    if success:
        return Response({'message': message, 'dish': MenuDishSerializer(dish).data}, status=status.HTTP_201_CREATED)
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
def update_dish(request, dish_id):
    """UC19: editDish - Update existing dish."""
    chef_id = request.data.get('chef_id')
    if not chef_id: return Response({'error': 'chef_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    success, message, dish = DishService.edit_dish(dish_id=dish_id, chef_id=chef_id, updated_data=request.data)
    
    if success:
        return Response({'message': message, 'dish': MenuDishSerializer(dish).data})
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_dish(request, dish_id):
    """UC19: deleteDish - Delete or mark dish unavailable."""
    chef_id = request.query_params.get('chef_id') or request.data.get('chef_id')
    if not chef_id: return Response({'error': 'chef_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = DishService.delete_dish(dish_id=dish_id, chef_id=chef_id)
    
    if success:
        # Success even if marked unavailable due to cart conflict
        return Response({'message': message})
    else:
        # Failure only if unauthorized or dish not found
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_chef_dishes(request):
    """Get all dishes by a specific chef."""
    chef_id = request.query_params.get('chef_id')
    if not chef_id: return Response({'error': 'chef_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    dishes = DishService.get_chef_dishes(chef_id)
    return Response(MenuDishSerializer(dishes, many=True).data)


@api_view(['POST'])
def toggle_dish_availability(request, dish_id):
    """Toggle dish availability status (UC19)."""
    chef_id = request.data.get('chef_id')
    if not chef_id: return Response({'error': 'chef_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    success, message, dish = DishService.toggle_dish_availability(dish_id=dish_id, chef_id=chef_id)
    
    if success:
        return Response({'message': message, 'dish': MenuDishSerializer(dish).data})
    else:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)