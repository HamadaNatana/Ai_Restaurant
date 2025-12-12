from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'drivers', views.DriverViewSet, basename='driver')
router.register(r'bids',views.BidViewSet,basename='bid')

urlpatterns = [
    path('', include(router.urls)),
]