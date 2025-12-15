"""
Activity Completion Tracking System
"""
from django.db import models
from django.utils import timezone
from apps.courses.models import Assignment, CourseGroup
from apps.students.models import Student


class ActivityCompletion(models.Model):
    """Track student completion of activities"""
    
    ACTIVITY_TYPES = [
        ('assignment', 'Ödev'),
        ('quiz', 'Quiz'),
        ('video', 'Video'),
        ('reading', 'Okuma'),
        ('discussion', 'Tartışma'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Başlanmadı'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('overdue', 'Gecikmiş'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='activity_completions'
    )
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='activity_completions'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_id = models.IntegerField(help_text='ID of the activity (assignment, quiz, etc.)')
    activity_name = models.CharField(max_length=200)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started'
    )
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.IntegerField(default=0)
    
    time_spent_seconds = models.IntegerField(default=0, help_text='Total time spent in seconds')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'activity_type', 'activity_id']
        verbose_name = 'Aktivite Tamamlama'
        verbose_name_plural = 'Aktivite Tamamlamalar'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.student} - {self.activity_name}: {self.status}"
    
    def mark_started(self):
        """Mark activity as started"""
        if not self.started_at:
            self.started_at = timezone.now()
            self.status = 'in_progress'
            self.save()
    
    def mark_completed(self):
        """Mark activity as completed"""
        self.completed_at = timezone.now()
        self.status = 'completed'
        self.progress_percentage = 100
        self.save()
    
    def update_progress(self, percentage):
        """Update progress percentage"""
        self.progress_percentage = min(100, max(0, percentage))
        if self.progress_percentage == 100:
            self.mark_completed()
        else:
            self.status = 'in_progress'
        self.save()
    
    def add_time_spent(self, seconds):
        """Add time spent on activity"""
        self.time_spent_seconds += seconds
        self.save(update_fields=['time_spent_seconds', 'updated_at'])


class PrerequisiteRule(models.Model):
    """Define prerequisites for accessing content"""
    
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='prerequisite_rules'
    )
    
    target_activity_type = models.CharField(max_length=20)
    target_activity_id = models.IntegerField()
    target_activity_name = models.CharField(max_length=200)
    
    required_activity_type = models.CharField(max_length=20)
    required_activity_id = models.IntegerField()
    required_activity_name = models.CharField(max_length=200)
    
    minimum_progress = models.IntegerField(
        default=100,
        help_text='Required progress percentage to unlock (0-100)'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Önkoşul Kuralı'
        verbose_name_plural = 'Önkoşul Kuralları'
        unique_together = ['course_group', 'target_activity_type', 'target_activity_id', 'required_activity_type', 'required_activity_id']
    
    def __str__(self):
        return f"{self.target_activity_name} requires {self.required_activity_name}"
    
    def check_prerequisite(self, student):
        """Check if student has completed prerequisite"""
        try:
            completion = ActivityCompletion.objects.get(
                student=student,
                activity_type=self.required_activity_type,
                activity_id=self.required_activity_id
            )
            
            return completion.progress_percentage >= self.minimum_progress
        except ActivityCompletion.DoesNotExist:
            return False


class ActivityTracker:
    """Service for tracking activities"""
    
    @staticmethod
    def track_view(student, activity_type, activity_id, activity_name, course_group):
        """Track when student views an activity"""
        completion, created = ActivityCompletion.objects.get_or_create(
            student=student,
            activity_type=activity_type,
            activity_id=activity_id,
            defaults={
                'activity_name': activity_name,
                'course_group': course_group,
                'status': 'in_progress'
            }
        )
        
        if created or not completion.started_at:
            completion.mark_started()
        
        return completion
    
    @staticmethod
    def can_access(student, activity_type, activity_id, course_group):
        """Check if student can access activity based on prerequisites"""
        rules = PrerequisiteRule.objects.filter(
            course_group=course_group,
            target_activity_type=activity_type,
            target_activity_id=activity_id,
            is_active=True
        )
        
        for rule in rules:
            if not rule.check_prerequisite(student):
                return False, f"Önce '{rule.required_activity_name}' tamamlanmalı"
        
        return True, "Access granted"
    
    @staticmethod
    def get_course_progress(student, course_group):
        """Get overall course progress for student"""
        completions = ActivityCompletion.objects.filter(
            student=student,
            course_group=course_group
        )
        
        if not completions.exists():
            return 0
        
        total_progress = sum(c.progress_percentage for c in completions)
        return total_progress / completions.count()
