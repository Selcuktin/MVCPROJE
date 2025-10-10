"""
URL configuration for utils app
"""
from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    path('activity-logs/', views.activity_log_list, name='activity_log_list'),
    path('activity-logs/<int:pk>/', views.activity_log_detail, name='activity_log_detail'),
    path('my-activity/', views.my_activity_log, name='my_activity_log'),
]

