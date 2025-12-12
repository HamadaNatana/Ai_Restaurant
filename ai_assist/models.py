from django.db import models
from common.models import TimeStampedModel
from accounts.models import Customer, Manager
# -----------------------------------------------------------
#   UC20–21: AI Chat + Rating + KB Flagging
# -----------------------------------------------------------

class KBEntry(TimeStampedModel):
    """
    Local knowledge base entry (UC20).
    """
    question = models.CharField(max_length=255)
    answer = models.TextField()
    active = models.BooleanField(default=True)
    author_id = models.ForeignKey(Customer, on_delete=models.PROTECT)

    def __str__(self):
        return f"KB: {self.question[:40]}"


class AIAnswer(TimeStampedModel):
    """
    Stored answers from either KB or external LLM (UC20).
    Used for rating (UC21).
    """

    kb_id = models.ForeignKey(KBEntry,on_delete=models.CASCADE,null=True,blank=True)
    question = models.TextField()
    answer = models.TextField()
    source = models.CharField(max_length=20,choices=[("kb", "KB"), ("llm", "LLM")],default="kb")

    def __str__(self):
        return f"AIAnswer({self.source})"


class AIRating(TimeStampedModel):
    """
    Users rate any AIAnswer from UC20 (UC21).
    Rating = 0 triggers manager review.
    """
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,blank=True)
    ai_answer_id = models.ForeignKey(AIAnswer,on_delete=models.CASCADE,related_name="ratings")
    stars = models.IntegerField()  # 0..5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stars}★ for {self.ai_answer_id}"


class KBFlag(TimeStampedModel):
    """
    Rating 0 on a KB answer creates a flag (UC21).
    Reviewed later by manager (UC21 continued).
    """
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE,null=True,blank=True)
    report_id = models.OneToOneField(KBEntry, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255, default="outrageous")
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Flag({self.report_id_id}, reviewed={self.reviewed})"


class KBModeration(TimeStampedModel):
    """
    Manager’s moderation record of flagged KB entries.
    """
    manager_id = models.ForeignKey(Manager, on_delete=models.PROTECT)
    flag_id = models.ForeignKey(KBFlag, on_delete=models.PROTECT)
    action = models.CharField(max_length=200)

    def __str__(self):
        return f"Moderation: {self.action}"