from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='list'),
    path('create/', views.CourseCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CourseUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='delete'),
    
    # Course Groups
    path('groups/', views.CourseGroupListView.as_view(), name='group_list'),
    path('groups/create/', views.CourseGroupCreateView.as_view(), name='group_create'),
    path('group/<int:pk>/', views.CourseGroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/edit/', views.CourseGroupUpdateView.as_view(), name='group_update'),
    
    # Enrollments
    path('enroll/<int:group_id>/', views.EnrollmentCreateView.as_view(), name='enroll'),
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/<int:pk>/grade/', views.GradeUpdateView.as_view(), name='grade_update'),
    
    # Assignments
    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:pk>/edit/', views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    path('assignments/<int:pk>/submit/', views.SubmissionCreateView.as_view(), name='submission_create'),
    
    # Announcements
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('announcements/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('announcements/<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path('announcements/<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
    
    # Reports - MVC Pattern ile genişletildi
    path('reports/students/', views.StudentReportView.as_view(), name='student_report'),
    path('reports/courses/', views.CourseReportView.as_view(), name='course_report'),
    path('reports/students/export/<str:format>/', views.export_student_report, name='export_student_report'),
    path('reports/course/<int:course_id>/export/<str:format>/', views.export_course_report, name='export_course_report'),
    path('reports/assignment/<int:assignment_id>/export/<str:format>/', views.export_assignment_report, name='export_assignment_report'),
    
    # AJAX
    path('ajax/update-grade/', views.update_grade_ajax, name='update_grade_ajax'),
    
    # Student Management
    path('<int:course_pk>/add-student/', views.add_student_to_course, name='add_student'),
    path('<int:course_pk>/remove-student/<int:student_id>/', views.remove_student_from_course, name='remove_student'),
    
    # Course Content
    path('<int:course_pk>/content/create/', views.course_content_create, name='content_create'),
    path('content/<int:pk>/update/', views.course_content_update, name='content_update'),
    path('content/<int:pk>/delete/', views.course_content_delete, name='content_delete'),
]
