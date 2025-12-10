from django.contrib import admin
from .models import Driver, Bids, OrderAssignment
admin.site.register(Driver)
admin.site.register(Bids)
admin.site.register(OrderAssignment)
'''
@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("driver_id", "user", "is_active", "warnings", "demotion_count", "created_at")
    search_fields = ("user__username",)

@admin.register(Bids)
class BidsAdmin(admin.ModelAdmin):
    list_display = ("bid_id", "order_id", "driver_id", "bid_price", "created_at")
    search_fields = ("order_id__id", "driver_id__user__username")

@admin.register(OrderAssignment)
class OrderAssignmentAdmin(admin.ModelAdmin):
    list_display = ("assignment_id", "order_id", "driver_id", "manager_id", "status", "choosen_price", "created_at")
    list_filter = ("status",)
    search_fields = ("order_id__id", "driver_id__user__username", "manager_id__user__username")
'''