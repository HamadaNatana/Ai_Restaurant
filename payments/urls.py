from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'transactions', views.PaymentViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]