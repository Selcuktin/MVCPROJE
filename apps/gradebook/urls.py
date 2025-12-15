"""
Gradebook URL Configuration
"""
from django.urls import path
from . import views

app_name = 'gradebook'

urlpatterns = [
    # Teacher views
    path('course/<int:group_id>/', views.gradebook_view, name='course_gradebook'),
    path('teacher/default/', views.teacher_default_gradebook, name='teacher_default'),
    path('course/<int:group_id>/quick-entry/', views.quick_grade_entry_view, name='course_quick_entry'),
    path('entry/<int:item_id>/', views.grade_entry_view, name='grade_entry'),
    path('update/<int:enrollment_id>/', views.update_enrollment_grade_view, name='update_enrollment_grade'),
    
    # Student views
    path('my-grades/', views.student_grades_view, name='my_grades'),
    path('transcript/', views.student_transcript_view, name='transcript'),
]
