from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('create/', views.StudentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.StudentDeleteView.as_view(), name='delete'),
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    path('courses/', views.StudentCoursesView.as_view(), name='courses'),
    path('assignments/', views.StudentAssignmentsView.as_view(), name='assignments'),
    path('grades/', views.StudentGradesView.as_view(), name='grades'),
    path('export/', views.StudentExportView.as_view(), name='export'),
]