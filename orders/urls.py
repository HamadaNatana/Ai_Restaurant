from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# CHANGE: Use r'' (empty string) instead of r'orders'
router.register(r'', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]