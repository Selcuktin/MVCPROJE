"""
Event-Driven Notification System
Automatically send notifications based on system events
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils import timezone

from apps.courses.models import Assignment, Announcement, Enrollment
from apps.gradebook.models import Grade
from .services import NotificationService

# Custom signals
assignment_deadline_approaching = Signal()
grade_published = Signal()
new_enrollment = Signal()


@receiver(post_save, sender=Assignment)
def assignment_created_notification(sender, instance, created, **kwargs):
    """Notify students when new assignment is created"""
    if created and instance.status == 'published':
        service = NotificationService()
        enrollments = Enrollment.objects.filter(
            group=instance.group,
            status='enrolled'
        ).select_related('student')
        
        for enrollment in enrollments:
            service.create_notification(
                user=enrollment.student.user,
                title='Yeni Ödev',
                message=f"{instance.group.course.name} dersi için yeni ödev: {instance.title}",
                notification_type='assignment',
                related_object_id=instance.id
            )


@receiver(post_save, sender=Announcement)
def announcement_created_notification(sender, instance, created, **kwargs):
    """Notify students when new announcement is posted"""
    if created:
        service = NotificationService()
        enrollments = Enrollment.objects.filter(
            group=instance.group,
            status='enrolled'
        ).select_related('student')
        
        for enrollment in enrollments:
            service.create_notification(
                user=enrollment.student.user,
                title='Yeni Duyuru',
                message=f"{instance.group.course.name}: {instance.title}",
                notification_type='announcement',
                related_object_id=instance.id
            )


@receiver(post_save, sender=Grade)
def grade_published_notification(sender, instance, created, **kwargs):
    """Notify student when grade is published"""
    if instance.score is not None and instance.graded_at:
        # Check if grade was just published (not updated)
        if created or (instance.graded_at and 
                      (timezone.now() - instance.graded_at).total_seconds() < 60):
            service = NotificationService()
            service.create_notification(
                user=instance.student.user,
                title='Not Yayınlandı',
                message=f"{instance.item.category.course_group.course.name} - {instance.item.name}: {instance.score}/{instance.item.max_score}",
                notification_type='grade',
                related_object_id=instance.id
            )


@receiver(post_save, sender=Enrollment)
def enrollment_notification(sender, instance, created, **kwargs):
    """Notify on enrollment events"""
    service = NotificationService()
    
    if created:
        # Notify student
        service.create_notification(
            user=instance.student.user,
            title='Ders Kaydı Başarılı',
            message=f"{instance.group.course.name} dersine kaydoldunuz",
            notification_type='enrollment',
            related_object_id=instance.id
        )
        
        # Notify teacher
        if instance.group.teacher and instance.group.teacher.user:
            service.create_notification(
                user=instance.group.teacher.user,
                title='Yeni Öğrenci',
                message=f"{instance.student.first_name} {instance.student.last_name} {instance.group.course.name} dersine kaydoldu",
                notification_type='enrollment',
                related_object_id=instance.id
            )


class EmailNotificationChannel:
    """Send notifications via email"""
    
    @staticmethod
    def send_email_notification(user, title, message):
        """Send email notification"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        if not user.email:
            return False
        
        try:
            send_mail(
                subject=f"[Uzaktan Eğitim] {title}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Email send error: {e}")
            return False
    
    @staticmethod
    def send_bulk_email(users, title, message):
        """Send bulk email notifications"""
        from django.core.mail import send_mass_mail
        from django.conf import settings
        
        email_data = []
        for user in users:
            if user.email:
                email_data.append((
                    f"[Uzaktan Eğitim] {title}",
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                ))
        
        if email_data:
            try:
                send_mass_mail(email_data, fail_silently=False)
                return len(email_data)
            except Exception as e:
                print(f"Bulk email error: {e}")
                return 0
        return 0


class BulkNotificationService:
    """Service for bulk notification operations"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.email_channel = EmailNotificationChannel()
    
    def notify_course_group(self, course_group, title, message, notification_type='general', send_email=False):
        """Send notification to all students in a course group"""
        enrollments = Enrollment.objects.filter(
            group=course_group,
            status='enrolled'
        ).select_related('student__user')
        
        count = 0
        users = []
        
        for enrollment in enrollments:
            self.notification_service.create_notification(
                user=enrollment.student.user,
                title=title,
                message=message,
                notification_type=notification_type
            )
            users.append(enrollment.student.user)
            count += 1
        
        if send_email and users:
            self.email_channel.send_bulk_email(users, title, message)
        
        return count
    
    def notify_by_role(self, role, title, message, notification_type='general', send_email=False):
        """Send notification to all users of a specific role"""
        from apps.users.models import UserProfile
        
        profiles = UserProfile.objects.filter(user_type=role).select_related('user')
        
        count = 0
        users = []
        
        for profile in profiles:
            self.notification_service.create_notification(
                user=profile.user,
                title=title,
                message=message,
                notification_type=notification_type
            )
            users.append(profile.user)
            count += 1
        
        if send_email and users:
            self.email_channel.send_bulk_email(users, title, message)
        
        return count
    
    def send_deadline_reminders(self):
        """Send reminders for upcoming assignment deadlines"""
        from datetime import timedelta
        
        tomorrow = timezone.now() + timedelta(days=1)
        upcoming_assignments = Assignment.objects.filter(
            due_date__date=tomorrow.date(),
            status='published'
        )
        
        for assignment in upcoming_assignments:
            self.notify_course_group(
                course_group=assignment.group,
                title='Ödev Hatırlatma',
                message=f"{assignment.title} ödevi yarın sona eriyor!",
                notification_type='reminder',
                send_email=True
            )
