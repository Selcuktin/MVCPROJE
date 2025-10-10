"""
Notes app URLs
"""
from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    path('', views.note_list, name='list'),
    path('<int:pk>/', views.note_detail, name='detail'),
    path('create/', views.note_create, name='create'),
    path('<int:pk>/edit/', views.note_edit, name='edit'),
    path('<int:pk>/delete/', views.note_delete, name='delete'),
    path('ajax/get-students/', views.get_students_by_course, name='get_students_by_course'),
]
