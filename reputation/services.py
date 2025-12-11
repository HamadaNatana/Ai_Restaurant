from django.db import transaction
from .models import FoodRating, DeliveryRating, Feedback
from accounts.models import Customer
from orders.models import Order
from menu.models import Dish

class ReputationService:
    
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
    def submit_complaint(filer_id, target_type, target_id, message, is_vip=False):
        """
        UC14: Submit a complaint/compliment.
        Auto-calculates weight based on VIP status.
        """
        weight = 2 if is_vip else 1
        
        try:
            feedback = Feedback(
                message=message,
                is_compliment=False, # Assuming complaint for now
                weight=weight,
                status=Feedback.STATUS_PENDING,
                filer_customer_id_id=filer_id # Assuming customer is filing
            )

            # Map target_type to the correct field
            if target_type == 'dish':
                feedback.target_dish_id_id = target_id
            elif target_type == 'driver':
                feedback.target_driver_id_id = target_id
            elif target_type == 'chef':
                feedback.target_chef_id_id = target_id
            else:
                return False, "Invalid target type"

            feedback.save()
            return True, "Feedback filed successfully"
        except Exception as e:
            return False, str(e)