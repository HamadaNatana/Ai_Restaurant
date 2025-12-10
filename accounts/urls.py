from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)), 
    path("register/", views.RegistrationAPIView.as_view(), name="api-register"),
    path("login/", views.LoginAPIView.as_view(), name="api-login"),
]