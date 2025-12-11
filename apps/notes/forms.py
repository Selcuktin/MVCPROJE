from django import forms
from apps.users.models import User
from .models import Note
from apps.courses.models import Course
from apps.students.models import Student

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['course', 'student', 'exam_type', 'score']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select', 'id': 'id_course'}),
            'student': forms.Select(attrs={'class': 'form-select', 'id': 'id_student'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '0-100 arası puan'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        initial_data = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)
        
        # Eğer öğretmen ise, sadece kendi derslerini göster
        if user and hasattr(user, 'userprofile') and user.userprofile.user_type == 'teacher':
            from apps.teachers.models import Teacher
            try:
                teacher = Teacher.objects.get(user=user)
                # Öğretmenin verdiği dersleri filtrele
                self.fields['course'].queryset = Course.objects.filter(groups__teacher=teacher).distinct()
            except Teacher.DoesNotExist:
                self.fields['course'].queryset = Course.objects.none()
        
        # Öğrenci seçeneklerinin etiketi: ad soyad (yoksa kullanıcı adı)
        self.fields['student'].label_from_instance = lambda obj: obj.get_full_name() or obj.username
        # Başlangıçta öğrenci listesini boş bırak
        self.fields['student'].queryset = User.objects.none()
        
        # URL parametrelerinden gelen course varsa, o derse kayıtlı öğrencileri göster
        course_id = None
        if 'course' in self.data:
            course_id = self.data.get('course')
        elif 'course' in initial_data:
            course_id = initial_data.get('course')
        elif self.instance.pk and self.instance.course:
            course_id = self.instance.course.id
            
        if course_id:
            try:
                course_id = int(course_id)
                course = Course.objects.get(id=course_id)
                # Bu derse kayıtlı öğrencileri getir
                enrolled_students = Student.objects.filter(
                    enrollments__group__course=course,
                    enrollments__status='enrolled'  # Sadece aktif kayıtlı öğrenciler
                ).distinct()
                # Student modellerini User modellerine dönüştür
                student_users = User.objects.filter(
                    student__in=enrolled_students
                )
                self.fields['student'].queryset = student_users
            except (ValueError, TypeError, Course.DoesNotExist):
                pass

        # Not düzenlemede mevcut öğrenciyi otomatik seç ve alanı kilitle
        if self.instance and self.instance.pk:
            self.fields['student'].initial = self.instance.student
            self.fields['student'].disabled = True

class NoteFilterForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        empty_label="Tüm Dersler",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Course"
    )
    exam_type = forms.ChoiceField(
        choices=[('', 'Tüm Sınav Türleri')] + Note.EXAM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Exam type"
    )
    grade = forms.ChoiceField(
        choices=[('', 'Tüm Notlar')] + Note.GRADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Grade"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Eğer öğretmen ise, sadece kendi derslerini göster
        if user and hasattr(user, 'userprofile') and user.userprofile.user_type == 'teacher':
            from apps.teachers.models import Teacher
            try:
                teacher = Teacher.objects.get(user=user)
                # Öğretmenin verdiği dersleri filtrele
                self.fields['course'].queryset = Course.objects.filter(groups__teacher=teacher).distinct()
            except Teacher.DoesNotExist:
                self.fields['course'].queryset = Course.objects.all()