from django.urls import path
from . import views, dish_views

urlpatterns = [
    # UC06: Menu Access for Customers/Visitors
    path('', views.get_menu, name='get_menu'), # Matches path('api/menu/', include('apps.menu.urls'))
    path('allergens/', views.get_allergens, name='get_allergens'),
    path('dish/<uuid:dish_id>/', views.get_dish_detail, name='get_dish_detail'),

    # UC19: Chef Dishes CRUD
    path('dishes/', dish_views.create_dish, name='create_dish'),
    path('dishes/by-chef/', dish_views.get_chef_dishes, name='get_chef_dishes'),
    path('dishes/<uuid:dish_id>/', dish_views.update_dish, name='update_dish'),
    path('dishes/<uuid:dish_id>/delete/', dish_views.delete_dish, name='delete_dish'),
    path('dishes/<uuid:dish_id>/toggle/', dish_views.toggle_dish_availability, name='toggle_dish_availability'),
]
