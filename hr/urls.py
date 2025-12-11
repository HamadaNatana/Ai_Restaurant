from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'registrations', views.RegistrationApprovalViewSet, basename='registration-approval')
router.register(r'actions', views.HRActionViewSet, basename='hr-action')
router.register(r'memos', views.AssignmentMemoViewSet, basename='assignment-memo')

urlpatterns = [
    path('', include(router.urls)),
]