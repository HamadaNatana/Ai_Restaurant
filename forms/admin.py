from django.contrib import admin
from .models import DiscussionPost, DiscussionThread

#admin.site.register(DiscussionPost)
#admin.site.register(DiscussionThread)


# -----------------------------------------------------------
#   UC16: Discussion Board
# -----------------------------------------------------------

class DiscussionPostInline(admin.TabularInline):
    model = DiscussionPost
    extra = 0

@admin.register(DiscussionThread)
class DiscussionTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_locked', 'customer_id', 'last_activity_at')
    list_filter = ("category", "is_locked")
    inlines = [DiscussionPostInline]

@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ['thread_id', 'customer_id', 'created_at'] 
    list_filter = ['created_at']
    search_fields = ['content']