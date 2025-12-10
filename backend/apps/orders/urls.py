from django.urls import path
from . import views

urlpatterns = [
    # UC07: Cart Operations 
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.get_cart, name='get_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<uuid:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    
    # UC07: Checkout 
    path('checkout/', views.checkout, name='checkout'),
    
    # Order History 
    path('detail/<uuid:order_id>/', views.get_order, name='get_order_detail'),
    path('my-orders/', views.get_customer_orders, name='get_customer_orders'),
]