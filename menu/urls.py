from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dishes', views.DishViewSet, basename='dish')
router.register(r'chefs',views.ChefViewSet, basename='chef')
urlpatterns = [
    path('', include(router.urls)),
]