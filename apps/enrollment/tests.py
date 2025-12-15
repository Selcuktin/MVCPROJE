"""
Enrollment Tests
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import EnrollmentMethod, EnrollmentRule
from .services import EnrollmentService
from apps.courses.models import Course, CourseGroup, Enrollment
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academic.models import AcademicTerm
from apps.users.models import UserProfile

User = get_user_model()


class EnrollmentMethodModelTest(TestCase):
    """Test EnrollmentMethod model"""
    
    def setUp(self):
        """Set up test data"""
        # Create academic term
        self.term = AcademicTerm.objects.create(
            name='2024-2025 Güz',
            year_start=2024,
            year_end=2025,
            term_type='fall',
            start_date=date(2024, 9, 16),
            end_date=date(2025, 1, 31),
            is_active=True
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Programming',
            credits=3,
            capacity=30,
            description='Test course'
        )
        
        # Create teacher
        teacher_user = User.objects.create_user(username='teacher1', password='pass')
        UserProfile.objects.create(user=teacher_user, user_type='teacher')
        self.teacher = Teacher.objects.create(
            user=teacher_user,
            first_name='Teacher',
            last_name='One',
            department='CS',
            birth_date=date(1980, 1, 1),
            hire_date=date(2020, 1, 1)
        )
        
        # Create course group
        self.group = CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            name='A',
            semester='2024-2025 Güz',
            academic_term=self.term,
            classroom='B201',
            schedule='Mon 09:00'
        )
        
        # Create student
        student_user = User.objects.create_user(username='student1', password='pass')
        UserProfile.objects.create(user=student_user, user_type='student')
        self.student = Student.objects.create(
            user=student_user,
            school_number='2024001',
            first_name='Student',
            last_name='One',
            email='student1@test.com',
            phone='5551234567',
            birth_date=date(2000, 1, 1),
            gender='M',
            address='Test Address'
        )
    
    def test_create_enrollment_method(self):
        """Test creating enrollment method"""
        method = EnrollmentMethod.objects.create(
            course_group=self.group,
            method_type='self',
            max_students=30
        )
        
        self.assertEqual(method.method_type, 'self')
        self.assertTrue(method.is_enabled)
        self.assertEqual(method.max_students, 30)
    
    def test_enrollment_key_validation(self):
        """Test enrollment key requirement"""
        method = EnrollmentMethod(
            course_group=self.group,
            method_type='key'
        )
        
        with self.assertRaises(Exception):
            method.full_clean()
    
    def test_is_enrollment_open(self):
        """Test enrollment open check"""
        today = timezone.now()
        method = EnrollmentMethod.objects.create(
            course_group=self.group,
            method_type='self',
            enrollment_start=today - timedelta(days=5),
            enrollment_end=today + timedelta(days=5)
        )
        
        self.assertTrue(method.is_enrollment_open)
    
    def test_capacity_check(self):
        """Test capacity checking"""
        method = EnrollmentMethod.objects.create(
            course_group=self.group,
            method_type='self',
            max_students=2
        )
        
        # Initially should have capacity
        self.assertTrue(method.has_capacity)
        
        # Create 2 enrollments
        for i in range(2):
            student_user = User.objects.create_user(username=f'st{i}', password='pass')
            UserProfile.objects.create(user=student_user, user_type='student')
            student = Student.objects.create(
                user=student_user,
                school_number=f'202400{i}',
                first_name=f'Student{i}',
                last_name='Test',
                email=f'st{i}@test.com',
                phone=f'555123456{i}',
                birth_date=date(2000, 1, 1),
                gender='M',
                address='Test Address'
            )
            Enrollment.objects.create(
                student=student,
                group=self.group,
                status='enrolled'
            )
        
        # Refresh method
        method.refresh_from_db()
        self.assertFalse(method.has_capacity)
    
    def test_can_enroll_with_key(self):
        """Test enrollment with key"""
        method = EnrollmentMethod.objects.create(
            course_group=self.group,
            method_type='key',
            enrollment_key='SECRET123'
        )
        
        # Correct key
        can_enroll, msg = method.can_enroll(self.student, key='SECRET123')
        self.assertTrue(can_enroll)
        
        # Wrong key
        can_enroll, msg = method.can_enroll(self.student, key='WRONG')
        self.assertFalse(can_enroll)
        self.assertIn('Geçersiz', msg)


class EnrollmentRuleModelTest(TestCase):
    """Test EnrollmentRule model"""
    
    def setUp(self):
        """Set up test data"""
        # Create courses
        self.prereq_course = Course.objects.create(
            code='CS100',
            name='Intro to CS',
            credits=3,
            capacity=30,
            description='Prerequisite course'
        )
        
        self.course = Course.objects.create(
            code='CS101',
            name='Programming',
            credits=3,
            capacity=30,
            description='Main course'
        )
        
        # Create academic term
        self.term = AcademicTerm.objects.create(
            name='2024-2025 Güz',
            year_start=2024,
            year_end=2025,
            term_type='fall',
            start_date=date(2024, 9, 16),
            end_date=date(2025, 1, 31)
        )
        
        # Create teacher
        teacher_user = User.objects.create_user(username='teacher1', password='pass')
        UserProfile.objects.create(user=teacher_user, user_type='teacher')
        self.teacher = Teacher.objects.create(
            user=teacher_user,
            first_name='Teacher',
            last_name='One',
            department='CS',
            birth_date=date(1980, 1, 1),
            hire_date=date(2020, 1, 1)
        )
        
        # Create course group
        self.group = CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            name='A',
            semester='2024-2025 Güz',
            academic_term=self.term,
            classroom='B201',
            schedule='Mon 09:00'
        )
        
        # Create student
        student_user = User.objects.create_user(username='student1', password='pass')
        UserProfile.objects.create(user=student_user, user_type='student')
        self.student = Student.objects.create(
            user=student_user,
            first_name='Student',
            last_name='One',
            student_no='2024001',
            department='CS',
            current_year=2,
            birth_date=date(2000, 1, 1),
            email='student1@test.com'
        )
    
    def test_prerequisite_rule(self):
        """Test prerequisite rule checking"""
        rule = EnrollmentRule.objects.create(
            course_group=self.group,
            rule_type='prerequisite',
            prerequisite_course=self.prereq_course,
            min_grade='DD'
        )
        
        # Student hasn't taken prerequisite
        passed, msg = rule.check_rule(self.student)
        self.assertFalse(passed)
        self.assertIn('CS100', msg)
    
    def test_department_rule(self):
        """Test department restriction"""
        rule = EnrollmentRule.objects.create(
            course_group=self.group,
            rule_type='department',
            allowed_departments='EE, ME'
        )
        
        # Student is from CS department
        passed, msg = rule.check_rule(self.student)
        self.assertFalse(passed)
        self.assertIn('bölüm', msg)
    
    def test_year_rule(self):
        """Test year restriction"""
        rule = EnrollmentRule.objects.create(
            course_group=self.group,
            rule_type='year',
            allowed_years='3, 4'
        )
        
        # Student is in year 2
        passed, msg = rule.check_rule(self.student)
        self.assertFalse(passed)


class EnrollmentServiceTest(TestCase):
    """Test EnrollmentService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = EnrollmentService()
        
        # Create term
        self.term = AcademicTerm.objects.create(
            name='2024-2025 Güz',
            year_start=2024,
            year_end=2025,
            term_type='fall',
            start_date=date(2024, 9, 16),
            end_date=date(2025, 1, 31),
            is_active=True
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            name='Programming',
            credits=3,
            capacity=30,
            description='Test course'
        )
        
        # Create teacher
        teacher_user = User.objects.create_user(username='teacher1', password='pass')
        UserProfile.objects.create(user=teacher_user, user_type='teacher')
        self.teacher = Teacher.objects.create(
            user=teacher_user,
            first_name='Teacher',
            last_name='One',
            department='CS',
            birth_date=date(1980, 1, 1),
            hire_date=date(2020, 1, 1)
        )
        
        # Create course group
        self.group = CourseGroup.objects.create(
            course=self.course,
            teacher=self.teacher,
            name='A',
            semester='2024-2025 Güz',
            academic_term=self.term,
            classroom='B201',
            schedule='Mon 09:00'
        )
        
        # Create student
        student_user = User.objects.create_user(username='student1', password='pass')
        UserProfile.objects.create(user=student_user, user_type='student')
        self.student = Student.objects.create(
            user=student_user,
            school_number='2024001',
            first_name='Student',
            last_name='One',
            email='student1@test.com',
            phone='5551234567',
            birth_date=date(2000, 1, 1),
            gender='M',
            address='Test Address'
        )
        
        # Create enrollment method
        self.method = EnrollmentMethod.objects.create(
            course_group=self.group,
            method_type='self',
            max_students=30
        )
    
    def test_can_student_enroll(self):
        """Test enrollment eligibility check"""
        result = self.service.can_student_enroll(self.student, self.group)
        
        self.assertTrue(result['can_enroll'])
        self.assertIsNotNone(result['method'])
    
    def test_enroll_student(self):
        """Test student enrollment"""
        result = self.service.enroll_student(self.student, self.group)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['enrollment'])
        
        # Check enrollment was created
        enrollment = Enrollment.objects.get(student=self.student, group=self.group)
        self.assertEqual(enrollment.status, 'enrolled')
    
    def test_cannot_enroll_twice(self):
        """Test duplicate enrollment prevention"""
        # First enrollment
        self.service.enroll_student(self.student, self.group)
        
        # Try to enroll again
        result = self.service.enroll_student(self.student, self.group)
        
        self.assertFalse(result['success'])
        self.assertIn('zaten', result['message'])
    
    def test_drop_enrollment(self):
        """Test dropping enrollment"""
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=self.student,
            group=self.group,
            status='enrolled'
        )
        
        # Allow self unenroll
        self.method.allow_self_unenroll = True
        self.method.save()
        
        # Drop enrollment
        result = self.service.drop_enrollment(enrollment.id, self.student)
        
        self.assertTrue(result['success'])
        
        # Check status changed
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'dropped')
    
    def test_get_available_courses(self):
        """Test getting available courses"""
        courses = self.service.get_available_courses_for_student(self.student, self.term)
        
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]['group'], self.group)
