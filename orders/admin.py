from django.contrib import admin
from .models import Order, OrderItem

admin.site.register(Order)
admin.site.register(OrderItem)
'''
# Optional: Improve readability of OrderItems within the Order Admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['dish_id'] # Use raw_id_fields for UUIDs/FKs for better performance
    readonly_fields = ['unit_price'] # Price is set at time of order

# Register Order with inline OrderItems
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_id', 'status', 'total', 'created_at']
    list_filter = ['status', 'vip_discount_applied', 'free_delivery_applied']
    search_fields = ['order_id', 'customer_id__customer_id']
    inlines = [OrderItemInline]

# OrderItem is accessed via OrderAdmin, so direct registration is optional.
'''