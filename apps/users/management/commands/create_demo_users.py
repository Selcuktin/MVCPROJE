"""
Management command to create demo users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import UserProfile
from apps.students.models import Student
from apps.teachers.models import Teacher
from django.utils import timezone
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = 'Create demo users for testing'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Admin user created: admin/admin123')
            )

        # Create student user
        if not User.objects.filter(username='student1').exists():
            student_user = User.objects.create_user(
                username='student1',
                email='student1@example.com',
                password='student123',
                first_name='Ahmet',
                last_name='Yılmaz'
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=student_user,
                user_type='student',
                phone='05551234567'
            )
            
            # Create student profile
            Student.objects.create(
                user=student_user,
                school_number='20240001',
                first_name='Ahmet',
                last_name='Yılmaz',
                email='student1@example.com',
                phone='05551234567',
                birth_date=date(2000, 1, 15),
                gender='M',
                address='İstanbul, Türkiye'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Student user created: student1/student123')
            )

        # Create teacher user
        if not User.objects.filter(username='teacher1').exists():
            teacher_user = User.objects.create_user(
                username='teacher1',
                email='teacher1@example.com',
                password='teacher123',
                first_name='Fatma',
                last_name='Kaya'
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=teacher_user,
                user_type='teacher',
                phone='05559876543'
            )
            
            # Create teacher profile
            Teacher.objects.create(
                user=teacher_user,
                tc_no='12345678901',
                first_name='Fatma',
                last_name='Kaya',
                email='teacher1@example.com',
                phone='05559876543',
                birth_date=date(1980, 5, 20),
                gender='F',
                title='Dr.',
                department='Bilgisayar Mühendisliği',
                hire_date=timezone.now()
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Teacher user created: teacher1/teacher123')
            )

        self.stdout.write(
            self.style.SUCCESS('Demo users created successfully!')
        )