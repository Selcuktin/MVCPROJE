from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.TeacherListView.as_view(), name='list'),
    path('create/', views.TeacherCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TeacherDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.TeacherUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.TeacherDeleteView.as_view(), name='delete'),
    path('dashboard/', views.TeacherDashboardView.as_view(), name='dashboard'),
    path('courses/', views.TeacherCoursesView.as_view(), name='courses'),
    path('assignments/', views.TeacherAssignmentsView.as_view(), name='assignments'),
    path('students/', views.TeacherStudentsView.as_view(), name='students'),
]