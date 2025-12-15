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
from .models import Course, CourseGroup, Assignment, Submission, Announcement, Enrollment, CourseContent, ExampleQuestion, Quiz
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

class AssignmentForm(forms.ModelForm):
    # Pratik teslim tarihi seçenekleri
    DUE_DATE_CHOICES = [
        ('', 'Manuel tarih seç'),
        ('1_day', '1 Gün sonra'),
        ('3_days', '3 Gün sonra'),
        ('1_week', '1 Hafta sonra'),
        ('2_weeks', '2 Hafta sonra'),
        ('3_weeks', '3 Hafta sonra'),
        ('1_month', '1 Ay sonra'),
    ]
    
    due_date_preset = forms.ChoiceField(
        choices=DUE_DATE_CHOICES,
        required=False,
        label='Hızlı Teslim Tarihi',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Assignment
        fields = ['group', 'title', 'description', 'file_url', 'due_date', 'max_score']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'group': 'Ders Grubu',
            'title': 'Başlık',
            'description': 'Açıklama',
            'file_url': 'Dosya',
            'due_date': 'Manuel Teslim Tarihi',
            'max_score': 'Maksimum Puan',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            if field != 'due_date_preset':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Ders grubu seçeneklerini ders ismiyle birlikte göster
        if user and hasattr(user, 'userprofile') and user.userprofile.user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                groups = CourseGroup.objects.filter(teacher=teacher, status='active').select_related('course')
                self.fields['group'].queryset = groups
                
                # Dropdown'da ders ismini göster
                choices = [(group.id, f"{group.course.name} - {group.course.code} ({group.semester})") 
                          for group in groups]
                self.fields['group'].choices = [('', '---------')] + choices
                
            except Teacher.DoesNotExist:
                self.fields['group'].queryset = CourseGroup.objects.none()
        
        # Hızlı teslim seçeneği kullanıldığında manuel tarih zorunlu olmasın
        self.fields['due_date'].required = False
        if hasattr(self, 'instance') and self.instance.pk:
            self.fields['due_date'].help_text = 'Değiştirmek istemiyorsanız boş bırakabilirsiniz'
        else:
            self.fields['due_date'].help_text = 'Teslim tarihi seçin'
    
    def clean(self):
        cleaned_data = super().clean()
        due_date_preset = cleaned_data.get('due_date_preset')
        due_date = cleaned_data.get('due_date')
        
        # Eğer preset seçilmişse, due_date'i hesapla
        if due_date_preset:
            from datetime import timedelta
            now = timezone.now()
            
            if due_date_preset == '1_day':
                cleaned_data['due_date'] = now + timedelta(days=1)
            elif due_date_preset == '3_days':
                cleaned_data['due_date'] = now + timedelta(days=3)
            elif due_date_preset == '1_week':
                cleaned_data['due_date'] = now + timedelta(weeks=1)
            elif due_date_preset == '2_weeks':
                cleaned_data['due_date'] = now + timedelta(weeks=2)
            elif due_date_preset == '3_weeks':
                cleaned_data['due_date'] = now + timedelta(weeks=3)
            elif due_date_preset == '1_month':
                cleaned_data['due_date'] = now + timedelta(days=30)
        
        # Manuel tarih kontrolü (sadece yeni tarih girildiyse ve geçmişte değilse)
        elif due_date:
            if due_date <= timezone.now():
                raise forms.ValidationError('Teslim tarihi gelecekte olmalıdır.')
        
        # Güncelleme sırasında tarih kontrolü - eğer hiçbir tarih yoksa mevcut tarihi koru
        elif not due_date and hasattr(self, 'instance') and self.instance.pk:
            # Güncelleme sırasında tarih değiştirilmiyorsa mevcut tarihi koru
            cleaned_data['due_date'] = self.instance.due_date
        
        # Yeni ödev oluştururken tarih zorunlu
        elif not due_date and (not hasattr(self, 'instance') or not self.instance.pk):
            raise forms.ValidationError('Lütfen bir teslim tarihi seçin.')
        
        return cleaned_data

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file_url']
        labels = {
            'file_url': 'Ödev Dosyası',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file_url'].widget.attrs.update({'class': 'form-control'})
        self.fields['file_url'].required = True

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['group', 'title', 'content', 'expire_date']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
            'expire_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'group': 'Ders Grubu',
            'title': 'Başlık',
            'content': 'İçerik',
            'expire_date': 'Son Geçerlilik Tarihi',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['expire_date'].required = False
        
        if user and hasattr(user, 'userprofile') and user.userprofile.user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                self.fields['group'].queryset = CourseGroup.objects.filter(teacher=teacher, status='active')
            except Teacher.DoesNotExist:
                self.fields['group'].queryset = CourseGroup.objects.none()

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = []  # No fields needed, student and group will be set in view
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        # Validation will be done in the view since we don't have fields
        return cleaned_data

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
    
    def clean_midterm_grade(self):
        grade = self.cleaned_data.get('midterm_grade')
        if grade is not None and (grade < 0 or grade > 100):
            raise forms.ValidationError('Vize notu 0-100 arasında olmalıdır.')
        return grade
    
    def clean_final_grade(self):
        grade = self.cleaned_data.get('final_grade')
        if grade is not None and (grade < 0 or grade > 100):
            raise forms.ValidationError('Final notu 0-100 arasında olmalıdır.')
        return grade
    
    def clean_makeup_grade(self):
        grade = self.cleaned_data.get('makeup_grade')
        if grade is not None and (grade < 0 or grade > 100):
            raise forms.ValidationError('Büt notu 0-100 arasında olmalıdır.')
        return grade
    
    def clean_project_grade(self):
        grade = self.cleaned_data.get('project_grade')
        if grade is not None and (grade < 0 or grade > 100):
            raise forms.ValidationError('Proje notu 0-100 arasında olmalıdır.')
        return grade
    
    def clean_attendance(self):
        attendance = self.cleaned_data.get('attendance')
        if attendance is not None and (attendance < 0 or attendance > 100):
            raise forms.ValidationError('Devam oranı 0-100 arasında olmalıdır.')
        return attendance

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