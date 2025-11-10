"""
DOSYA: apps/courses/forms.py
AMAÇ: Ders yönetimi form sınıfları
KULLANIM: 
- CourseForm: Ders oluşturma/düzenleme
- CourseGroupForm: Ders grubu yönetimi
- AssignmentForm: Ödev oluşturma (hızlı tarih seçenekleri ile)
- SubmissionForm: Öğrenci ödev teslimi
- AnnouncementForm: Duyuru yayınlama
- GradeForm: Not girişi
- CourseContentForm: Ders içeriği (döküman, video) ekleme
"""
from django import forms
from django.utils import timezone
from .models import Course, CourseGroup, Enrollment, CourseContent, ExampleQuestion, Quiz
from apps.teachers.models import Teacher

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'credits', 'description', 'department', 'semester', 'capacity', 'is_elective', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'code': 'Ders Kodu',
            'name': 'Ders Adı',
            'credits': 'Kredi',
            'description': 'Açıklama',
            'department': 'Bölüm',
            'semester': 'Dönem',
            'capacity': 'Kapasite',
            'is_elective': 'Seçmeli Ders',
            'status': 'Durum',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['is_elective'].widget.attrs.update({'class': 'form-check-input'})

class CourseGroupForm(forms.ModelForm):
    class Meta:
        model = CourseGroup
        fields = ['course', 'teacher', 'semester', 'classroom', 'schedule', 'status']
        labels = {
            'course': 'Ders',
            'teacher': 'Öğretmen',
            'semester': 'Dönem',
            'classroom': 'Sınıf',
            'schedule': 'Program',
            'status': 'Durum',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['teacher'].queryset = Teacher.objects.filter(status='active')

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = []  # No fields needed, student and group will be set in view
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class GradeForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['midterm_grade', 'final_grade', 'makeup_grade', 'project_grade', 'attendance']
        widgets = {
            'midterm_grade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'final_grade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'makeup_grade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'project_grade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'attendance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
        }
        labels = {
            'midterm_grade': 'Vize Notu',
            'final_grade': 'Final Notu',
            'makeup_grade': 'Büt Notu',
            'project_grade': 'Proje Notu',
            'attendance': 'Devam (%)',
        }

class CourseContentForm(forms.ModelForm):
    class Meta:
        model = CourseContent
        fields = ['week_number', 'title', 'description', 'content_type', 'file', 'url', 'is_active']
        widgets = {
            'week_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '16'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'week_number': 'Hafta Numarası',
            'title': 'Başlık',
            'description': 'Açıklama',
            'content_type': 'İçerik Tipi',
            'file': 'Dosya',
            'url': 'Link (Opsiyonel)',
            'is_active': 'Aktif',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')
        
        if not file and not url:
            raise forms.ValidationError('Lütfen bir dosya yükleyin veya bir link girin.')
        
        return cleaned_data

class ExampleQuestionForm(forms.ModelForm):
    class Meta:
        model = ExampleQuestion
        fields = ['course', 'title', 'content', 'question_type', 'attachment', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Soru metni veya açıklaması'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'course': 'Ders',
            'title': 'Başlık',
            'content': 'İçerik',
            'question_type': 'Soru Tipi',
            'attachment': 'Ek (opsiyonel)',
            'visibility': 'Görünürlük',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Öğretmen için sadece kendi verdiği dersleri listele
        if user and hasattr(user, 'userprofile') and user.userprofile.user_type == 'teacher':
            try:
                from apps.teachers.models import Teacher
                teacher = Teacher.objects.get(user=user)
                courses = Course.objects.filter(groups__teacher=teacher).distinct()
                self.fields['course'].queryset = courses
            except Exception:
                pass


class QuizFromFileForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label='Ders', widget=forms.Select(attrs={'class': 'form-control'}))
    title = forms.CharField(max_length=255, label='Başlık', widget=forms.TextInput(attrs={'class': 'form-control'}))
    quiz_type = forms.ChoiceField(choices=Quiz.QUIZ_TYPE_CHOICES, label='Tür', widget=forms.Select(attrs={'class': 'form-control'}))
    duration_minutes = forms.IntegerField(min_value=1, initial=20, label='Süre (dk)', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    file = forms.FileField(label='Dosya (.pdf/.docx/.txt)', widget=forms.FileInput(attrs={'class': 'form-control'}))