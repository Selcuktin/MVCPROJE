"""
Users app URLs - Web ve API endpoints
Web: Session-based authentication
API: JWT token-based authentication (geçici olarak devre dışı - paket yüklenmesi gerekiyor)
"""
from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView  # Geçici olarak devre dışı
from .views import HomeView, CustomLoginView, CustomLogoutView, RegisterView
# from . import api_views  # Geçici olarak devre dışı

app_name = 'users'

urlpatterns = [
    # Web Authentication
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    
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