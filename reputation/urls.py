from django.urls import path
from . import views

urlpatterns = [
    # 1. Create Complaint/Compliment (Frontend uses this)
    path('api/create/', views.create_feedback, name='create_feedback'),
    
    # 2. Manager Dashboard: Get list of pending disputes
    path('api/pending/', views.get_pending_feedback, name='get_pending_feedback'),
    
    # 3. Manager Action: Resolve a dispute (Accept/Dismiss)
    # Uses uuid because your Feedback model uses UUIDField
    path('api/resolve/<uuid:pk>/', views.resolve_feedback, name='resolve_feedback'),
]