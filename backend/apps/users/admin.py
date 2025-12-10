from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    # Fields displayed in the list view
    list_display = ('username', 'email', 'status', 'balance', 'warnings', 'is_staff', 'is_blacklisted')
    
    # Fields that can be filtered
    list_filter = ('status', 'is_staff', 'is_blacklisted')
    
    # Fields to allow searching
    search_fields = ('username', 'email', 'customer_id')
    
    # Add custom fields to the user detail page (fieldsets)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('status', 'balance', 'warnings', 'is_blacklisted', 'order_count', 'total_spent', 'user_type', 'customer_id')}),
    )
    
    # Fields that cannot be edited on creation or after creation
    readonly_fields = ('customer_id',)