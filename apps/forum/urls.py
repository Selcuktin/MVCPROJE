"""Forum URLs"""
from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    # Messaging UI
    path('inbox/', views.inbox, name='inbox'),
    path('compose/', views.message_compose, name='message_compose'),
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('detail/<int:message_id>/', views.message_detail, name='message_detail_alt'),
    
    # API endpoints for floating chat
    path('api/inbox/', views.api_inbox, name='api_inbox'),
    path('api/send/', views.api_send_message, name='api_send_message'),
    path('api/thread/<int:user_id>/', views.api_thread, name='api_thread'),
    path('api/clear/<int:user_id>/', views.api_clear_conversation, name='api_clear_conversation'),
    path('recipients/', views.api_recipients, name='api_recipients'),
]
