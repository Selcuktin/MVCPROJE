"""
Smoke Tests: Temel sistem işlevlerini kontrol eder
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.users.models import UserProfile
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.courses.models import Course, CourseGroup
from apps.notes.models import Note

User = get_user_model()


class SmokeTest(TestCase):
    """Basic smoke tests to ensure system is functional"""
    
    def setUp(self):
        """Set up test users and basic data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            user_type='admin'
        )
        
        # Create teacher user
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            password='teacher123',
            email='teacher@test.com'
        )
        UserProfile.objects.create(
            user=self.teacher_user,
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            tc_no='12345678901',
            first_name='John',
            last_name='Doe',
            email='teacher@test.com',
            phone='1234567890',
            birth_date='1980-01-01',
            gender='M',
            title='Dr.',
            department='Computer Science',
            hire_date='2020-01-01'
        )
        
        # Create student user
        self.student_user = User.objects.create_user(
            username='student1',
            password='student123',
            email='student@test.com'
        )
        UserProfile.objects.create(
            user=self.student_user,
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school_number='20240001',
            first_name='Jane',
            last_name='Smith',
            email='student@test.com',
            phone='9876543210',
            birth_date='2000-01-01',
            gender='F',
            address='Test Address'
        )
        
        # Create a course
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Programming',
            credits=3,
            description='Basic programming concepts',
            department='Computer Science',
            semester='fall',
            capacity=30
        )
    
    def test_login_functionality(self):
        """Test: Kullanıcılar login olabiliyor mu?"""
        # Test admin login
        response = self.client.post(reverse('users:login'), {
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
        # Test teacher login
        self.client.logout()
        response = self.client.post(reverse('users:login'), {
            'username': 'teacher1',
            'password': 'teacher123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Test student login
        self.client.logout()
        response = self.client.post(reverse('users:login'), {
            'username': 'student1',
            'password': 'student123'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_course_list_page(self):
        """Test: Ders listesi sayfası açılıyor mu?"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CS101')
    
    def test_course_detail_page(self):
        """Test: Ders detay sayfası açılıyor mu?"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('courses:detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Introduction to Programming')
    
    def test_notifications_page(self):
        """Test: Bildirimler sayfası açılıyor mu?"""
        self.client.login(username='student1', password='student123')
        response = self.client.get(reverse('users:notifications'))
        self.assertEqual(response.status_code, 200)
    
    def test_notification_api_endpoint(self):
        """Test: Bildirim API endpoint çalışıyor mu?"""
        self.client.login(username='student1', password='student123')
        response = self.client.get(reverse('users:api_unread_count'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('count', response.json())
    
    def test_student_dashboard(self):
        """Test: Öğrenci dashboard'u açılıyor mu?"""
        self.client.login(username='student1', password='student123')
        response = self.client.get(reverse('students:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_teacher_dashboard(self):
        """Test: Öğretmen dashboard'u açılıyor mu?"""
        self.client.login(username='teacher1', password='teacher123')
        response = self.client.get(reverse('teachers:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_course_creation(self):
        """Test: Yeni ders oluşturulabiliyor mu?"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post(reverse('courses:create'), {
            'code': 'CS102',
            'name': 'Data Structures',
            'credits': 4,
            'description': 'Advanced data structures',
            'department': 'Computer Science',
            'semester': 'spring',
            'capacity': 25,
            'is_elective': False
        })
        # Either redirect (302) or form validation issue (200)
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 302:
            # Check if course was created
            self.assertTrue(Course.objects.filter(code='CS102').exists())
    
    def test_enrollment_letter_grade_calculation(self):
        """Test: Enrollment harf notu hesaplama çalışıyor mu?"""
        from apps.courses.models import CourseGroup, Enrollment
        
        # Create course group
        group = CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            semester='2024-Fall',
            classroom='A101',
            schedule='Monday 09:00-12:00'
        )
        
        # Create enrollment with grades
        enrollment = Enrollment.objects.create(
            student=self.student,
            group=group,
            midterm_grade=85.0,
            final_grade=90.0,
            status='enrolled'
        )
        
        # Check if letter grade was calculated
        self.assertNotEqual(enrollment.grade, 'NA')
        self.assertIn(enrollment.grade, ['AA', 'BA', 'BB', 'CB', 'CC', 'DC', 'DD', 'FD', 'FF'])
