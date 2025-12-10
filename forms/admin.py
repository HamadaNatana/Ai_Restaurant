from django.contrib import admin
from .models import DiscussionPost, DiscussionThread

admin.site.register(DiscussionPost)
admin.site.register(DiscussionThread)
