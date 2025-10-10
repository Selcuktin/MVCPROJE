"""
Management command to add sample announcements and assignments
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.courses.models import Course, CourseGroup, Assignment, Announcement
from apps.teachers.models import Teacher
from apps.students.models import Student

class Command(BaseCommand):
    help = 'Adds sample announcements and assignments to the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Adding sample announcements and assignments...'))
        
        # Get or create sample data
        try:
            # Get some courses
            courses = Course.objects.filter(status='active')[:3]
            if not courses:
                self.stdout.write(self.style.ERROR('No active courses found. Please create courses first.'))
                return
            
            # Get teachers
            teachers = Teacher.objects.filter(status='active')[:2]
            if not teachers:
                self.stdout.write(self.style.ERROR('No active teachers found. Please create teachers first.'))
                return
            
            # Create course groups if they don't exist
            groups_created = 0
            for course in courses:
                for i, teacher in enumerate(teachers):
                    group, created = CourseGroup.objects.get_or_create(
                        course=course,
                        teacher=teacher,
                        semester='2024-Güz',
                        defaults={
                            'name': f'Grup {i+1}',
                            'classroom': f'A{100+i}',
                            'schedule': 'Pazartesi 09:00-12:00',
                            'status': 'active'
                        }
                    )
                    if created:
                        groups_created += 1
            
            self.stdout.write(self.style.SUCCESS(f'Created {groups_created} course groups'))
            
            # Get all groups
            groups = CourseGroup.objects.filter(status='active')
            
            # Create sample announcements
            announcements_created = 0
            announcement_data = [
                {
                    'title': 'Hoş Geldiniz!',
                    'content': 'Yeni dönemde tüm öğrencilerimize başarılar dileriz. Ders materyalleri yakında paylaşılacaktır.',
                },
                {
                    'title': 'Vize Sınavı Duyurusu',
                    'content': 'Vize sınavımız gelecek hafta Pazartesi günü saat 10:00\'da A101 sınıfında yapılacaktır. Lütfen kimliklerinizi yanınıza almayı unutmayın.',
                    'expire_date': timezone.now() + timedelta(days=14)
                },
                {
                    'title': 'Proje Konuları Açıklandı',
                    'content': 'Final projesi konuları açıklanmıştır. Konuları ödev bölümünden inceleyebilirsiniz. Proje gruplarını gelecek hafta oluşturacağız.',
                },
                {
                    'title': 'Ders Materyalleri Güncellendi',
                    'content': 'Bu haftanın ders notları ve slaytları sisteme yüklenmiştir. Lütfen derse gelmeden önce gözden geçiriniz.',
                },
            ]
            
            for group in groups:
                for data in announcement_data[:2]:  # Her grup için 2 duyuru
                    announcement, created = Announcement.objects.get_or_create(
                        group=group,
                        teacher=group.teacher,
                        title=data['title'],
                        defaults={
                            'content': data['content'],
                            'expire_date': data.get('expire_date'),
                            'status': 'active'
                        }
                    )
                    if created:
                        announcements_created += 1
            
            self.stdout.write(self.style.SUCCESS(f'Created {announcements_created} announcements'))
            
            # Create sample assignments
            assignments_created = 0
            assignment_data = [
                {
                    'title': 'Ödev 1 - Temel Kavramlar',
                    'description': 'Bu ödevde dersin temel kavramlarını pekiştireceğiz. Aşağıdaki soruları cevaplayınız:\n\n1. Konu 1 hakkında kısa bir özet yazınız.\n2. Örnek bir uygulama geliştiriniz.\n3. Sonuçlarınızı rapor ediniz.\n\nRapor en az 3 sayfa olmalıdır.',
                    'due_date': timezone.now() + timedelta(days=14),
                    'max_score': 100
                },
                {
                    'title': 'Ödev 2 - Uygulama Projesi',
                    'description': 'Bu ödevde öğrendiğiniz kavramları kullanarak küçük bir proje geliştireceksiniz.\n\nProje Gereksinimleri:\n- Fonksiyonel kod\n- Dokümantasyon\n- Test senaryoları\n- Kullanım kılavuzu\n\nProjeyi ZIP dosyası olarak yükleyiniz.',
                    'due_date': timezone.now() + timedelta(days=21),
                    'max_score': 100
                },
                {
                    'title': 'Araştırma Ödevi',
                    'description': 'Belirlenen konulardan birini seçerek detaylı bir araştırma yapınız.\n\nAraştırma Konuları:\n1. Güncel teknolojiler ve trendler\n2. Endüstri uygulamaları\n3. Gelecek perspektifi\n\nSunum hazırlayarak sınıfa sunacaksınız.',
                    'due_date': timezone.now() + timedelta(days=30),
                    'max_score': 100
                },
                {
                    'title': 'Vaka Analizi',
                    'description': 'Verilen vaka çalışmasını analiz ediniz ve çözüm önerilerinizi sunun.\n\nBeklentiler:\n- Sorun tespiti\n- Analiz yöntemleri\n- Çözüm önerileri\n- Sonuç ve değerlendirme\n\nRapor 5-7 sayfa arasında olmalıdır.',
                    'due_date': timezone.now() + timedelta(days=28),
                    'max_score': 100
                },
            ]
            
            for group in groups:
                for data in assignment_data[:3]:  # Her grup için 3 ödev
                    assignment, created = Assignment.objects.get_or_create(
                        group=group,
                        title=data['title'],
                        defaults={
                            'description': data['description'],
                            'due_date': data['due_date'],
                            'max_score': data['max_score'],
                            'status': 'active'
                        }
                    )
                    if created:
                        assignments_created += 1
            
            self.stdout.write(self.style.SUCCESS(f'Created {assignments_created} assignments'))
            
            self.stdout.write(self.style.SUCCESS('✓ Sample announcements and assignments added successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Total: {announcements_created} announcements, {assignments_created} assignments'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

