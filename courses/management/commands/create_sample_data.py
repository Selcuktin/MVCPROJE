from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from accounts.models import UserProfile
from students.models import Student
from teachers.models import Teacher
from courses.models import Course, CourseGroup, Enrollment, Assignment, Announcement

class Command(BaseCommand):
    help = 'Create sample data for the course management system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            UserProfile.objects.create(
                user=admin_user,
                user_type='admin',
                phone='05551234567'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created: admin/admin123'))

        # Create sample teacher
        if not User.objects.filter(username='teacher1').exists():
            teacher_user = User.objects.create_user(
                username='teacher1',
                email='teacher1@example.com',
                password='teacher123',
                first_name='Ahmet',
                last_name='Yılmaz'
            )
            UserProfile.objects.create(
                user=teacher_user,
                user_type='teacher',
                phone='05551234568'
            )
            
            Teacher.objects.create(
                user=teacher_user,
                tc_no='12345678901',
                first_name='Ahmet',
                last_name='Yılmaz',
                email='teacher1@example.com',
                phone='05551234568',
                birth_date='1980-01-01',
                gender='M',
                title='Dr.',
                department='Bilgisayar Mühendisliği',
                hire_date=timezone.now() - timedelta(days=365),
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Teacher created: teacher1/teacher123'))

        # Create sample student
        if not User.objects.filter(username='student1').exists():
            student_user = User.objects.create_user(
                username='student1',
                email='student1@example.com',
                password='student123',
                first_name='Mehmet',
                last_name='Demir'
            )
            UserProfile.objects.create(
                user=student_user,
                user_type='student',
                phone='05551234569'
            )
            
            Student.objects.create(
                user=student_user,
                school_number='2024101',
                first_name='Mehmet',
                last_name='Demir',
                email='student1@example.com',
                phone='05551234569',
                birth_date='2000-01-01',
                gender='M',
                address='İstanbul, Türkiye',
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Student created: student1/student123'))

        # Create sample courses
        if not Course.objects.filter(code='BIL101').exists():
            course1 = Course.objects.create(
                code='BIL101',
                name='Programlama Temelleri',
                credits=3,
                description='Programlama temellerini öğreten ders',
                department='Bilgisayar Mühendisliği',
                semester='fall',
                capacity=30,
                is_elective=False,
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Course created: BIL101'))

        if not Course.objects.filter(code='BIL201').exists():
            course2 = Course.objects.create(
                code='BIL201',
                name='Veri Yapıları',
                credits=4,
                description='Veri yapıları ve algoritmalar',
                department='Bilgisayar Mühendisliği',
                semester='spring',
                capacity=25,
                is_elective=False,
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Course created: BIL201'))

        # Create course groups
        teacher = Teacher.objects.filter(tc_no='12345678901').first()
        course1 = Course.objects.filter(code='BIL101').first()
        course2 = Course.objects.filter(code='BIL201').first()
        
        if teacher and course1 and not CourseGroup.objects.filter(course=course1, teacher=teacher).exists():
            group1 = CourseGroup.objects.create(
                course=course1,
                teacher=teacher,
                semester='2024-Güz',
                classroom='A101',
                schedule='Pazartesi 09:00-12:00',
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Course group created for BIL101'))

        if teacher and course2 and not CourseGroup.objects.filter(course=course2, teacher=teacher).exists():
            group2 = CourseGroup.objects.create(
                course=course2,
                teacher=teacher,
                semester='2024-Bahar',
                classroom='A102',
                schedule='Çarşamba 13:00-16:00',
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Course group created for BIL201'))

        # Create enrollment
        student = Student.objects.filter(school_number='2024101').first()
        group1 = CourseGroup.objects.filter(course__code='BIL101').first()
        
        if student and group1 and not Enrollment.objects.filter(student=student, group=group1).exists():
            enrollment = Enrollment.objects.create(
                student=student,
                group=group1,
                attendance=85,
                grade='BA',
                status='enrolled'
            )
            self.stdout.write(self.style.SUCCESS('Enrollment created'))

        # Create assignment
        if group1 and not Assignment.objects.filter(group=group1, title='İlk Ödev').exists():
            assignment = Assignment.objects.create(
                group=group1,
                title='İlk Ödev',
                description='Python ile basit hesap makinesi yapın',
                due_date=timezone.now() + timedelta(days=7),
                max_score=100,
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Assignment created'))

        # Create announcement
        if group1 and teacher and not Announcement.objects.filter(group=group1, title='Hoş Geldiniz').exists():
            announcement = Announcement.objects.create(
                group=group1,
                teacher=teacher,
                title='Hoş Geldiniz',
                content='Programlama Temelleri dersine hoş geldiniz. İlk dersimiz Pazartesi günü.',
                expire_date=timezone.now() + timedelta(days=30),
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Announcement created'))

        # Create sample notes (grades)
        from notes.models import Note
        if student and teacher and course1 and course2:
            # BIL101 notları
            if not Note.objects.filter(course=course1, student=student.user, exam_type='vize').exists():
                Note.objects.create(
                    course=course1,
                    student=student.user,
                    teacher=teacher.user,
                    exam_type='vize',
                    score=85
                )
                self.stdout.write(self.style.SUCCESS('BIL101 Vize notu oluşturuldu: 85 (BA)'))

            if not Note.objects.filter(course=course1, student=student.user, exam_type='final').exists():
                Note.objects.create(
                    course=course1,
                    student=student.user,
                    teacher=teacher.user,
                    exam_type='final',
                    score=78
                )
                self.stdout.write(self.style.SUCCESS('BIL101 Final notu oluşturuldu: 78 (CB)'))

            # BIL201 notları
            if not Note.objects.filter(course=course2, student=student.user, exam_type='vize').exists():
                Note.objects.create(
                    course=course2,
                    student=student.user,
                    teacher=teacher.user,
                    exam_type='vize',
                    score=92
                )
                self.stdout.write(self.style.SUCCESS('BIL201 Vize notu oluşturuldu: 92 (AA)'))

            if not Note.objects.filter(course=course2, student=student.user, exam_type='final').exists():
                Note.objects.create(
                    course=course2,
                    student=student.user,
                    teacher=teacher.user,
                    exam_type='final',
                    score=65
                )
                self.stdout.write(self.style.SUCCESS('BIL201 Final notu oluşturuldu: 65 (DC)'))

            # Bütünleme notu örneği
            if not Note.objects.filter(course=course2, student=student.user, exam_type='but').exists():
                Note.objects.create(
                    course=course2,
                    student=student.user,
                    teacher=teacher.user,
                    exam_type='but',
                    score=75
                )
                self.stdout.write(self.style.SUCCESS('BIL201 Bütünleme notu oluşturuldu: 75 (CB)'))

        # Create additional sample teachers
        teacher_data = [
            ('teacher2', 'Ayşe', 'Kaya', 'Prof. Dr.', 'Matematik', 'F'),
            ('teacher3', 'Mehmet', 'Özkan', 'Doç. Dr.', 'Fizik', 'M'),
            ('teacher4', 'Fatma', 'Şahin', 'Dr.', 'Kimya', 'F'),
            ('teacher5', 'Ali', 'Çelik', 'Prof. Dr.', 'Bilgisayar Mühendisliği', 'M'),
            ('teacher6', 'Zeynep', 'Arslan', 'Doç. Dr.', 'Elektrik Mühendisliği', 'F'),
            ('teacher7', 'Hasan', 'Koç', 'Dr.', 'Makine Mühendisliği', 'M'),
            ('teacher8', 'Elif', 'Yıldız', 'Prof. Dr.', 'İnşaat Mühendisliği', 'F'),
            ('teacher9', 'Osman', 'Acar', 'Doç. Dr.', 'Endüstri Mühendisliği', 'M'),
            ('teacher10', 'Seda', 'Polat', 'Dr.', 'Gıda Mühendisliği', 'F'),
        ]
        
        for i, (username, first_name, last_name, title, department, gender) in enumerate(teacher_data, 2):
            if not User.objects.filter(username=username).exists():
                teacher_user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='teacher123',
                    first_name=first_name,
                    last_name=last_name
                )
                UserProfile.objects.create(
                    user=teacher_user,
                    user_type='teacher',
                    phone=f'0555123456{i}'
                )
                
                Teacher.objects.create(
                    user=teacher_user,
                    tc_no=f'1234567890{i}',
                    first_name=first_name,
                    last_name=last_name,
                    email=f'{username}@example.com',
                    phone=f'0555123456{i}',
                    birth_date=f'{1970 + i}-01-01',
                    gender=gender,
                    title=title,
                    department=department,
                    hire_date=timezone.now() - timedelta(days=random.randint(365, 3650)),
                    status='active'
                )
                self.stdout.write(self.style.SUCCESS(f'Teacher created: {username}/teacher123'))

        # Create additional sample students
        student_data = [
            ('student2', 'Ayşe', 'Yılmaz', 'F', 'Ankara'),
            ('student3', 'Can', 'Özdemir', 'M', 'İzmir'),
            ('student4', 'Selin', 'Kara', 'F', 'Bursa'),
            ('student5', 'Burak', 'Çetin', 'M', 'Antalya'),
            ('student6', 'Deniz', 'Aydın', 'F', 'Adana'),
            ('student7', 'Emre', 'Güneş', 'M', 'Gaziantep'),
            ('student8', 'Gizem', 'Öztürk', 'F', 'Konya'),
            ('student9', 'Kerem', 'Yıldırım', 'M', 'Kayseri'),
            ('student10', 'Merve', 'Doğan', 'F', 'Eskişehir'),
            ('student11', 'Onur', 'Çakır', 'M', 'Samsun'),
            ('student12', 'Pınar', 'Erdoğan', 'F', 'Trabzon'),
            ('student13', 'Serkan', 'Yavuz', 'M', 'Diyarbakır'),
            ('student14', 'Tuba', 'Kılıç', 'F', 'Malatya'),
            ('student15', 'Ufuk', 'Şen', 'M', 'Van'),
            ('student16', 'Vildan', 'Akın', 'F', 'Erzurum'),
            ('student17', 'Yusuf', 'Taş', 'M', 'Şanlıurfa'),
            ('student18', 'Zehra', 'Kurt', 'F', 'Hatay'),
            ('student19', 'Berk', 'Özer', 'M', 'Manisa'),
            ('student20', 'Ceren', 'Bayrak', 'F', 'Balıkesir'),
            ('student21', 'Doruk', 'Çiftçi', 'M', 'Tekirdağ'),
            ('student22', 'Ece', 'Mutlu', 'F', 'Çanakkale'),
            ('student23', 'Furkan', 'Başar', 'M', 'Edirne'),
            ('student24', 'Gamze', 'Sezer', 'F', 'Kırklareli'),
            ('student25', 'Hakan', 'Uysal', 'M', 'Sakarya'),
            ('student26', 'İrem', 'Bozkurt', 'F', 'Kocaeli'),
            ('student27', 'Jale', 'Erdem', 'F', 'Yalova'),
            ('student28', 'Kaan', 'Güler', 'M', 'Düzce'),
            ('student29', 'Lale', 'Özkan', 'F', 'Bolu'),
            ('student30', 'Murat', 'Çelik', 'M', 'Zonguldak'),
        ]
        
        for i, (username, first_name, last_name, gender, city) in enumerate(student_data, 2):
            if not User.objects.filter(username=username).exists():
                student_user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='student123',
                    first_name=first_name,
                    last_name=last_name
                )
                UserProfile.objects.create(
                    user=student_user,
                    user_type='student',
                    phone=f'0555987654{i:02d}'
                )
                
                Student.objects.create(
                    user=student_user,
                    school_number=f'202410{i}',
                    first_name=first_name,
                    last_name=last_name,
                    email=f'{username}@example.com',
                    phone=f'0555987654{i:02d}',
                    birth_date=f'{1998 + random.randint(0, 6)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                    gender=gender,
                    address=f'{city}, Türkiye',
                    status='active'
                )
                self.stdout.write(self.style.SUCCESS(f'Student created: {username}/student123'))

        # Create additional courses
        additional_courses = [
            ('MAT101', 'Matematik I', 4, 'Temel matematik konuları', 'Matematik', 'fall', 40, False),
            ('MAT102', 'Matematik II', 4, 'İleri matematik konuları', 'Matematik', 'spring', 40, False),
            ('FIZ101', 'Fizik I', 3, 'Temel fizik konuları', 'Fizik', 'fall', 35, False),
            ('FIZ102', 'Fizik II', 3, 'İleri fizik konuları', 'Fizik', 'spring', 35, False),
            ('KIM101', 'Genel Kimya', 3, 'Temel kimya konuları', 'Kimya', 'fall', 30, False),
            ('BIL301', 'Veritabanı Sistemleri', 3, 'Veritabanı tasarımı ve yönetimi', 'Bilgisayar Mühendisliği', 'fall', 25, True),
            ('BIL302', 'Web Programlama', 3, 'Modern web teknolojileri', 'Bilgisayar Mühendisliği', 'spring', 25, True),
            ('ELK201', 'Devre Analizi', 4, 'Elektrik devre analizi', 'Elektrik Mühendisliği', 'fall', 30, False),
            ('MAK201', 'Termodinamik', 3, 'Termodinamik prensipleri', 'Makine Mühendisliği', 'spring', 30, False),
            ('END201', 'Üretim Planlama', 3, 'Üretim sistemleri planlaması', 'Endüstri Mühendisliği', 'fall', 25, True),
        ]
        
        for code, name, credits, description, department, semester, capacity, is_elective in additional_courses:
            if not Course.objects.filter(code=code).exists():
                Course.objects.create(
                    code=code,
                    name=name,
                    credits=credits,
                    description=description,
                    department=department,
                    semester=semester,
                    capacity=capacity,
                    is_elective=is_elective,
                    status='active'
                )
                self.stdout.write(self.style.SUCCESS(f'Course created: {code}'))

        # Create course groups for new courses and teachers
        teachers = Teacher.objects.all()
        courses = Course.objects.all()
        
        classrooms = ['A101', 'A102', 'A103', 'B101', 'B102', 'B103', 'C101', 'C102', 'C103', 'D101']
        schedules = [
            'Pazartesi 09:00-12:00', 'Pazartesi 13:00-16:00',
            'Salı 09:00-12:00', 'Salı 13:00-16:00',
            'Çarşamba 09:00-12:00', 'Çarşamba 13:00-16:00',
            'Perşembe 09:00-12:00', 'Perşembe 13:00-16:00',
            'Cuma 09:00-12:00', 'Cuma 13:00-16:00'
        ]
        
        for course in courses:
            # Her ders için uygun bölümden öğretmen seç
            suitable_teachers = teachers.filter(department=course.department)
            if not suitable_teachers.exists():
                suitable_teachers = teachers  # Eğer uygun öğretmen yoksa hepsinden seç
            
            teacher = random.choice(suitable_teachers)
            
            if not CourseGroup.objects.filter(course=course, teacher=teacher).exists():
                CourseGroup.objects.create(
                    course=course,
                    teacher=teacher,
                    semester='2024-Güz' if course.semester == 'fall' else '2024-Bahar',
                    classroom=random.choice(classrooms),
                    schedule=random.choice(schedules),
                    status='active'
                )

        # Create random enrollments
        students = Student.objects.all()
        groups = CourseGroup.objects.all()
        
        for student in students:
            # Her öğrenci 3-6 derse kayıt olsun
            num_enrollments = random.randint(3, 6)
            selected_groups = random.sample(list(groups), min(num_enrollments, len(groups)))
            
            for group in selected_groups:
                if not Enrollment.objects.filter(student=student, group=group).exists():
                    Enrollment.objects.create(
                        student=student,
                        group=group,
                        attendance=random.randint(70, 100),
                        grade='NA',
                        status='enrolled'
                    )

        # Create random notes for enrolled students
        from notes.models import Note
        enrollments = Enrollment.objects.all()
        exam_types = ['vize', 'final', 'but']
        
        for enrollment in enrollments:
            # Her kayıt için rastgele notlar oluştur
            for exam_type in exam_types:
                if random.choice([True, False, False]):  # %33 şans ile not oluştur
                    if not Note.objects.filter(
                        course=enrollment.group.course,
                        student=enrollment.student.user,
                        exam_type=exam_type
                    ).exists():
                        score = random.randint(40, 100)
                        Note.objects.create(
                            course=enrollment.group.course,
                            student=enrollment.student.user,
                            teacher=enrollment.group.teacher.user,
                            exam_type=exam_type,
                            score=score
                        )

        self.stdout.write(self.style.SUCCESS('Extended sample data creation completed!'))
        self.stdout.write('Login credentials:')
        self.stdout.write('Admin: admin/admin123')
        self.stdout.write('Teachers: teacher1-teacher10/teacher123')
        self.stdout.write('Students: student1-student30/student123')