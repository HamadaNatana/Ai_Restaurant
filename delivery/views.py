from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import OrderAssignment, Bids, Driver
from orders.models import Order
from accounts.models import Manager


# --------------------------------------------------------------------
# Helper: check if the logged-in user is a driver
# --------------------------------------------------------------------
def is_driver(user):
    return hasattr(user, "driver")


# --------------------------------------------------------------------
# UC18 — Driver Dashboard (See Assigned Deliveries)
# --------------------------------------------------------------------
@login_required
def driver_dashboard(request):
    """Driver sees all assigned deliveries."""
    if not is_driver(request.user):
        return HttpResponseForbidden("You are not a driver.")

    driver = request.user.driver

    assignments = OrderAssignment.objects.filter(
        driver_id=driver
    ).order_by("-created_at")

    return render(request, "delivery/driver_dashboard.html", {
        "driver": driver,
        "assignments": assignments
    })


# --------------------------------------------------------------------
# UC18 — Driver Marks Delivery as Delivered
# --------------------------------------------------------------------
@login_required
def mark_delivered(request, assignment_id):
    """Driver marks delivery as delivered."""
    if not is_driver(request.user):
        return HttpResponseForbidden("You are not a driver.")

    driver = request.user.driver

    assignment = get_object_or_404(
        OrderAssignment, assignment_id=assignment_id, driver_id=driver
    )

    if request.method == "POST":
        assignment.status = "DELIVERED"
        assignment.save()
        return redirect("delivery:driver_dashboard")

    return render(request, "delivery/confirm_delivered.html", {
        "assignment": assignment
    })


# --------------------------------------------------------------------
# UC17 — Driver Submits a Bid
# --------------------------------------------------------------------
@login_required
def submit_bid(request, order_id):
    """Driver submits a bid for an order."""
    if not is_driver(request.user):
        return HttpResponseForbidden("You are not a driver.")

    driver = request.user.driver
    order = get_object_or_404(Order, id=order_id)

    # Prevent duplicate bids
    if Bids.objects.filter(order_id=order, driver_id=driver).exists():
        return render(request, "delivery/bid_exists.html")

    if request.method == "POST":
        bid_price = request.POST.get("bid_price")

        Bids.objects.create(
            order_id=order,
            driver_id=driver,
            bid_price=bid_price
        )

        return redirect("delivery:driver_dashboard")

    return render(request, "delivery/bid_form.html", {"order": order})


# --------------------------------------------------------------------
# UC17 — Manager Views All Bids for an Order
# --------------------------------------------------------------------
@login_required
def view_bids(request, order_id):
    """Manager sees all bids for a specific order."""
    if not hasattr(request.user, "manager"):
        return HttpResponseForbidden("You are not a manager.")

    order = get_object_or_404(Order, id=order_id)
    bids = Bids.objects.filter(order_id=order).order_by("bid_price")  # lowest first

    return render(request, "delivery/manager_view_bids.html", {
        "order": order,
        "bids": bids
    })


# --------------------------------------------------------------------
# UC17 — Manager Assigns Driver After Reviewing Bids
# --------------------------------------------------------------------
@login_required
def assign_driver(request, order_id, driver_id):
    
    # ... inside assign_driver, after OrderAssignment.objects.create(...)

    # UPDATE THE MAIN ORDER STATUS
    order.status = 'delivering' # Or 'assigned' based on Order model choices
    order.save()

    return redirect('manager_dashboard')
    
    """Manager assigns a driver to an order."""
    if not hasattr(request.user, "manager"):
        return HttpResponseForbidden("You are not a manager.")

    manager = request.user.manager
    order = get_object_or_404(Order, id=order_id)
    driver = get_object_or_404(Driver, driver_id=driver_id)

    # Get the bid chosen
    bid = Bids.objects.filter(order_id=order, driver_id=driver).first()

    if request.method == "POST":
        memo = request.POST.get("memo", "")

        # Create the assignment
        OrderAssignment.objects.create(
            order_id=order,
            driver_id=driver,
            manager_id=manager,
            choosen_price=bid.bid_price,
            status="PENDING"
        )

        # optional: you can store memo later
        return redirect("/manager/dashboard/")

    return render(request, "delivery/manager_assign.html", {
        "order": order,
        "driver": driver,
        "bid": bid
    })

