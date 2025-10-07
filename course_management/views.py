from django.views.generic import TemplateView
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, Enrollment

class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_students'] = Student.objects.count()
        context['total_teachers'] = Teacher.objects.count()
        context['total_courses'] = Course.objects.count()
        context['total_enrollments'] = Enrollment.objects.count()
        return context