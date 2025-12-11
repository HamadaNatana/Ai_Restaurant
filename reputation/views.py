from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from .models import Feedback
from .serializers import FeedbackSerializer
from accounts.models import Customer
from delivery.models import Driver 

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().order_by('created_at')
    serializer_class = FeedbackSerializer
    # This ViewSet will handle the base URL '/api/feedback/'

    # --- HELPER METHODS (Moved from global scope) ---

    def _issue_warning(self, feedback, target=True):
        """
        Adds a warning to the appropriate user.
        target=True -> Warn the person who was reported.
        target=False -> Warn the person who filed the report (Penalty).
        """
        user_to_warn = None
        
        if target:
            if feedback.target_customer_id: user_to_warn = feedback.target_customer_id
            elif feedback.target_driver_id: user_to_warn = feedback.target_driver_id
            elif feedback.target_chef_id: user_to_warn = feedback.target_chef_id
        else:
            if feedback.filer_customer_id: user_to_warn = feedback.filer_customer_id
            elif feedback.filer_driver_id: user_to_warn = feedback.filer_driver_id

        if user_to_warn:
            user_to_warn.warnings = F('warnings') + 1 # Use F() for safe, concurrent update
            user_to_warn.save(update_fields=['warnings']) # Only update the warnings field
            user_to_warn.refresh_from_db() # Get the updated value if needed

    def _handle_cancellation(self, new_compliment):
        """
        Business Rule: One compliment cancels one complaint.
        """
        # We need to find the user who received this compliment
        target_user = None
        kwargs = {} # Dynamic filter args
        
        # Determine the target user and the filter arguments
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
            # Find an active, accepted complaint against this user to cancel
            old_complaint = Feedback.objects.filter(
                **kwargs,
                is_compliment=False,
                status='accepted'
            ).order_by('created_at').first() # FIFO for cancellation
            
            if old_complaint:
                # Found one! Cancel both.
                old_complaint.status = 'cancelled'
                old_complaint.save(update_fields=['status'])
                
                new_compliment.status = 'cancelled'
                new_compliment.save(update_fields=['status'])
                
                # Reduce the warning count since we cancelled a complaint
                if target_user.warnings > 0:
                    target_user.warnings = F('warnings') - 1
                    target_user.save(update_fields=['warnings'])
                    target_user.refresh_from_db()

    # 1. FILE A COMPLAINT/COMPLIMENT
    def create(self, request, *args, **kwargs):
        data = request.data.copy() 
        # We need to manually map the IDs and set defaults
        feedback_data = {
            'message': data.get('message'),
            'is_compliment': data.get('is_compliment', False),
            'status': 'pending' 
        }
        
        filer_id = data.get('filer_customer_id')
        weight = 1
        if filer_id:
            try:
                customer = Customer.objects.get(pk=filer_id)
                if getattr(customer, 'status', 'Regular') == 'vip':
                    weight = 2
            except Customer.DoesNotExist:
                pass
                
        feedback_data['weight'] = weight

        # Map the foreign keys based on who is filing/targeted
        # We only assign keys if they exist in the incoming data
        for key in ['filer_customer_id', 'filer_driver_id', 'target_customer_id', 
                    'target_driver_id', 'target_chef_id', 'target_dish_id']:
            if key in data and data[key] not in (None, ''):
                feedback_data[key] = data[key]

        # Use the serializer for validation and final creation
        serializer = self.get_serializer(data=feedback_data)
        serializer.is_valid(raise_exception=True)
        
        # Creates the object
        feedback = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    # 2. MANAGER DASHBOARD (View Pending) (Replacing get_pending_feedback)
    # This method generates the URL: /api/feedback/pending/
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Only show pending feedback items, ordered by creation date.
        """
        items = self.queryset.filter(status='pending').order_by('created')
        
        # Use pagination and filtering provided by ModelViewSet automatically
        page = self.paginate_queryset(items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


    # 3. RESOLVE DISPUTE (The Judge Logic) (Replacing resolve_feedback)
    # This method generates the URL: /api/feedback/{pk}/resolve/
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Allows a manager to accept or dismiss a feedback item.
        Applies business logic for warnings and cancellations.
        """
        try:
            feedback = self.get_object() # Gets the feedback instance based on the URL pk
        except Feedback.DoesNotExist:
             # get_object() raises 404 automatically for ModelViewSet, but keeping structure for clarity
             return Response({"error": "Feedback not found"}, status=status.HTTP_404_NOT_FOUND)
             
        decision = request.data.get('decision') # 'accepted' or 'dismissed'
        
        if decision == 'accepted':
            # Manager agrees with the feedback
            feedback.status = 'accepted'
            
            # If it's a COMPLAINT, issue a warning to the TARGET
            if not feedback.is_compliment:
                self._issue_warning(feedback, target=True)
            
            # If it's a COMPLIMENT, try to cancel an old complaint
            else:
                self._handle_cancellation(feedback)

        elif decision == 'dismissed':
            # Manager disagrees (Frivolous complaint)
            feedback.status = 'dismissed'
            
            # If it was a complaint, the FILER gets a penalty warning
            if not feedback.is_compliment:
                self._issue_warning(feedback, target=False) # target=False means warn the Filer

        else:
            return Response({"error": "Invalid decision. Must be 'accepted' or 'dismissed'."}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        feedback.save(update_fields=['status']) # Only update status field
        
        # Return the fully updated object
        serializer = self.get_serializer(feedback)
        return Response(serializer.data) # Returning full data is more RESTful than just success message