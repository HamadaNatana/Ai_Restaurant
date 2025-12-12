from django.contrib import admin
from .models import KBEntry, AIAnswer, AIRating, KBFlag, KBModeration
from django.contrib import admin
from .models import KBEntry, AIAnswer, AIRating, KBFlag, KBModeration

@admin.register(KBEntry)
class KBEntryAdmin(admin.ModelAdmin):
    list_display = ('question', 'active', 'author_id', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('question', 'answer') 
    ordering = ('created_at',)

@admin.register(AIAnswer)
class AIAnswerAdmin(admin.ModelAdmin):
    list_display = ('short_question', 'source', 'created_at')
    list_filter = ('source', 'created_at')
    readonly_fields = ('question', 'answer', 'source', 'kb_id') 
    
    def short_question(self, obj):
        return obj.question[:50] + "..."

@admin.register(KBFlag)
class KBFlagAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'customer_id', 'reviewed', 'created_at')
    list_filter = ('reviewed',)
    actions = ['mark_reviewed']

    def mark_reviewed(self, request, queryset):
        queryset.update(reviewed=True)

admin.site.register(AIRating)
admin.site.register(KBModeration)