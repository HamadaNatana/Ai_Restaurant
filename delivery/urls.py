from django.urls import path
from . import views

app_name = "delivery"

urlpatterns = [
    # UC18 — Driver Dashboard & Delivery Update
    path("dashboard/", views.driver_dashboard, name="driver_dashboard"),
    path("delivered/<uuid:assignment_id>/", views.mark_delivered, name="mark_delivered"),

    # UC17 — Driver Bidding
    path("bid/<uuid:order_id>/", views.submit_bid, name="submit_bid"),

    # UC17 — Manager Views Bids + Assigns Driver
    path("manager/bids/<uuid:order_id>/", views.view_bids, name="view_bids"),
    path("manager/assign/<uuid:order_id>/<uuid:driver_id>/", views.assign_driver, name="assign_driver"),
]
