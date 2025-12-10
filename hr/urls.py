from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('api/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    
    # Actions (Using UUIDs)
    path('api/chef/<uuid:pk>/', views.manage_chef, name='manage_chef'),
    path('api/driver/<uuid:pk>/', views.manage_driver, name='manage_driver'),
    path('api/customer/kick/<uuid:pk>/', views.kick_customer, name='kick_customer'),
]