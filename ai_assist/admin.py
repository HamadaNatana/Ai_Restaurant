from django.contrib import admin
from .models import KBEntry, AIAnswer, AIRating, KBFlag, KBModeration


# -----------------------------------------------------------
#   UC20–21: AI Chat + Rating + KB Flagging
# -----------------------------------------------------------

@admin.register(KBEntry)
class KBEntryAdmin(admin.ModelAdmin):
    list_display = ("pk", "question", "active", "created_at")
    search_fields = ("question", "answer")
    list_filter = ("active", "created_at")

@admin.register(AIAnswer)
class AIAnswerAdmin(admin.ModelAdmin):
    list_display = ("pk", "source", "short_question", "created_at")
    list_filter = ("source", "created_at")

    def short_question(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question

@admin.register(AIRating)
class AIRatingAdmin(admin.ModelAdmin):
    list_display = ("pk", "stars", "created_at")
    list_filter = ("stars",)

@admin.register(KBFlag)
class KBFlagAdmin(admin.ModelAdmin):
    list_display = ("pk", "reason", "reviewed", "created_at")
    list_filter = ("reviewed",)

@admin.register(KBModeration)
class KBModerationAdmin(admin.ModelAdmin):
    list_display = ("pk", "action", "created_at")