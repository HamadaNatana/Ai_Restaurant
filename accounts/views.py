from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from hr.models import RegistrationApproval
from .forms import CustomerLoginForm
from .models import Customer

# UC1: Visitor registers to become a customer
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        address = request.POST.get("address", "")

        # basic validation
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "accounts/register.html")

        # blacklisted
        if Customer.objects.filter(username=username, is_blacklisted=True).exists():
            messages.error(request, "This account has been blocked and cannot register again.")
            return render(request, "accounts/register.html")

        # username already used
        if Customer.objects.filter(username=username).exists():
            messages.error(request, "This username is already in use.")
            return render(request, "accounts/register.html")

        # pending registration exists
        if RegistrationApproval.objects.filter(
            username=username,
            status=RegistrationApproval.STATUS_PENDING
        ).exists():
            messages.error(request, "There is already a pending registration for this username.")
            return render(request, "accounts/register.html")

        RegistrationApproval.objects.create(
            username=username,
            password_hash=password,   
            address=address,
        )

        messages.success(request, "Registration request submitted. A manager must approve it.")
        return redirect("login")

    return render(request, "accounts/register.html")

# UC3: Customer logs into their account
def login_view(request):
    if request.method == "POST":
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # check blacklist
            if user.is_blacklisted:
                messages.error(request, "Your account has been blocked and cannot log in.")
                return render(request, "accounts/login.html", {"form": form})

            login(request, user)

            # Build warning info (UC15)
            warning_msg = build_warning_message(user)
            if warning_msg:
                messages.warning(request, warning_msg)

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")  # change to dashboard/home url name
    else:
        form = CustomerLoginForm(request)

    return render(request, "accounts/login.html", {"form": form})

# UC15: Customer views their accumilated warnings when they log in
def build_warning_message(customer: Customer) -> str | None:
    if customer.warnings == 0:
        return None

    if customer.status == Customer.STATUS_VIP:
        return f"You currently have {customer.warnings} warning(s). VIPs are demoted after 2 warnings."
    else:
        return f"You currently have {customer.warnings} warning(s). Registered customers are removed after 3 warnings."