"""
URL configuration for restaurant project.
"""

from django.contrib import admin
from django.urls import path, include

# Streamlit redirect views
from restaurant.frontend_redirects import (
    ai_chat_redirect,
    discussion_redirect,
    allergy_redirect
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Django apps
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('accounts.urls')),   
    path('reputation/', include('reputation.urls')),
    path('hr/', include('hr.urls')),
    path('payments/', include('payments.urls')),
    path('reputation/', include('reputation.urls')),
    path("ai/chat/", ai_chat_redirect, name="ai_chat"),
    path("discussion/", discussion_redirect, name="discussion"),
    path("allergy/", allergy_redirect, name="allergy"),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),

]
