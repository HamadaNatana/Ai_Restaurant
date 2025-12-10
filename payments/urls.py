from django.urls import path
from . import views

urlpatterns = [
    path("deposit/", views.DepositAPIView.as_view(), name="api-deposit"),
]