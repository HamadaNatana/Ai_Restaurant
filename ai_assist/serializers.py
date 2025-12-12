from rest_framework import serializers
from .models import KBEntry, AIAnswer, AIRating, KBFlag, KBModeration

class KBEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = KBEntry
        fields = ['id', 'question', 'answer', 'active', 'author_id']

class AIAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAnswer
        fields = ['id', 'question', 'answer', 'source', 'kb_id', 'created_at'] 

class AIRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRating
        fields = ['id', 'customer_id', 'ai_answer_id', 'stars', 'created_at']

class KBFlagSerializer(serializers.ModelSerializer):
    kb_question = serializers.CharField(source='report_id.question', read_only=True)
    kb_answer = serializers.CharField(source='report_id.answer', read_only=True)

    class Meta:
        model = KBFlag
        fields = ['id', 'customer_id', 'report_id', 'kb_question', 'kb_answer', 'reason', 'reviewed', 'created_at']