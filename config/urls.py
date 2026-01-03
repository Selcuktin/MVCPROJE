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
admin.site.site_header = "Öğretmen Paneli"
admin.site.site_title = "Yönetim Paneli"
admin.site.index_title = "Yönetim"

# Custom admin views
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from apps.students.models import Student
from apps.notes.models import Note
from apps.courses.models import Course

@staff_member_required
def admin_transcripts_view(request):
    """Admin transkript görüntüleme sayfası"""
    students = Student.objects.filter(status='active').order_by('first_name', 'last_name')
    selected_student = None
    notes = []
    
    student_id = request.GET.get('student')
    if student_id:
        try:
            selected_student = Student.objects.get(id=student_id)
            notes = Note.objects.filter(student=selected_student.user).select_related('course').order_by('course__code', 'exam_type')
        except Student.DoesNotExist:
            pass
    
    return render(request, 'admin/transcripts.html', {
        'students': students,
        'selected_student': selected_student,
        'notes': notes,
    })

urlpatterns = [
    path('admin/transcripts/', admin_transcripts_view, name='admin_transcripts'),
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