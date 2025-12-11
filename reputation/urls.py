from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views 

router = DefaultRouter()
router.register(r'feedback', views.FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('api/', include(router.urls)),
]