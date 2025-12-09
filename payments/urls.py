from django.urls import path
from . import views

urlpatterns = [
    path('deposit/',views.deposit_view,name='deposit')
]