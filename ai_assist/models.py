from django.db import models
from django.conf import settings

class KBArticle(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    active = models.BooleanField(default=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

class ChatTurn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    question = models.TextField()
    answer = models.TextField()
    source = models.CharField(max_length=20, choices=[('kb','KB'),('llm','LLM')], default='kb')

class AnswerRating(models.Model):
    chat_turn = models.ForeignKey(ChatTurn, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    stars = models.IntegerField()  # 0..5  (0 triggers flag)
    created_at = models.DateTimeField(auto_now_add=True)

class FlaggedAnswer(models.Model):
    chat_turn = models.OneToOneField(ChatTurn, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255, default='outrageous')
    reviewed = models.BooleanField(default=False)
