import csv
import os
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AIRating, FlaggedChat # Ensure these exist in models.py

# --- HELPER: Load Local Knowledge Base ---
def load_knowledge_base():
    """Reads the local CSV file into memory."""
    kb_path = os.path.join(settings.BASE_DIR, 'ai_assist/data/knowledge_base.csv')
    kb_data = {}
    
    if os.path.exists(kb_path):
        with open(kb_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Key = Question (lowercase), Value = Answer
                kb_data[row['question'].lower().strip()] = row['answer']
    return kb_data

# --- UC 20: GET AI ANSWER ---
@api_view(['POST'])
def get_ai_answer(request):
    user_question = request.data.get('question', '').strip().lower()
    
    if not user_question:
        return Response({"answer": "Please ask a question.", "source": "System"})

    # 1. Try Local Knowledge Base First [cite: 1806-1807]
    kb = load_knowledge_base()
    
    # Simple keyword matching (for demo stability)
    for stored_question, answer in kb.items():
        if stored_question in user_question or user_question in stored_question:
            return Response({
                "answer": answer,
                "source": "Local KB", # Frontend uses this to show rating button
                "can_rate": True
            })

    # 2. Fallback to "LLM" (Simulated for Demo) [cite: 1820-1821]
    # In a real app, you would call OpenAI/Ollama here.
    # For the presentation, we return a polite placeholder.
    fake_llm_response = f"That's a great question about '{user_question}'. As an AI, I suggest checking our menu or asking a waiter!"
    
    return Response({
        "answer": fake_llm_response,
        "source": "External AI",
        "can_rate": False # Requirement: Only local answers are rated
    })

# --- UC 21: RATE ANSWER ---
@api_view(['POST'])
def rate_answer(request):
    question = request.data.get('question')
    answer = request.data.get('answer')
    rating = request.data.get('rating') # 0-5
    
    # Save the rating
    AIRating.objects.create(
        question=question,
        answer=answer,
        rating=rating
    )
    
    # [cite: 1843-1844] LOGIC: If rating is 0, flag for manager
    if int(rating) == 0:
        FlaggedChat.objects.create(
            question=question,
            answer=answer,
            reason="User rated 0 stars (Outrageous)"
        )
        return Response({"message": "Rating saved. This answer has been flagged for review."}, status=200)

    return Response({"message": "Thank you for your feedback!"}, status=200)