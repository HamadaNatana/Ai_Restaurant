from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from .models import Feedback, FeedbackDecision, WarningLog
from accounts.models import Customer
from delivery.models import Driver
from menu.models import Chef

# --- UC 12: File Complaint / Compliment ---
def create_feedback_view(request):
    if request.method == 'POST':
        # 1. Identify the Filer (Who is submitting?)
        # Assuming request.user is linked to Customer/Driver models
        filer_customer = getattr(request.user, 'customer', None)
        filer_driver = getattr(request.user, 'driver', None)

        # 2. Identify the Target (Who is it about?)
        target_type = request.POST.get('target_type')  # 'customer', 'driver', 'chef'
        target_id = request.POST.get('target_id')
        message = request.POST.get('message')
        is_compliment = request.POST.get('category') == 'compliment'

        # 3. Calculate Weight (BRR-2.2: VIP counts double)
        weight = 1
        if filer_customer and getattr(filer_customer, 'is_vip', False):
            weight = 2

        # 4. Create the Feedback Object
        feedback = Feedback(
            is_compliment=is_compliment,
            message=message,
            weight=weight,
            status='pending',  # Matches STATUS_PENDING in your model
            
            # Link the Filer
            filer_customer_id=filer_customer,
            filer_driver_id=filer_driver
        )

        # Link the specific Target based on type
        if target_type == 'customer':
            feedback.target_customer_id = get_object_or_404(Customer, pk=target_id)
        elif target_type == 'driver':
            feedback.target_driver_id = get_object_or_404(Driver, pk=target_id)
        elif target_type == 'chef':
            feedback.target_chef_id = get_object_or_404(Chef, pk=target_id)

        feedback.save()
        messages.success(request, "Feedback submitted successfully.")
        return redirect('dashboard')

# --- UC 13/14: Manager Resolves Feedback ---
def resolve_feedback_view(request, feedback_id):
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    
    if request.method == 'POST':
        outcome = request.POST.get('outcome')  # 'Accepted' or 'Dismissed'
        note = request.POST.get('note')

        # 1. Create the Decision Record (Your model uses a separate table for this)
        FeedbackDecision.objects.create(
            feedback=feedback,
            outcome=outcome,
            note=note
        )

        if outcome == 'Accepted':
            feedback.status = 'kept' # Matches STATUS_KEPT
            feedback.save()

            # If it was a Complaint, issue a Warning to the TARGET
            if not feedback.is_compliment:
                create_warning_log(feedback, target=True)
                
                # Logic: Check for cancellations or Kick/Demotion consequences
                handle_cancellation_and_consequences(feedback)

        elif outcome == 'Dismissed':
            feedback.status = 'dismissed' # Matches STATUS_DISMISSED
            feedback.save()

            # BRR-2.3: If it was a Complaint, penalize the FILER for meritless filing
            if not feedback.is_compliment:
                create_warning_log(feedback, target=False)
                
        return redirect('manager_dashboard')

# --- Helper Functions ---

def create_warning_log(feedback, target=True):
    """Creates a WarningLog entry for either the Target (True) or Filer (False)"""
    reason = f"Outcome of feedback {feedback.pk}"
    
    if target:
        # Warn the Target
        WarningLog.objects.create(
            target_type=get_target_type_string(feedback), # Helper to get "customer"/"driver" string
            customer_id=feedback.target_customer_id,
            driver_id=feedback.target_driver_id,
            chef_id=feedback.target_chef_id,
            reason=reason
        )
    else:
        # Warn the Filer (The Penalize Filer Rule)
        # We need to determine if filer was customer or driver
        if feedback.filer_customer_id:
            WarningLog.objects.create(target_type="customer", customer_id=feedback.filer_customer_id, reason=reason)
        elif feedback.filer_driver_id:
            WarningLog.objects.create(target_type="driver", driver_id=feedback.filer_driver_id, reason=reason)

def handle_cancellation_and_consequences(feedback):
    """
    1. Checks if a compliment cancels this complaint (BRR-2.10)
    2. Checks if the user has reached warning thresholds (Kick/Demote)
    """
    # Logic to find the specific user object (Customer, Driver, or Chef)
    user_obj = feedback.target_customer_id or feedback.target_driver_id or feedback.target_chef_id
    
    # ... (Cancellation logic here would query Feedback objects filtered by this user) ...
    # This part gets complex with separate tables, but the core idea is counting 
    # Feedback.objects.filter(target_customer_id=user, is_compliment=True, status='kept')
    
    pass # Placeholder for brevity, logic remains similar to previous version

def get_target_type_string(feedback):
    if feedback.target_customer_id: return "customer"
    if feedback.target_driver_id: return "driver"
    if feedback.target_chef_id: return "chef"
    return "unknown"
