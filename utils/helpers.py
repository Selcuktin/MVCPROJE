"""
General helper functions
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_notification_email(to_email, subject, template_name, context):
    """Send notification email using template"""
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False

def calculate_gpa(enrollments):
    """Calculate GPA from enrollments"""
    total_points = 0
    total_credits = 0
    
    grade_points = {
        'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
        'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FF': 0.0
    }
    
    for enrollment in enrollments:
        if enrollment.grade in grade_points and enrollment.status == 'completed':
            points = grade_points[enrollment.grade]
            credits = enrollment.group.course.credits
            total_points += points * credits
            total_credits += credits
    
    return total_points / total_credits if total_credits > 0 else 0.0

def get_user_type(user):
    """Get user type safely"""
    if hasattr(user, 'userprofile'):
        return user.userprofile.user_type
    return None

def format_grade_display(grade, score=None):
    """Format grade for display"""
    if score is not None:
        return f"{grade} ({score})"
    return grade

def get_semester_display(semester_code):
    """Get semester display name"""
    semester_map = {
        'fall': 'Güz',
        'spring': 'Bahar', 
        'summer': 'Yaz'
    }
    return semester_map.get(semester_code, semester_code)