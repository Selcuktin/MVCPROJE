from django import forms
from apps.users.models import User, UserProfile
from .models import Teacher

class TeacherForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label='Kullanıcı Adı')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label='Şifre')
    
    class Meta:
        model = Teacher
        fields = ['tc_no', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'gender', 'title', 'department', 'hire_date', 'status']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'tc_no': 'TC Kimlik No',
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-posta',
            'phone': 'Telefon',
            'birth_date': 'Doğum Tarihi',
            'gender': 'Cinsiyet',
            'title': 'Unvan',
            'department': 'Bölüm',
            'hire_date': 'İşe Başlama Tarihi',
            'status': 'Durum',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        if self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Şifreyi değiştirmek için yeni şifre girin, boş bırakırsanız mevcut şifre korunur.'
    
    def clean_tc_no(self):
        tc_no = self.cleaned_data['tc_no']
        if Teacher.objects.filter(tc_no=tc_no).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Bu TC Kimlik No ile kayıtlı başka bir öğretmen var.')
        return tc_no
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if Teacher.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Bu e-posta adresi ile kayıtlı başka bir öğretmen var.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.user.pk if self.instance.pk else None).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        if not teacher.pk:
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            teacher.user = user
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                user_type='teacher',
                phone=self.cleaned_data['phone']
            )
        else:
            # Update existing user
            user = teacher.user
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
            teacher.save()
        
        return teacher