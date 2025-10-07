from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from .models import UserProfile
from .forms import UserRegistrationForm, ProfileEditForm

class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Giriş başarılı olduğunda çalışır"""
        # Kullanıcı bilgilerini al
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Kullanıcıyı doğrula
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            # Next parametresini kontrol et
            next_url = self.request.GET.get('next', '')
            
            # Kullanıcı türünü kontrol et
            if hasattr(user, 'userprofile'):
                user_type = user.userprofile.user_type
                
                # Öğrenci portalına gitmek istiyorsa ama öğrenci değilse - GİRİŞE İZİN VERME
                if 'students/dashboard' in next_url and user_type != 'student':
                    messages.error(self.request, f'Bu hesap {user_type} hesabıdır. Öğrenci portalına sadece öğrenciler erişebilir.')
                    return self.form_invalid(form)
                
                # Öğretmen portalına gitmek istiyorsa ama öğretmen değilse - GİRİŞE İZİN VERME
                elif 'teachers/dashboard' in next_url and user_type != 'teacher':
                    messages.error(self.request, f'Bu hesap {user_type} hesabıdır. Öğretmen portalına sadece öğretmenler erişebilir.')
                    return self.form_invalid(form)
        
        # Eğer her şey uygunsa normal giriş işlemini yap
        return super().form_valid(form)
    
    def get_success_url(self):
        # Next parametresini kontrol et
        next_url = self.request.GET.get('next', '')
        user = self.request.user
        
        # Kullanıcı türünü kontrol et
        if hasattr(user, 'userprofile'):
            user_type = user.userprofile.user_type
            
            # Eğer next URL var ve kullanıcı türü uygunsa
            if next_url:
                # Öğrenci portalına gitmek istiyorsa ve öğrenciyse
                if 'students/dashboard' in next_url and user_type == 'student':
                    return reverse_lazy('students:dashboard')
                
                # Öğretmen portalına gitmek istiyorsa ve öğretmense
                elif 'teachers/dashboard' in next_url and user_type == 'teacher':
                    return reverse_lazy('teachers:dashboard')
            
            # Default yönlendirme - kullanıcı türüne göre
            if user_type == 'student':
                return reverse_lazy('students:dashboard')
            elif user_type == 'teacher':
                return reverse_lazy('teachers:dashboard')
            else:
                return reverse_lazy('home')
        
        return reverse_lazy('home')

class LogoutView(DjangoLogoutView):
    http_method_names = ['get', 'post']  # GET isteklerini de kabul et
    
    def get(self, request, *args, **kwargs):
        # Logout işlemini yap ve ana sayfaya yönlendir
        from django.contrib.auth import logout
        logout(request)
        return redirect('home')
    
    def post(self, request, *args, **kwargs):
        # POST istekleri için de aynı işlem
        from django.contrib.auth import logout
        logout(request)
        return redirect('home')

class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user_type = form.cleaned_data.get('user_type')
        
        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            phone=form.cleaned_data.get('phone', '')
        )
        
        messages.success(self.request, 'Kayıt başarılı! Giriş yapabilirsiniz.')
        return response

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = self.request.user.userprofile
        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileEditForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil başarıyla güncellendi.')
        return super().form_valid(form)