"""
Controller Layer: Handles request routing and response context generation.
Bu dosya kullanıcı işlemleri için HTTP isteklerini yönlendirir ve context oluşturur.
"""
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse_lazy
import json

from .services import UserService


class UserController:
    """User request handling controller"""
    
    def __init__(self):
        self.user_service = UserService()
    
    def get_home_context(self, request):
        """Get context for home page"""
        stats = self.user_service.get_home_statistics()
        return stats
    
    def handle_user_registration(self, request, form_data=None):
        """Handle user registration"""
        if form_data:
            try:
                user = self.user_service.create_user_with_profile(form_data)
                messages.success(request, 'Hesabınız başarıyla oluşturuldu. Giriş yapabilirsiniz.')
                return {'success': True, 'user': user}
            except Exception as e:
                messages.error(request, f'Hesap oluşturulurken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {'form_title': 'Yeni Hesap Oluştur'}
    
    def get_login_success_url(self, user):
        """Get redirect URL after successful login"""
        return reverse_lazy(self.user_service.get_user_redirect_url(user))
    
    def handle_login_success(self, request, user):
        """Handle successful login"""
        full_name = user.get_full_name() or user.username
        messages.success(request, f'Hoş geldiniz, {full_name}!')
        return self.get_login_success_url(user)
    
    def handle_logout(self, request):
        """Handle user logout"""
        messages.info(request, 'Başarıyla çıkış yaptınız.')
        return 'home'
    
    def get_control_panel_context(self, request):
        """Get context for control panel"""
        # Get statistics
        stats = self.user_service.get_control_panel_statistics(request.user)
        
        # Get recent activities
        recent_activities = self.user_service.get_recent_activities(request.user)
        
        # Generate calendar data
        today = timezone.now().date()
        calendar_data = self.user_service.get_calendar_data(request.user, today.year, today.month)
        
        # Month names in Turkish
        month_names = [
            'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
        ]
        
        context = {
            **stats,
            'recent_activities': recent_activities,
            'calendar_days': calendar_data.get('calendar_days', []),
            'current_year': today.year,
            'current_month': today.month,
            'current_month_name': month_names[today.month - 1]
        }
        
        return context
    
    def get_calendar_data_ajax(self, request):
        """Handle AJAX request for calendar data"""
        try:
            year = int(request.GET.get('year', timezone.now().year))
            month = int(request.GET.get('month', timezone.now().month))
            
            # Validate year and month
            if not (1900 <= year <= 2100):
                return JsonResponse({'error': 'Invalid year'}, status=400)
            if not (1 <= month <= 12):
                return JsonResponse({'error': 'Invalid month'}, status=400)
            
            calendar_data = self.user_service.get_calendar_data(request.user, year, month)
            return JsonResponse(calendar_data)
            
        except ValueError as e:
            return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    
    def get_notifications_context(self, request):
        """Get context for notifications page"""
        data = self.user_service.get_notifications_data(request.user)
        return data
    
    def mark_notification_read_ajax(self, request):
        """Handle AJAX request to mark notification as read"""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
        
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            if notification_id:
                success = self.user_service.mark_notification_as_read(request.user, notification_id)
                
                if success:
                    return JsonResponse({'success': True, 'message': 'Bildirim okundu olarak işaretlendi'})
                else:
                    return JsonResponse({'success': False, 'error': 'Bildirim işaretlenirken hata oluştu'})
            else:
                return JsonResponse({'success': False, 'error': 'Bildirim ID bulunamadı'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Geçersiz JSON verisi'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def get_user_statistics_context(self, request, user_id=None):
        """Get user statistics context"""
        if user_id:
            # Get specific user statistics (admin view)
            pass
        else:
            # Get current user statistics
            stats = self.user_service.get_control_panel_statistics(request.user)
            return {'statistics': stats}