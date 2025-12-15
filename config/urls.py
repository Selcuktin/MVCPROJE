"""
URL configuration for course_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.users.views import HomeView
from apps.users.api_views import faq_ask
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

# Admin panel başlığını özelleştir
admin.site.site_header = "Uzaktan Eğitim Sistemi - Yönetim Paneli"
admin.site.site_title = "Yönetim Paneli"
admin.site.index_title = "Sistem Yönetimi"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('', include('apps.users.urls')),
    path('courses/', include('apps.courses.urls')),
    path('students/', include('apps.students.urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('notes/', include('apps.notes.urls')),
    path('enrollment/', include('apps.enrollment.urls')),
    path('gradebook/', include('apps.gradebook.urls')),
    path('quiz/', include('apps.quiz.urls')),
    path('messages/', include('apps.forum.urls')),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # API Documentation (Swagger & ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # FAQ Chatbot
    path('api/faq/ask/', faq_ask, name='faq_ask'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)