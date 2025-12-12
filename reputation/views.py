from rest_framework import viewsets, status, permissions, decorators
from rest_framework.response import Response
from .models import Feedback, FoodRating
from .serializers import FeedbackSerializer, FoodRatingSerializer
from .services import ReputationService
from accounts.models import Customer

class ReputationViewSet(viewsets.ModelViewSet):
    """
    Unified Endpoint for Ratings & Feedback.
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.AllowAny]

    # --- ACTIONS ---
    
    @decorators.action(detail=True, methods=['post'])
    def resolve_complaint(self, request, pk=None):
        """UC13/UC14: Manager accepts or dismisses a complaint."""
        decision = request.data.get('decision') # 'accepted' or 'dismissed'
        
        success, msg, _ = ReputationService.resolve_complaint(pk, decision)

        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=True, methods=['post'])
    def accept_compliment(self, request, pk=None):
        """UC13: Manager manually accepts a pending compliment."""
        # NOTE: Authorization check (Manager role) is crucial here.
        
        success, msg, _ = ReputationService.accept_compliment(pk)

        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=False, methods=['post'])
    def rate_food(self, request):
        """Submit a food rating."""
        customer_id = request.data.get('customer_id')
        dish_id = request.data.get('dish_id')
        order_id = request.data.get('order_id')
        stars = request.data.get('stars')

        success, msg = ReputationService.submit_food_rating(customer_id, dish_id, order_id, stars)
        
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=False, methods=['post'])
    def file_complaint(self, request):
        """Submit a complaint."""
        customer_id = request.data.get('customer_id')
        target_type = request.data.get('target_type')
        target_id = request.data.get('target_id')
        message = request.data.get('message')

        #Check VIP status
        is_vip = False
        try:
            customer = Customer.objects.get(pk=customer_id)
            is_vip = (customer.status == 'vip')
        except:
            pass

        success, msg = ReputationService.submit_complaint(
            customer_id, target_type, target_id, message, is_vip
        )
        
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        
    @decorators.action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending complaints (For Managers)."""
        pending = Feedback.objects.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)