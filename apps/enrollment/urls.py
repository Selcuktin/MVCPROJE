"""
Enrollment URL Configuration
"""
from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    # Student enrollment
    path('available/', views.available_courses_view, name='available_courses'),
    path('my-enrollments/', views.my_enrollments_view, name='my_enrollments'),
    
    # Actions
    path('enroll/<int:group_id>/', views.enroll_course_view, name='enroll_course'),
    path('drop/<int:enrollment_id>/', views.drop_enrollment_view, name='drop_enrollment'),
    
    # AJAX
    path('check/<int:group_id>/', views.check_enrollment_eligibility, name='check_eligibility'),
]
