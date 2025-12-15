"""
Forum and Messaging Models
"""
from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.courses.models import CourseGroup


class ForumCategory(models.Model):
    """Forum categories for organizing discussions"""
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='forum_categories'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Forum Kategorisi'
        verbose_name_plural = 'Forum Kategorileri'
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.course_group.course.code} - {self.name}"


class ForumTopic(models.Model):
    """Discussion topics"""
    category = models.ForeignKey(
        ForumCategory,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    title = models.CharField(max_length=300)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_topics'
    )
    content = models.TextField()
    
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)
    
    views_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_post_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Forum Konusu'
        verbose_name_plural = 'Forum Konuları'
        ordering = ['-is_pinned', '-last_post_at']
    
    def __str__(self):
        return self.title
    
    @property
    def reply_count(self):
        return self.replies.count()


class ForumReply(models.Model):
    """Replies to forum topics"""
    topic = models.ForeignKey(
        ForumTopic,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_replies'
    )
    content = models.TextField()
    
    is_solution = models.BooleanField(default=False, help_text='Marked as solution by topic author')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Forum Cevabı'
        verbose_name_plural = 'Forum Cevapları'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply to {self.topic.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update topic's last_post_at
        self.topic.last_post_at = timezone.now()
        self.topic.save(update_fields=['last_post_at'])


class DirectMessage(models.Model):
    """1:1 messaging system"""
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Direkt Mesaj'
        verbose_name_plural = 'Direkt Mesajlar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.subject}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageThread(models.Model):
    """Group message threads"""
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='message_threads',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='message_threads'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Mesaj Dizisi'
        verbose_name_plural = 'Mesaj Dizileri'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title


class ThreadMessage(models.Model):
    """Messages in a thread"""
    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Dizi Mesajı'
        verbose_name_plural = 'Dizi Mesajları'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author} in {self.thread.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update thread timestamp
        self.thread.updated_at = timezone.now()
        self.thread.save(update_fields=['updated_at'])
