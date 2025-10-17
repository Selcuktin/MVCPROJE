from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    path('activity-log/', views.ActivityLogListView.as_view(), name='activity_log_list'),
    path('my-activity/', views.MyActivityLogView.as_view(), name='my_activity_log'),
]