from rest_framework import viewsets, status, permissions, decorators
from rest_framework.response import Response
from .models import AIAnswer, KBFlag
from .serializers import AIAnswerSerializer, KBFlagSerializer
from .services import AIService

class AIChatViewSet(viewsets.GenericViewSet):
    """
    Primary Endpoint for UC20 (Chat) and UC21 (Rate).
    """
    queryset = AIAnswer.objects.all()
    serializer_class = AIAnswerSerializer
    permission_classes = [permissions.AllowAny]

    @decorators.action(detail=False, methods=['post'])
    def ask(self, request):
        """
        UC20: Ask a question.
        """
        customer_id = request.data.get('customer_id')
        question = request.data.get('question')

        if not customer_id or not question:
            return Response({'error': 'Missing customer_id or question'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg, answer_obj = AIService.ask_question(customer_id, question)
        
        if success:
            return Response({
                "message": msg,
                "answer": AIAnswerSerializer(answer_obj).data
            }, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=False, methods=['post'])
    def rate(self, request):
        """
        UC21: Rate an answer (0-5 stars).
        """
        customer_id = request.data.get('customer_id')
        ai_answer_id = request.data.get('ai_answer_id')
        stars = request.data.get('stars')

        if not all([customer_id, ai_answer_id, stars is not None]):
            return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = AIService.submit_rating(customer_id, ai_answer_id, stars)
        
        if success:
            return Response({'message': msg}, status=status.HTTP_200_OK)
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

class ManagerKBViewSet(viewsets.ModelViewSet):
    """
    For Managers to view flagged entries (UC21 continued).
    """
    queryset = KBFlag.objects.all()
    serializer_class = KBFlagSerializer