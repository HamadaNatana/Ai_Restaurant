import uuid
from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from accounts.models import Customer, Manager

class KBEntry(TimeStampedModel):
    kb_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    active = models.BooleanField(default=True)
    author_id = models.ForeignKey(Customer, on_delete=models.PROTECT)

class AIAnswer(TimeStampedModel):
    ai_answer_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    kb_id = models.ForeignKey(KBEntry, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    source = models.CharField(max_length=20, choices=[('kb','KB'),('llm','LLM')], default='kb')

class AIRating(TimeStampedModel):
    ai_rating_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    ai_answer_id = models.ForeignKey(AIAnswer, on_delete=models.CASCADE, related_name='ratings')
    stars = models.IntegerField()  # 0..5  (0 triggers flag)
    created_at = models.DateTimeField(auto_now_add=True)

class KBFlag(TimeStampedModel):
    flag_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    report_id = models.OneToOneField(KBEntry, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255, default='outrageous')
    reviewed = models.BooleanField(default=False)

class KBModeration(TimeStampedModel):
    moderation_id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    manager_id = models.ForeignKey(Manager, on_delete=models.PROTECT)
    flag_id = models.ForeignKey(KBFlag,on_delete=models.PROTECT)
    action = models.CharField(max_length=100)