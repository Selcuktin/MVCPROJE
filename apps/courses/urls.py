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
    
    # Teacher-Course Assignment
    path('teacher-assignment/', views.TeacherCourseAssignmentView.as_view(), name='teacher_assignment'),
    path('teacher-assignment/bulk-assign/', views.bulk_assign_view, name='bulk_assign'),
    path('teacher-assignment/bulk-remove/', views.bulk_remove_view, name='bulk_remove'),
    path('teacher-assignment/check-compatibility/', views.check_compatibility_view, name='check_compatibility'),
    path('teacher-assignment/check-conflicts/', views.check_conflicts_view, name='check_conflicts'),
    path('teacher-assignment/availability/<int:teacher_id>/', views.teacher_availability_view, name='teacher_availability'),

    # Example Questions (devre dışı)
    # path('questions/', views.ExampleQuestionListView.as_view(), name='question_list'),
    # path('questions/create/', views.ExampleQuestionCreateView.as_view(), name='question_create'),
    # path('questions/<int:pk>/', views.ExampleQuestionDetailView.as_view(), name='question_detail'),
    # path('questions/<int:pk>/edit/', views.ExampleQuestionUpdateView.as_view(), name='question_update'),
    # path('questions/<int:pk>/delete/', views.ExampleQuestionDeleteView.as_view(), name='question_delete'),
    # path('questions/<int:pk>/ai-solve/', views.ai_solve_question, name='question_ai_solve'),

    # Quizzes (devre dışı)
    # path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    # path('quizzes/from-file/', views.QuizCreateFromFileView.as_view(), name='quiz_from_file'),
    # path('quizzes/<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
]
