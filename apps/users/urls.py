"""
Users app URLs - Web ve API endpoints
Web: Session-based authentication
API: JWT token-based authentication (geçici olarak devre dışı - paket yüklenmesi gerekiyor)
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
# from rest_framework_simplejwt.views import TokenRefreshView  # Geçici olarak devre dışı
from .views import HomeView, CustomLoginView, CustomLogoutView, RegisterView, NotificationsView, ProfileView, mark_notification_read, get_unread_notification_count, UserListView
# from . import api_views  # Geçici olarak devre dışı

app_name = 'users'

urlpatterns = [
    # Web Authentication
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('notifications/', NotificationsView.as_view(), name='notifications'),
    path('notifications/mark-read/', mark_notification_read, name='mark_notification_read'),
    path('api/notifications/unread-count/', get_unread_notification_count, name='api_unread_count'),
    
    # Admin - Kullanıcı Yönetimi
    path('users/', UserListView.as_view(), name='user_list'),
    
    # Debug
    path('debug/chatbot/', TemplateView.as_view(template_name='debug_chatbot.html'), name='debug_chatbot'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # JWT API Endpoints - Geçici olarak devre dışı
    # JWT paketini aktif etmek için:
    # 1. pip install djangorestframework-simplejwt==5.3.0
    # 2. Bu yorumları kaldır
    # path('api/token/', api_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/register/', api_views.register_api, name='api_register'),
    # path('api/logout/', api_views.logout_api, name='api_logout'),
    # path('api/profile/', api_views.user_profile_api, name='api_profile'),
]