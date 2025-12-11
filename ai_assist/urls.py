from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'chat', views.AIChatViewSet, basename='chat')
router.register(r'flags', views.ManagerKBViewSet, basename='kb-flags')

urlpatterns = [
    path('', include(router.urls)),
]