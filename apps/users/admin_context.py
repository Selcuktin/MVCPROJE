"""
Admin Dashboard Context Processor
Admin paneline istatistik verileri sağlar
"""
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.courses.models import Course, Enrollment


def admin_stats(request):
    """Admin dashboard için istatistikler"""
    if not request.path.startswith('/admin'):
        return {}
    
    try:
        stats = {
            'total_students': Student.objects.filter(status='active').count(),
            'total_teachers': Teacher.objects.filter(status='active').count(),
            'total_courses': Course.objects.filter(status='active').count(),
            'total_enrollments': Enrollment.objects.filter(status='enrolled').count(),
        }
    except:
        stats = {
            'total_students': 0,
            'total_teachers': 0,
            'total_courses': 0,
            'total_enrollments': 0,
        }
    
    return stats
