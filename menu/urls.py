from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dishes', views.DishViewSet, basename='dish')

urlpatterns = [
    path('', include(router.urls)),
]