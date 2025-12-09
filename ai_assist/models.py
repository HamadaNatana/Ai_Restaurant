import uuid
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
    kb_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    active = models.BooleanField(default=True)

    # author is a customer (manager-approved KB maybe later)
    author_id = models.ForeignKey(Customer, on_delete=models.PROTECT)

    def __str__(self):
        return f"KB: {self.question[:40]}"


class AIAnswer(TimeStampedModel):
    """
    Stored answers from either KB or external LLM (UC20).
    Used for rating (UC21).
    """
    ai_answer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to KBEntry if source was KB; else null (LLM)
    kb_id = models.ForeignKey(
        KBEntry,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    question = models.TextField()
    answer = models.TextField()

    source = models.CharField(
        max_length=20,
        choices=[("kb", "KB"), ("llm", "LLM")],
        default="kb"
    )

    def __str__(self):
        return f"AIAnswer({self.source})"


class AIRating(TimeStampedModel):
    """
    Users rate any AIAnswer from UC20 (UC21).
    Rating = 0 triggers manager review.
    """
    ai_rating_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer_id = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    ai_answer_id = models.ForeignKey(
        AIAnswer,
        on_delete=models.CASCADE,
        related_name="ratings"
    )

    stars = models.IntegerField()  # 0..5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stars}★ for {self.ai_answer_id}"


class KBFlag(TimeStampedModel):
    """
    Rating 0 on a KB answer creates a flag (UC21).
    Reviewed later by manager (UC21 continued).
    """
    flag_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer_id = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    report_id = models.OneToOneField(KBEntry, on_delete=models.CASCADE)

    reason = models.CharField(max_length=255, default="outrageous")
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Flag({self.report_id_id}, reviewed={self.reviewed})"


class KBModeration(TimeStampedModel):
    """
    Manager’s moderation record of flagged KB entries.
    """
    moderation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    manager_id = models.ForeignKey(Manager, on_delete=models.PROTECT)
    flag_id = models.ForeignKey(KBFlag, on_delete=models.PROTECT)
    action = models.CharField(max_length=200)

    def __str__(self):
        return f"Moderation: {self.action}"


# -----------------------------------------------------------
#   UC16: Discussion Board (Topics + Posts)
# -----------------------------------------------------------

class DiscussionTopic(TimeStampedModel):
    """
    UC16 – Topics for Chef/Dish/Delivery discussions.
    """
    CATEGORY_CHOICES = [
        ("chef", "Chef"),
        ("dish", "Dish"),
        ("delivery", "Delivery"),
        ("general", "General"),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")

    topic_ref_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID of related dish/chef/etc (optional)."
    )

    author = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discussion_topics"
    )

    is_locked = models.BooleanField(default=False)
    last_activity_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Topic #{self.pk}: {self.title[:40]}"


class DiscussionPost(TimeStampedModel):
    """
    UC16 – Replies under a discussion topic.
    """
    topic = models.ForeignKey(
        DiscussionTopic,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    author = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="discussion_posts"
    )

    content = models.TextField()

    def __str__(self):
        return f"Post #{self.pk} on Topic #{self.topic_id}"


# -----------------------------------------------------------
#   UC22: Allergy Preferences (Stored for Menu Filtering)
# -----------------------------------------------------------

class AllergyPreference(TimeStampedModel):
    """
    UC22 – A customer's stored allergy list.
    Helps UC06/UC07 hide unsafe dishes.
    """
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="allergy_preference"
    )

    allergens = models.TextField(blank=True, default="")
    # Stored as comma-separated list: "milk,peanut,gluten"

    def get_allergen_list(self):
        if not self.allergens:
            return []
        return [
            a.strip().lower()
            for a in self.allergens.split(",")
            if a.strip()
        ]

    def set_allergen_list(self, allergen_list):
        cleaned = [a.strip().lower() for a in allergen_list if a.strip()]
        self.allergens = ",".join(cleaned)

    def __str__(self):
        return f"Allergies({self.customer_id}: {self.allergens})"
