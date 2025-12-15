"""Forum Admin"""
from django.contrib import admin
from .models import ForumCategory, ForumTopic, ForumReply, DirectMessage, MessageThread, ThreadMessage


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_group', 'order', 'is_active']
    list_filter = ['is_active', 'course_group']
    search_fields = ['name', 'description']


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_pinned', 'is_locked', 'views_count', 'reply_count', 'created_at']
    list_filter = ['is_pinned', 'is_locked', 'is_announcement', 'category']
    search_fields = ['title', 'content']
    readonly_fields = ['views_count', 'created_at', 'updated_at']


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'is_solution', 'created_at']
    list_filter = ['is_solution', 'created_at']
    search_fields = ['content', 'topic__title']


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'message', 'sender__username', 'recipient__username']
    readonly_fields = ['read_at', 'created_at']


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'course_group', 'created_at', 'updated_at']
    list_filter = ['course_group', 'created_at']
    search_fields = ['title']
    filter_horizontal = ['participants']


@admin.register(ThreadMessage)
class ThreadMessageAdmin(admin.ModelAdmin):
    list_display = ['thread', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'thread__title']
