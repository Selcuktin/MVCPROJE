from django.urls import path
from .views import (
    TeacherListView, TeacherDetailView, TeacherCreateView, TeacherUpdateView, TeacherDeleteView,
    TeacherDashboardView, TeacherCoursesView, TeacherStudentsView, TeacherAssignmentsView, 
    TeacherAnnouncementsView
)

app_name = 'teachers'

urlpatterns = [
    path('', TeacherListView.as_view(), name='list'),
    path('create/', TeacherCreateView.as_view(), name='create'),
    path('<int:pk>/', TeacherDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', TeacherUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', TeacherDeleteView.as_view(), name='delete'),
    path('dashboard/', TeacherDashboardView.as_view(), name='dashboard'),
    path('courses/', TeacherCoursesView.as_view(), name='courses'),
    path('students/', TeacherStudentsView.as_view(), name='students'),
    path('assignments/', TeacherAssignmentsView.as_view(), name='assignments'),
    path('announcements/', TeacherAnnouncementsView.as_view(), name='announcements'),
]