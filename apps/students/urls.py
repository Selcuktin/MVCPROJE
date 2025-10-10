from django.urls import path
from .views import StudentListView, StudentDetailView, StudentDashboardView, StudentCoursesView, StudentCreateView, StudentUpdateView, StudentDeleteView

app_name = 'students'

urlpatterns = [
    path('', StudentListView.as_view(), name='list'),
    path('<int:pk>/', StudentDetailView.as_view(), name='detail'),
    path('create/', StudentCreateView.as_view(), name='create'),
    path('<int:pk>/update/', StudentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', StudentDeleteView.as_view(), name='delete'),
    path('dashboard/', StudentDashboardView.as_view(), name='dashboard'),
    path('courses/', StudentCoursesView.as_view(), name='courses'),
]