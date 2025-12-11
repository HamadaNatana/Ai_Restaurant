from django.urls import path
from .views import CartAPIView, CartItemAPIView, CheckoutAPIView

urlpatterns = [
    # 1. Main Cart Endpoint (GET to view, POST to add)
    path('api/cart/', CartAPIView.as_view(), name='cart-api'),

    # 2. Cart Item Management (PUT to update quantity, DELETE to remove)
    path('api/cart/item/', CartItemAPIView.as_view(), name='cart-item-api'),

    # 3. Checkout Endpoint (POST to pay)
    path('api/checkout/', CheckoutAPIView.as_view(), name='checkout-api'),
]