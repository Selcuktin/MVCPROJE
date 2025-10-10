"""
Course app tests
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Course, CourseGroup, Enrollment
from .services import CourseService, EnrollmentService
from apps.teachers.models import Teacher
from apps.students.models import Student

User = get_user_model()

class CourseModelTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            credits=3,
            description='Basic computer science concepts',
            department='Computer Science',
            semester='fall',
            capacity=30,
            is_elective=False
        )
    
    def test_course_str(self):
        self.assertEqual(str(self.course), 'CS101 - Introduction to Computer Science')
    
    def test_course_creation(self):
        self.assertEqual(self.course.code, 'CS101')
        self.assertEqual(self.course.credits, 3)
        self.assertEqual(self.course.status, 'active')

class CourseServiceTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            credits=3,
            description='Basic computer science concepts',
            department='Computer Science',
            semester='fall',
            capacity=2,
            is_elective=False
        )
        
        # Create teacher
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            first_name='John',
            last_name='Doe'
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
            hire_date=timezone.now()
        )
        
        self.course_group = CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            name='A',
            semester='2024-Fall',
            classroom='A101',
            schedule='Monday 09:00-12:00'
        )
    
    def test_check_course_capacity(self):
        # Initially should have capacity
        self.assertTrue(CourseService.check_course_capacity(self.course_group))
        
        # Create students to fill capacity
        for i in range(2):
            student_user = User.objects.create_user(
                username=f'student{i}',
                email=f'student{i}@test.com'
            )
            student = Student.objects.create(
                user=student_user,
                school_number=f'2024000{i}',
                first_name=f'Student{i}',
                last_name='Test',
                email=f'student{i}@test.com',
                phone='1234567890',
                birth_date='2000-01-01',
                gender='M',
                address='Test Address'
            )
            Enrollment.objects.create(
                student=student,
                group=self.course_group,
                status='enrolled'
            )
        
        # Now should be at capacity
        self.assertFalse(CourseService.check_course_capacity(self.course_group))

class CourseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            credits=3,
            description='Basic computer science concepts',
            department='Computer Science',
            semester='fall',
            capacity=30,
            is_elective=False
        )
    
    def test_course_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('courses:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CS101')
    
    def test_course_detail_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('courses:detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.name)