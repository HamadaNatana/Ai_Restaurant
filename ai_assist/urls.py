from django.urls import path
from . import views

urlpatterns = [
    path('api/ask/', views.get_ai_answer, name='get_ai_answer'),
    path('api/rate/', views.rate_answer, name='rate_answer'),
]