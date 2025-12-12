from typing import Tuple, Optional, Dict, List
from django.db import transaction
from django.db.models import F, Q
from django.contrib.auth import get_user_model
from django.utils import timezone


from .models import FoodRating, Feedback 
from accounts.models import Customer
from menu.models import Chef
from delivery.models import Driver 

User = get_user_model()


class ReputationService:
    
    #  FILING FEEDBACK (UC12)

    @staticmethod
    def submit_food_rating(customer_id, dish_id, order_id, stars):
        """Submit a star rating for a dish."""
        try:
            stars = int(stars)
            if not (1 <= stars <= 5): return False, "Stars must be between 1 and 5"

            FoodRating.objects.create(
                customer_id_id=customer_id,
                dish_id_id=dish_id,
                order_id_id=order_id,
                stars=stars
            )
            return True, "Rating submitted"
        except Exception as e:
            return False, f"Error: {str(e)}"

    @staticmethod
    def file_feedback(filer_id, target_type, target_id, message, category: str):
        """
        UC12: Submit a complaint or compliment.
        Auto-calculates weight based on filer's status.
        """
        try:
            filer = Customer.objects.get(pk=filer_id) 
            weight = 2 if filer.status == Customer.STATUS_VIP else 1
        except Customer.DoesNotExist:
            return False, "Filing user not found"
        
        is_compliment = (category.lower() == 'compliment')
        
        try:
            feedback = Feedback(
                message=message,
                is_compliment=is_compliment,
                weight=weight,
                status=Feedback.STATUS_PENDING,
                filer_customer_id_id=filer_id
            )

            if target_type == 'dish':
                feedback.target_dish_id_id = target_id
            elif target_type == 'driver':
                feedback.target_driver_id_id = target_id
            elif target_type == 'chef':
                feedback.target_chef_id_id = target_id
            elif target_type == 'customer': 
                feedback.target_customer_id_id = target_id 
            else:
                return False, "Invalid target type"

            feedback.save()
            return True, f"Feedback filed (category: {category.upper()}) and awaits manager review."
        except Exception as e:
            return False, str(e)


    #  SECTION 2: MANAGER RESOLUTION & CONSEQUENCES (UC13/UC14)

    @staticmethod
    def resolve_complaint(complaint_id: str, manager_decision: str) -> Tuple[bool, str, Optional[Feedback]]:
        """
        UC13: Manager finalizes a pending complaint.
        Triggers warning issuance and status checks.
        """
        try:
            complaint = Feedback.objects.get(pk=complaint_id, status=Feedback.STATUS_PENDING)
        except Feedback.DoesNotExist:
            return False, "Complaint not found or already resolved.", None
        
        # Only process complaints (compliments are resolved by cancellation logic)
        if complaint.is_compliment:
            return False, "Use 'accept_compliment' endpoint for compliments.", None

        with transaction.atomic():
            target_user = complaint.target_user 
            filer_user = complaint.filer_customer

            if manager_decision.lower() == 'accepted':
                if target_user:
                    # Apply complaint weight
                    target_user.warnings = F('warnings') + complaint.weight 
                    target_user.save()
                    ReputationService._handle_complaint_cancellation(target_user.pk) # Check cancellation immediately
                    ReputationService._check_user_status_after_warning(target_user.pk)
                    
                complaint.status = Feedback.STATUS_ACCEPTED
                complaint.save()
                return True, f"Complaint accepted. Warning(s) issued to {target_user}.", complaint
                
            elif manager_decision.lower() == 'dismissed':
                if filer_user:
                    filer_user.warnings = F('warnings') + 1 
                    filer_user.save()
                    ReputationService._check_user_status_after_warning(filer_user.pk)
                    
                complaint.status = Feedback.STATUS_DISMISSED
                complaint.save()
                return True, "Complaint dismissed. Warning issued to filer.", complaint
                
            else:
                return False, "Invalid manager decision.", None


    @staticmethod
    def accept_compliment(compliment_id: str) -> Tuple[bool, str, Optional[Feedback]]:
        """
        Manager accepts a compliment. 
        Note: Compliments are marked 'accepted' but do not issue warnings.
        They are used later by the cancellation logic.
        """
        try:
            compliment = Feedback.objects.get(pk=compliment_id, status=Feedback.STATUS_PENDING)
        except Feedback.DoesNotExist:
            return False, "Compliment not found or already resolved.", None
        
        if not compliment.is_compliment:
            return False, "Only compliments can be accepted this way.", None
            
        with transaction.atomic():
            compliment.status = Feedback.STATUS_ACCEPTED
            compliment.save()
            
            target_user = compliment.target_user 
            if target_user:
                 ReputationService._handle_complaint_cancellation(target_user.pk)
                 
            return True, "Compliment accepted and ready for cancellation use.", compliment


    #  SECTION 3: CONSEQUENCE AND CANCELLATION HELPERS 

    @staticmethod
    def _handle_complaint_cancellation(user_id):
        """
        Implements BRR-2.10: One compliment cancels one complaint for the same user.
        Updates user's warnings and marks feedback items as 'cancelled'.
        """
        
        active_complaints = Feedback.objects.filter(
            target_user__pk=user_id,
            is_compliment=False,
            status=Feedback.STATUS_ACCEPTED
        ).order_by('timestamp')
        
        usable_compliments = Feedback.objects.filter(
            target_user__pk=user_id,
            is_compliment=True,
            status=Feedback.STATUS_ACCEPTED
        ).order_by('timestamp')
        
        num_complaints = active_complaints.count()
        num_compliments = usable_compliments.count()
        
        cancellations_to_perform = min(num_complaints, num_compliments)
        
        if cancellations_to_perform > 0:
            with transaction.atomic():
                target_user = Customer.objects.get(pk=user_id)
                target_user.warnings = F('warnings') - cancellations_to_perform
                target_user.save()

                for i in range(cancellations_to_perform):
                    active_complaints[i].status = Feedback.STATUS_CANCELLED
                    active_complaints[i].save()
                    usable_compliments[i].status = Feedback.STATUS_CANCELLED
                    usable_compliments[i].save()

                target_user.refresh_from_db()
                ReputationService._check_user_status_after_warning(user_id)
        
        return cancellations_to_perform > 0


    @staticmethod
    def _check_user_status_after_warning(user_id):
        """Checks warning count to trigger demotions (UC09) or kick-out (UC10)."""
        try:
            user = Customer.objects.get(pk=user_id) 
            user.refresh_from_db()

            if user.status == Customer.STATUS_VIP and user.warnings >= 2:

                user.status = Customer.STATUS_REGISTERED
                user.warnings = 0 
                user.save()
                
            elif user.status == Customer.STATUS_REGISTERED and user.warnings >= 3:
                ReputationService.kick_customer(user.pk)
                
        except Customer.DoesNotExist:
            return
        except Exception as e:
            print(f"Error checking user status: {e}")

    @staticmethod
    def kick_customer(customer_id):
        """UC10: Kicks a customer out of the system due to 3 warnings."""
        try:
            user_to_kick = Customer.objects.get(pk=customer_id)
            
            user_to_kick.is_blacklisted = True
            
            user_to_kick.balance = 0 
            

            user_to_kick.status = Customer.STATUS_DEACTIVATED 
            
            user_to_kick.save()
            return True, "Customer kicked out and blacklisted."
            
        except Customer.DoesNotExist:
            return False, "Customer not found."