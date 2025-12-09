
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test,staff_member_required
from django.utils import timezone
from django.shortcuts import get_object_or_404
from accounts.models import Customer, Manager
from delivery.models import Driver
from menu.models import Chef
from reputation.models import WarningLog
from .models import RegistrationApproval


# Helper to check if user is a Manager
def is_manager(user):
    return user.is_authenticated and getattr(user, 'is_manager', False)

# --- UC 11: Manage HR (Hire, Fire, Pay) ---
#@user_passes_test(is_manager)
@staff_member_required(Manager)
def hire_employee_view(request):
    """Allows Manager to hire a new Chef or Driver"""
    if request.method == 'POST':
        role = request.POST.get(Chef,Driver) # 'chef' or 'driver'
        username = request.POST.get('username')
        password = request.POST.get('password')
        salary = request.POST.get('salary')
        
        # 1. Create the User account (simplified)
        # You would likely use a detailed RegistrationForm here in production
        #from django.contrib.auth import get_user_model
        #User = get_user_model()
        new_user = Manager.objects.create_user(username=username, password=password)
        
        # 2. Create the specific Role profile
        if role == Chef:
            Chef.objects.create(user=new_user, salary=salary, is_active=True) # , status='active'
        elif role == Driver:
            Driver.objects.create(user=new_user, salary=salary, is_active=True) # , status='available'
            
        messages.success(request, f"Hired new {role}: {username}")
        return redirect('manager_dashboard')
    
    return render(request, 'hr/hire_employee.html')

#@user_passes_test(is_manager)
@staff_member_required(Manager)
def fire_employee_view(request, employee_id, role):
    """Allows Manager to fire an employee (UC11 / BRR-2.8)"""
    if role == 'chef':
        employee = get_object_or_404(Chef, pk=employee_id)
    else:
        employee = get_object_or_404(Driver, pk=employee_id)
        
    # Logic: Set status to fired and deactivate login
    employee.is_active = False
    employee.user.is_active = False # Prevents login
    employee.save()
    employee.user.save()
    
    messages.warning(request, f"Fired employee {employee.user.username}")
    return redirect('manager_dashboard')

#@user_passes_test(is_manager)
@staff_member_required(Manager)
def update_salary_view(request, employee_id, role):
    """Allows Manager to raise or cut pay (UC11)"""
    if request.method == 'POST':
        new_salary = request.POST.get('salary')
        
        if role == 'chef':
            employee = get_object_or_404(Chef, pk=employee_id)
        else:
            employee = get_object_or_404(Driver, pk=employee_id)
            
        employee.salary = new_salary
        employee.save()
        messages.success(request, "Salary updated.")
        
    return redirect('manager_dashboard')


# --- UC 09: Manage Demotion/Promotion ---
@user_passes_test(is_manager)
def promote_demote_view(request, employee_id, role, action):
    """
    Handles Manager's decision to Promote (Bonus) or Demote (Pay Cut/Status Change)
    Triggered manually or by 'Pending Demotion' flags from the Reputation system.
    """
    if role == 'chef':
        employee = get_object_or_404(Chef, pk=employee_id)
    else:
        employee = get_object_or_404(Driver, pk=employee_id)

    if action == 'promote':
        # Example promotion: 10% raise or Bonus
        # In a real app, you might check if they have enough compliments here
        current_salary = float(employee.salary)
        employee.salary = current_salary * 1.10
        messages.success(request, f"Promoted {employee.user.username}. New salary: {employee.salary}")

    elif action == 'demote':
        # UC09: Routine Demotion
        # If they were 'Pending Demotion', we confirm it here
        if employee.status == 'pending_demotion':
            employee.demotion_count += 1 # Track for firing rule (BRR-2.8)
            
            # BRR-2.8: Fire if demoted twice
            if employee.demotion_count >= 2:
                return fire_employee_view(request, employee_id, role)
                
            employee.status = 'active' # Reset status but keep the strike
            
        # Apply pay cut
        current_salary = float(employee.salary)
        employee.salary = current_salary * 0.90
        messages.warning(request, f"Demoted {employee.user.username}. New salary: {employee.salary}")

    employee.save()
    return redirect('manager_dashboard')


# --- UC 10: Process Kicked/Quit Customers ---
#@user_passes_test(is_manager)
def close_customer_account_view(request, customer_id):
    """
    Handles closing a customer account (Quitting or Kicked Out).
    Clears deposit and Blacklists user if necessary.
    """
    customer = get_object_or_404(Customer, pk=customer_id)
    reason = request.POST.get('reason') # 'quit' or 'kicked'
    
    # 1. Clear Deposit (FR-1.2.10)
    refund_amount = customer.deposit_balance
    customer.deposit_balance = 0
    
    # 2. Close Account
    customer.user.is_active = False
    customer.status = 'deactivated'
    
    # 3. Blacklist (BRR-2.6)
    if reason == 'kicked':
        # Assuming you have a Blacklist model or field
        customer.is_blacklisted = True
        messages.error(request, f"Customer {customer.user.username} kicked and blacklisted.")
    else:
        messages.info(request, f"Customer {customer.user.username} account closed. Refund: ${refund_amount}")
        
    customer.save()
    customer.user.save()
    
    return redirect('manager_dashboard')

# --- ADD THIS TO THE BOTTOM OF hr/views.py ---
from reputation.models import Feedback

@user_passes_test(is_manager)
def dashboard_view(request):
    """
    Renders the Manager Dashboard with all necessary data.
    """
    # FIX: Use 'is_active' instead of 'status' based on your error message
    chefs = Chef.objects.filter(is_active=True)
    
    # Assuming Driver likely follows the same pattern:
    drivers = Driver.objects.filter(is_active=True)
    
    pending_feedback = Feedback.objects.filter(status='pending')
    
    context = {
        'chefs': chefs,
        'drivers': drivers,
        'pending_feedback': pending_feedback,
    }
    return render(request, 'hr/manager_dashboard.html', context)

#UC2: Manager registers new customers
@staff_member_required
def pending_registrations_view(request):
    pending = RegistrationApproval.objects.filter(
        status=RegistrationApproval.STATUS_PENDING
    ).order_by("created_at")
    return render(request, "hr/pending_registrations.html", {"pending": pending})


@staff_member_required
def approve_registration_view(request, pk):
    req = RegistrationApproval.objects.filter(pk=pk).first()
    if not req or req.status != RegistrationApproval.STATUS_PENDING:
        messages.error(request, "Registration request not found or not pending.")
        return redirect("pending_registrations")

    # still blacklisted
    if Customer.objects.filter(username=req.username, is_blacklisted=True).exists():
        req.status = RegistrationApproval.STATUS_REJECTED
        req.rejection_reason = "User is blacklisted."
        req.processed_at = timezone.now()
        req.save()
        messages.error(request, "Applicant is blacklisted and cannot be approved.")
        return redirect("pending_registrations")

    # username conflict
    if Customer.objects.filter(username=req.username).exists():
        req.status = RegistrationApproval.STATUS_REJECTED
        req.rejection_reason = "Username already taken."
        req.processed_at = timezone.now()
        req.save()
        messages.error(request, "Username already exists.")
        return redirect("pending_registrations")

    # create Customer (using AbstractUser)
    user = Customer(username=req.username)
    user.set_password(req.password)
    user.save()

    # optional:
    # user.address = req.address
    # user.save()

    req.status = RegistrationApproval.STATUS_APPROVED
    req.processed_at = timezone.now()
    req.save()

    messages.success(request, f"Customer '{user.username}' created and approved.")
    return redirect("pending_registrations")


@staff_member_required
def reject_registration_view(request, pk):
    req = RegistrationApproval.objects.filter(pk=pk).first()
    if not req or req.status != RegistrationApproval.STATUS_PENDING:
        messages.error(request, "Registration request not found or not pending.")
        return redirect("pending_registrations")

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        req.status = RegistrationApproval.STATUS_REJECTED
        req.rejection_reason = reason
        req.processed_at = timezone.now()
        req.save()
        messages.success(request, "Registration request rejected.")
        return redirect("pending_registrations")

    return render(request, "hr/reject_registration.html", {"req": req})

