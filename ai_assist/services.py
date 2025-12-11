import ollama
from django.db import transaction
from django.db.models import Q
from .models import KBEntry, AIAnswer, AIRating, KBFlag
from accounts.models import Customer

class AIService:
    @staticmethod
    def ask_question(customer_id, question_text):
        """
        UC20: Answers a question.
        Priority: 1. Local KB (Exact match) -> 2. Mistral AI (Fallback)
        """
        # 1. Search KB
        kb_match = KBEntry.objects.filter(
            question__icontains=question_text, 
            active=True
        ).first()

        if kb_match:
            # Source: KB
            answer = AIAnswer.objects.create(
                kb_id=kb_match,
                question=question_text,
                answer=kb_match.answer,
                source="kb"
            )
        else:
            # Source: LLM (Mistral)
            try:
                # System prompt to keep the AI on topic
                system_instruction = "You are a helpful customer service AI for a restaurant. Answer briefly and politely."
                
                response = ollama.chat(model='mistral', messages=[
                    {'role': 'system', 'content': system_instruction},
                    {'role': 'user', 'content': question_text},
                ])
                llm_response_text = response['message']['content']

            except Exception as e:
                # Fallback if AI server is down
                llm_response_text = "I apologize, but I am unable to connect to the server at the moment."
                print(f"AI Error: {e}")

            answer = AIAnswer.objects.create(
                kb_id=None,
                question=question_text,
                answer=llm_response_text,
                source="llm"
            )

        return True, "Answer generated", answer

    @staticmethod
    def submit_rating(customer_id, ai_answer_id, stars):
        """
        UC21: Rate an answer.
        Logic: If stars == 0 and source was KB, flag the KB entry.
        """
        try:
            stars = int(stars)
            if not (0 <= stars <= 5):
                return False, "Stars must be between 0 and 5"
            
            # 1. Save Rating
            ai_answer = AIAnswer.objects.get(pk=ai_answer_id)
            customer = Customer.objects.get(pk=customer_id)
            
            AIRating.objects.create(
                customer_id=customer,
                ai_answer_id=ai_answer,
                stars=stars
            )

            # 2. Flag Logic (UC21)
            # If rating is 0 AND it came from a KB entry, flag it.
            if stars == 0 and ai_answer.source == "kb" and ai_answer.kb_id:
                KBFlag.objects.get_or_create(
                    customer_id=customer,
                    report_id=ai_answer.kb_id, # Link flag to the KB Entry
                    defaults={'reason': "Rated 0 stars by user"}
                )
                return True, "Rating submitted. KB Entry has been flagged for review."

            return True, "Rating submitted."

        except AIAnswer.DoesNotExist:
            return False, "Answer not found."
        except Customer.DoesNotExist:
            return False, "Customer not found."
        except Exception as e:
            return False, str(e)