from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import F
from .models import Feedback
from .serializers import FeedbackSerializer
from accounts.models import Customer
from delivery.models import Driver 

# 1. FILE A COMPLAINT/COMPLIMENT (Used by Streamlit)
@api_view(['POST'])
def create_feedback(request):
    data = request.data
    
    # We need to manually map the IDs since we have custom FKs
    feedback_data = {
        'message': data.get('message'),
        'is_compliment': data.get('is_compliment', False),
        # Default status is pending
        'status': 'pending' 
    }
    
    # LOGIC 1: VIP WEIGHTING [Business Rule]
    # Check if the filer is a VIP (assuming filer_customer_id is sent)
    filer_id = data.get('filer_customer_id')
    weight = 1
    if filer_id:
        try:
            customer = Customer.objects.get(pk=filer_id)
            # Check if David's model has 'status' or 'is_vip'
            if getattr(customer, 'status', 'Regular') == 'vip':
                weight = 2
        except Customer.DoesNotExist:
            pass
            
    feedback_data['weight'] = weight

    # Map the foreign keys based on who is filing/targeted
    if 'filer_customer_id' in data: feedback_data['filer_customer_id'] = data['filer_customer_id']
    if 'filer_driver_id' in data: feedback_data['filer_driver_id'] = data['filer_driver_id']
    
    if 'target_customer_id' in data: feedback_data['target_customer_id'] = data['target_customer_id']
    if 'target_driver_id' in data: feedback_data['target_driver_id'] = data['target_driver_id']
    if 'target_chef_id' in data: feedback_data['target_chef_id'] = data['target_chef_id']
    if 'target_dish_id' in data: feedback_data['target_dish_id'] = data['target_dish_id']

    # Create the object
    feedback = Feedback.objects.create(**feedback_data)
    
    return Response(FeedbackSerializer(feedback).data, status=201)

# 2. MANAGER DASHBOARD (View Pending)
@api_view(['GET'])
def get_pending_feedback(request):
    # Only show pending items
    items = Feedback.objects.filter(status='pending').order_by('created')
    serializer = FeedbackSerializer(items, many=True)
    return Response(serializer.data)

# 3. RESOLVE DISPUTE (The Judge Logic)
@api_view(['POST'])
def resolve_feedback(request, pk):
    try:
        feedback = Feedback.objects.get(pk=pk)
        decision = request.data.get('decision') # 'accepted' or 'dismissed'
        
        if decision == 'accepted':
            # Manager agrees with the feedback
            feedback.status = 'accepted'
            
            # If it's a COMPLAINT, issue a warning to the TARGET
            if not feedback.is_compliment:
                issue_warning(feedback, target=True)
            
            # If it's a COMPLIMENT, try to cancel an old complaint
            else:
                handle_cancellation(feedback)

        elif decision == 'dismissed':
            # Manager disagrees (Frivolous complaint)
            feedback.status = 'dismissed'
            
            # If it was a complaint, the FILER gets a penalty warning
            if not feedback.is_compliment:
                issue_warning(feedback, target=False) # target=False means warn the Filer
                
        feedback.save()
        return Response({"status": "success", "new_state": feedback.status})
        
    except Feedback.DoesNotExist:
        return Response({"error": "Feedback not found"}, status=404)

# --- HELPER FUNCTIONS ---

def issue_warning(feedback, target=True):
    """
    Adds a warning to the appropriate user.
    target=True -> Warn the person who was reported.
    target=False -> Warn the person who filed the report (Penalty).
    """
    user_to_warn = None
    
    if target:
        # We are warning the TARGET (Chef, Driver, or Customer)
        if feedback.target_customer_id: user_to_warn = feedback.target_customer_id
        elif feedback.target_driver_id: user_to_warn = feedback.target_driver_id
        elif feedback.target_chef_id: user_to_warn = feedback.target_chef_id
    else:
        # We are warning the FILER (Penalty for lying)
        if feedback.filer_customer_id: user_to_warn = feedback.filer_customer_id
        elif feedback.filer_driver_id: user_to_warn = feedback.filer_driver_id

    if user_to_warn:
        # Assuming David's models have a 'warnings' integer field
        user_to_warn.warnings += 1
        user_to_warn.save()

def handle_cancellation(new_compliment):
    """
    Business Rule: One compliment cancels one complaint.
    """
    # We need to find the user who received this compliment
    target_user = None
    kwargs = {} # Dynamic filter args
    
    if new_compliment.target_customer_id:
        target_user = new_compliment.target_customer_id
        kwargs['target_customer_id'] = target_user
    elif new_compliment.target_driver_id:
        target_user = new_compliment.target_driver_id
        kwargs['target_driver_id'] = target_user
    elif new_compliment.target_chef_id:
        target_user = new_compliment.target_chef_id
        kwargs['target_chef_id'] = target_user
        
    if target_user:
        # Find an active complaint against this user to cancel
        old_complaint = Feedback.objects.filter(
            **kwargs,
            is_compliment=False,
            status='accepted'
        ).first()
        
        if old_complaint:
            # Found one! Cancel both.
            old_complaint.status = 'cancelled'
            old_complaint.save()
            
            new_compliment.status = 'cancelled'
            new_compliment.save()
            
            # Reduce the warning count since we cancelled a complaint
            if target_user.warnings > 0:
                target_user.warnings -= 1
                target_user.save()