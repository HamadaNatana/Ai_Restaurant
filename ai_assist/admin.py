from django.contrib import admin
from .models import (
    KBEntry, AIAnswer, AIRating, KBFlag, KBModeration,
    DiscussionTopic, DiscussionPost,
    AllergyPreference
)


# -----------------------------------------------------------
#   UC20–21: AI Chat + Rating + KB Flagging
# -----------------------------------------------------------

@admin.register(KBEntry)
class KBEntryAdmin(admin.ModelAdmin):
    list_display = ("kb_id", "question", "active", "author_id", "created_at")
    search_fields = ("question", "answer")
    list_filter = ("active", "created_at")
    readonly_fields = ("kb_id", "created_at", "updated_at")


@admin.register(AIAnswer)
class AIAnswerAdmin(admin.ModelAdmin):
    list_display = ("ai_answer_id", "source", "kb_id", "short_question", "created_at")
    list_filter = ("source", "created_at")
    search_fields = ("question", "answer")
    readonly_fields = ("ai_answer_id", "created_at", "updated_at")

    def short_question(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question


@admin.register(AIRating)
class AIRatingAdmin(admin.ModelAdmin):
    list_display = ("ai_rating_id", "ai_answer_id", "customer_id", "stars", "created_at")
    list_filter = ("stars", "created_at")
    readonly_fields = ("ai_rating_id", "created_at", "updated_at")


@admin.register(KBFlag)
class KBFlagAdmin(admin.ModelAdmin):
    list_display = ("flag_id", "report_id", "customer_id", "reason", "reviewed", "created_at")
    list_filter = ("reviewed", "created_at")
    search_fields = ("reason",)
    readonly_fields = ("flag_id", "created_at", "updated_at")


@admin.register(KBModeration)
class KBModerationAdmin(admin.ModelAdmin):
    list_display = ("moderation_id", "manager_id", "flag_id", "action", "created_at")
    list_filter = ("created_at",)
    search_fields = ("action",)
    readonly_fields = ("moderation_id", "created_at", "updated_at")


# -----------------------------------------------------------
#   UC16: Discussion Board
# -----------------------------------------------------------

class DiscussionPostInline(admin.TabularInline):
    model = DiscussionPost
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(DiscussionTopic)
class DiscussionTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "is_locked", "author", "last_activity_at")
    list_filter = ("category", "is_locked", "last_activity_at")
    search_fields = ("title", "topic_ref_id")
    inlines = [DiscussionPostInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "author", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content",)
    readonly_fields = ("created_at", "updated_at")


# -----------------------------------------------------------
#   UC22: Allergy Preferences
# -----------------------------------------------------------

@admin.register(AllergyPreference)
class AllergyPreferenceAdmin(admin.ModelAdmin):
    list_display = ("customer", "allergens", "created_at")
    search_fields = ("customer__username", "allergens")
    readonly_fields = ("created_at", "updated_at")
