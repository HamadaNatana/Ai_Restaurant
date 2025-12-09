from django.urls import path
from . import views

urlpatterns = [
    # UC 11: Hiring
    path('hire/', views.hire_employee_view, name='hire_employee'),
    
    # UC 11: Firing & Pay
    path('fire/<int:employee_id>/<str:role>/', views.fire_employee_view, name='fire_employee'),
    path('salary/<int:employee_id>/<str:role>/', views.update_salary_view, name='update_salary'),
    
    # UC 09: Promotion / Demotion
    path('status/<int:employee_id>/<str:role>/<str:action>/', views.promote_demote_view, name='promote_demote'),
    
    # UC 10: Closing Accounts (Kick/Quit)
    path('close-account/<int:customer_id>/', views.close_customer_account_view, name='close_customer_account'),
]
