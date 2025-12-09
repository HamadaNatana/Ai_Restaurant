from django.urls import path
from . import views

urlpatterns = [
    # UC 12: The form action for submitting feedback
    path('create/', views.create_feedback_view, name='create_feedback'),
    
    # UC 13/14: The manager clicking "Accept" or "Dismiss" on a complaint
    path('resolve/<uuid:feedback_id>/', views.resolve_feedback_view, name='resolve_feedback'),
]