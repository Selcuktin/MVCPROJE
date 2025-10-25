from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import UserProfile
from apps.courses.models import Course
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.notes.models import Note

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for the application'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            UserProfile.objects.create(user=admin, user_type='admin')
            self.stdout.write(f'[+] Admin user created: admin/admin123')

        # Create teachers
        teachers_data = [
            {'username': 'teacher1', 'first_name': 'Ahmet', 'last_name': 'Yılmaz', 'email': 'ahmet@example.com'},
            {'username': 'teacher2', 'first_name': 'Fatma', 'last_name': 'Kaya', 'email': 'fatma@example.com'},
        ]
        
        for teacher_data in teachers_data:
            if not User.objects.filter(username=teacher_data['username']).exists():
                user = User.objects.create_user(
                    username=teacher_data['username'],
                    password='teacher123',
                    first_name=teacher_data['first_name'],
                    last_name=teacher_data['last_name'],
                    email=teacher_data['email']
                )
                UserProfile.objects.create(user=user, user_type='teacher')
                from datetime import date
                Teacher.objects.create(
                    user=user,
                    tc_no=f'1234567890{user.id}',
                    first_name=teacher_data['first_name'],
                    last_name=teacher_data['last_name'],
                    email=teacher_data['email'],
                    phone=f'0555-123-456{user.id}',
                    birth_date=date(1980, 1, 1),
                    gender='M',
                    title='Dr.',
                    department='Bilgisayar Mühendisliği',
                    hire_date=date.today()
                )
                self.stdout.write(f'[+] Teacher created: {teacher_data["username"]}/teacher123')

        # Create students
        students_data = [
            {'username': 'student1', 'first_name': 'Ali', 'last_name': 'Demir', 'email': 'ali@example.com'},
            {'username': 'student2', 'first_name': 'Ayşe', 'last_name': 'Çelik', 'email': 'ayse@example.com'},
            {'username': 'student3', 'first_name': 'Mehmet', 'last_name': 'Özkan', 'email': 'mehmet@example.com'},
        ]
        
        for student_data in students_data:
            if not User.objects.filter(username=student_data['username']).exists():
                user = User.objects.create_user(
                    username=student_data['username'],
                    password='student123',
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    email=student_data['email']
                )
                UserProfile.objects.create(user=user, user_type='student')
                from datetime import date
                Student.objects.create(
                    user=user,
                    school_number=f'2024{user.id:04d}',
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    email=student_data['email'],
                    phone=f'0555-987-654{user.id}',
                    birth_date=date(2000, 1, 1),
                    gender='M',
                    address='İstanbul, Türkiye'
                )
                self.stdout.write(f'[+] Student created: {student_data["username"]}/student123')

        # Create courses
        courses_data = [
            {'code': 'BM101', 'name': 'Programlama Temelleri', 'credits': 4, 'semester': 'fall'},
            {'code': 'BM201', 'name': 'Veri Yapıları', 'credits': 3, 'semester': 'spring'},
            {'code': 'BM301', 'name': 'Web Programlama', 'credits': 3, 'semester': 'fall'},
        ]
        
        try:
            teacher1 = Teacher.objects.get(user__username='teacher1')
            teacher2 = Teacher.objects.get(user__username='teacher2')
        except Teacher.DoesNotExist:
            self.stdout.write('Teachers not found, skipping course creation')
            return
        
        for course_data in courses_data:
            if not Course.objects.filter(code=course_data['code']).exists():
                course = Course.objects.create(
                    code=course_data['code'],
                    name=course_data['name'],
                    description=f'{course_data["name"]} dersi açıklaması',
                    credits=course_data['credits'],
                    department='Bilgisayar Mühendisliği',
                    semester=course_data['semester'],
                    capacity=30
                )
                
                # Create course group
                teacher = teacher1 if course_data['code'] in ['BM101', 'BM301'] else teacher2
                from apps.courses.models import CourseGroup
                group = CourseGroup.objects.create(
                    course=course,
                    teacher=teacher,
                    name='A',
                    semester='2024-2025 Güz',
                    classroom='B101',
                    schedule='Pazartesi 09:00-12:00'
                )
                
                self.stdout.write(f'[+] Course created: {course_data["code"]} - {course_data["name"]}')

        # Create enrollments
        from apps.courses.models import CourseGroup, Enrollment
        groups = CourseGroup.objects.all()
        students = Student.objects.all()
        
        for group in groups:
            for student in students[:2]:  # İlk 2 öğrenciyi kaydet
                if not Enrollment.objects.filter(student=student, group=group).exists():
                    Enrollment.objects.create(
                        student=student,
                        group=group,
                        status='enrolled'
                    )
                    self.stdout.write(f'[+] Enrollment created: {student.full_name} -> {group.course.name}')

        # Create sample assignments
        from apps.courses.models import Assignment
        from datetime import datetime, timedelta
        
        assignments_data = [
            {
                'title': 'Python Temel Programlama Ödevi',
                'description': 'Python dilinde temel programlama kavramlarını içeren ödev. Değişkenler, döngüler ve fonksiyonlar konularını kapsayacak.',
                'max_score': 100,
                'days_from_now': 7
            },
            {
                'title': 'Veri Yapıları Projesi',
                'description': 'Linked List, Stack ve Queue veri yapılarını implement eden bir proje geliştiriniz.',
                'max_score': 100,
                'days_from_now': 14
            },
            {
                'title': 'Web Sayfası Tasarımı',
                'description': 'HTML, CSS ve JavaScript kullanarak responsive bir web sayfası tasarlayınız.',
                'max_score': 100,
                'days_from_now': 10
            }
        ]
        
        for i, group in enumerate(groups):
            if i < len(assignments_data):
                assignment_data = assignments_data[i]
                if not Assignment.objects.filter(group=group, title=assignment_data['title']).exists():
                    Assignment.objects.create(
                        group=group,
                        title=assignment_data['title'],
                        description=assignment_data['description'],
                        due_date=datetime.now() + timedelta(days=assignment_data['days_from_now']),
                        max_score=assignment_data['max_score'],
                        status='active'
                    )
                    self.stdout.write(f'[+] Assignment created: {assignment_data["title"]}')

        # Create sample announcements
        from apps.courses.models import Announcement
        
        announcements_data = [
            {
                'title': 'Ders Programı Değişikliği',
                'content': 'Bu hafta Pazartesi günü dersimiz saat 10:00\'da başlayacaktır. Lütfen geç kalmayınız.'
            },
            {
                'title': 'Vize Sınavı Duyurusu',
                'content': 'Vize sınavımız 15 Kasım Çarşamba günü saat 14:00\'te B201 sınıfında yapılacaktır. Sınav süresi 90 dakikadır.'
            },
            {
                'title': 'Proje Teslim Tarihi',
                'content': 'Dönem sonu projelerinizi 20 Aralık tarihine kadar teslim etmeniz gerekmektedir. Geç teslimler kabul edilmeyecektir.'
            }
        ]
        
        for i, group in enumerate(groups):
            if i < len(announcements_data):
                announcement_data = announcements_data[i]
                if not Announcement.objects.filter(group=group, title=announcement_data['title']).exists():
                    Announcement.objects.create(
                        group=group,
                        teacher=group.teacher,
                        title=announcement_data['title'],
                        content=announcement_data['content'],
                        status='active'
                    )
                    self.stdout.write(f'[+] Announcement created: {announcement_data["title"]}')

        # Create sample notes
        import random
        
        for group in groups:
            enrollments = Enrollment.objects.filter(group=group)
            for enrollment in enrollments:
                student = enrollment.student
                # Vize notu
                if not Note.objects.filter(course=group.course, student=student.user, exam_type='vize').exists():
                    vize_score = random.randint(40, 95)
                    Note.objects.create(
                        course=group.course,
                        student=student.user,
                        teacher=group.teacher.user,
                        exam_type='vize',
                        score=vize_score
                    )
                
                # Final notu
                if not Note.objects.filter(course=group.course, student=student.user, exam_type='final').exists():
                    final_score = random.randint(45, 100)
                    Note.objects.create(
                        course=group.course,
                        student=student.user,
                        teacher=group.teacher.user,
                        exam_type='final',
                        score=final_score
                    )

        self.stdout.write(self.style.SUCCESS('[+] Sample data created successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('Admin: admin/admin123')
        self.stdout.write('Teacher: teacher1/teacher123 or teacher2/teacher123')
        self.stdout.write('Student: student1/student123, student2/student123, student3/student123')