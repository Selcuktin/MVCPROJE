"""
DOSYA: apps/students/forms.py
AMAÇ: Öğrenci form sınıfları - Öğrenci oluşturma/düzenleme için form validasyonu
KULLANIM: StudentForm - Öğrenci kaydı ve güncelleme işlemleri
- Kullanıcı hesabı otomatik oluşturur
- Email ve okul numarası tekil kontrolü yapar
- Password güvenliği sağlar
"""
from django import forms
from apps.users.models import User, UserProfile
from .models import Student

class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Kullanıcı Adı')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Şifre')
    
    class Meta:
        model = Student
        fields = ['school_number', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'gender', 'address', 'status']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'school_number': 'Okul Numarası',
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-posta',
            'phone': 'Telefon',
            'birth_date': 'Doğum Tarihi',
            'gender': 'Cinsiyet',
            'address': 'Adres',
            'status': 'Durum',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        if self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Şifreyi değiştirmek için yeni şifre girin, boş bırakırsanız mevcut şifre korunur.'
            self.fields['password'].widget.attrs['placeholder'] = 'Yeni şifre (opsiyonel)'
    
    def clean_school_number(self):
        school_number = self.cleaned_data['school_number']
        if Student.objects.filter(school_number=school_number).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Bu okul numarası ile kayıtlı başka bir öğrenci var.')
        return school_number
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if Student.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Bu e-posta adresi ile kayıtlı başka bir öğrenci var.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data['username']
        exclude_pk = None
        if self.instance.pk and hasattr(self.instance, 'user'):
            exclude_pk = self.instance.user.pk
        
        if User.objects.filter(username=username).exclude(pk=exclude_pk).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username
    
    def save(self, commit=True):
        student = super().save(commit=False)
        
        if not student.pk:
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            student.user = user
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                user_type='student',
                phone=self.cleaned_data['phone']
            )
        else:
            # Update existing user
            user = student.user
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            
            if commit:
                user.save()
                user.userprofile.phone = self.cleaned_data['phone']
                user.userprofile.save()
        
        if commit:
            student.save()
        
        return student