"""
Management Command: Örnek Online Kurs Oluştur
Bu komut Udemy tarzı örnek bir online kurs oluşturur
Kullanım: python manage.py create_sample_online_course
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import (
    Course, CourseModule, Lesson, Quiz, QuizQuestion, 
    QuizChoice, CourseExam
)
from apps.teachers.models import Teacher


class Command(BaseCommand):
    help = 'Örnek online kurs oluşturur (Udemy tarzı)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📚 Örnek online kurs oluşturuluyor...'))
        
        # Öğretmen kontrolü
        teacher = Teacher.objects.filter(status='active').first()
        if not teacher:
            self.stdout.write(self.style.ERROR('❌ Aktif öğretmen bulunamadı'))
            return
        
        # Kurs oluştur
        course, created = Course.objects.get_or_create(
            code='PY101',
            defaults={
                'name': 'Python ile Programlamaya Giriş',
                'credits': 3,
                'description': 'Sıfırdan Python öğrenin. Bu kurs Python programlama dilinin temellerini öğretir. Video dersler, quizler ve opsiyonel ödevlerle pekiştirin.',
                'department': 'Bilgisayar Bilimleri',
                'semester': 'fall',
                'capacity': 1000,
                'course_type': 'online',
                'is_self_paced': True,
                'estimated_duration_hours': 20,
                'level': 'beginner',
                'status': 'active',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Kurs oluşturuldu: {course.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ Kurs zaten mevcut: {course.name}'))
            # Mevcut modülleri temizle (isteğe bağlı)
            # course.modules.all().delete()
        
        # Modül 1: Python'a Giriş
        module1, _ = CourseModule.objects.get_or_create(
            course=course,
            order=1,
            defaults={
                'title': '1. Python\'a Giriş',
                'description': 'Python dilinin temelleri ve kurulum',
                'is_active': True,
            }
        )
        self.stdout.write(f'  📁 Modül: {module1.title}')
        
        # Modül 1 - Ders 1: Python Nedir?
        lesson1_1, _ = Lesson.objects.get_or_create(
            module=module1,
            order=1,
            defaults={
                'title': 'Python Nedir?',
                'description': 'Python programlama dilinin tarihçesi ve kullanım alanları',
                'content_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=Y8Tko2YC5hA',
                'video_duration': 600,  # 10 dakika
                'is_mandatory': True,
                'is_preview': True,  # Önizleme için açık
            }
        )
        self.stdout.write(f'    📹 {lesson1_1.title}')
        
        # Modül 1 - Ders 2: Python Kurulumu
        lesson1_2, _ = Lesson.objects.get_or_create(
            module=module1,
            order=2,
            defaults={
                'title': 'Python Kurulumu',
                'description': 'Python ve IDE kurulumu adım adım',
                'content_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=x7X9w_GIm1s',
                'video_duration': 900,  # 15 dakika
                'is_mandatory': True,
            }
        )
        self.stdout.write(f'    📹 {lesson1_2.title}')
        
        # Modül 1 - Ders 3: Quiz
        quiz1, quiz1_created = Quiz.objects.get_or_create(
            course=course,
            title='Python Giriş Quiz',
            defaults={
                'created_by': teacher,
                'description': 'Python temel bilgiler testi',
                'quiz_type': 'quiz',
                'duration_minutes': 10,
                'is_published': True,
            }
        )
        
        if quiz1_created:
            # Quiz soruları
            q1 = QuizQuestion.objects.create(
                quiz=quiz1,
                order=1,
                text='Python hangi tür bir programlama dilidir?',
                explanation='Python yorumlanan (interpreted) bir dildir.'
            )
            c1_a = QuizChoice.objects.create(question=q1, label='A', text='Derlenmiş (Compiled)')
            c1_b = QuizChoice.objects.create(question=q1, label='B', text='Yorumlanan (Interpreted)')
            c1_c = QuizChoice.objects.create(question=q1, label='C', text='Assembly')
            c1_d = QuizChoice.objects.create(question=q1, label='D', text='Makine dili')
            q1.correct_choice = c1_b
            q1.save()
            
            q2 = QuizQuestion.objects.create(
                quiz=quiz1,
                order=2,
                text='Python dosyalarının uzantısı nedir?',
                explanation='Python dosyaları .py uzantısına sahiptir.'
            )
            c2_a = QuizChoice.objects.create(question=q2, label='A', text='.python')
            c2_b = QuizChoice.objects.create(question=q2, label='B', text='.pt')
            c2_c = QuizChoice.objects.create(question=q2, label='C', text='.py')
            c2_d = QuizChoice.objects.create(question=q2, label='D', text='.pyt')
            q2.correct_choice = c2_c
            q2.save()
        
        lesson1_3, _ = Lesson.objects.get_or_create(
            module=module1,
            order=3,
            defaults={
                'title': 'Giriş Quiz',
                'description': 'Python temelleri hakkında bilginizi test edin',
                'content_type': 'quiz',
                'quiz': quiz1,
                'is_mandatory': True,
            }
        )
        self.stdout.write(f'    ❓ {lesson1_3.title}')
        
        # Modül 2: Temel Kavramlar
        module2, _ = CourseModule.objects.get_or_create(
            course=course,
            order=2,
            defaults={
                'title': '2. Temel Kavramlar',
                'description': 'Değişkenler, veri tipleri ve operatörler',
                'is_active': True,
            }
        )
        self.stdout.write(f'  📁 Modül: {module2.title}')
        
        # Modül 2 - Ders 1: Değişkenler
        lesson2_1, _ = Lesson.objects.get_or_create(
            module=module2,
            order=1,
            defaults={
                'title': 'Değişkenler ve Veri Tipleri',
                'description': 'Python\'da değişken tanımlama ve temel veri tipleri',
                'content_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=OH86oLzVzzw',
                'video_duration': 1200,  # 20 dakika
                'is_mandatory': True,
            }
        )
        self.stdout.write(f'    📹 {lesson2_1.title}')
        
        # Modül 2 - Ders 2: Operatörler
        lesson2_2, _ = Lesson.objects.get_or_create(
            module=module2,
            order=2,
            defaults={
                'title': 'Operatörler',
                'description': 'Aritmetik, karşılaştırma ve mantıksal operatörler',
                'content_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=v5MR5JnKcZI',
                'video_duration': 900,  # 15 dakika
                'is_mandatory': True,
            }
        )
        self.stdout.write(f'    📹 {lesson2_2.title}')
        
        # Modül 2 - Ders 3: Opsiyonel Ödev
        lesson2_3, _ = Lesson.objects.get_or_create(
            module=module2,
            order=3,
            defaults={
                'title': 'Pratik: Hesap Makinesi',
                'description': 'Basit bir hesap makinesi programı yazın',
                'content_type': 'assignment',
                'is_assignment_optional': True,
                'assignment_description': '''
Bir hesap makinesi programı yazın:
- Kullanıcıdan iki sayı alın
- İşlem türünü sorun (+, -, *, /)
- Sonucu ekrana yazdırın

Bu ödev opsiyoneldir ve notlandırılmaz.
''',
                'is_mandatory': False,  # Opsiyonel
            }
        )
        self.stdout.write(f'    📝 {lesson2_3.title} (Opsiyonel)')
        
        # Modül 3: Kontrol Yapıları
        module3, _ = CourseModule.objects.get_or_create(
            course=course,
            order=3,
            defaults={
                'title': '3. Kontrol Yapıları',
                'description': 'if-else, döngüler ve fonksiyonlar',
                'is_active': True,
            }
        )
        self.stdout.write(f'  📁 Modül: {module3.title}')
        
        # Modül 3 - Ders 1: if-else
        lesson3_1, _ = Lesson.objects.get_or_create(
            module=module3,
            order=1,
            defaults={
                'title': 'if-else Yapıları',
                'description': 'Koşullu ifadeler ve karar yapıları',
                'content_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=Zp5MuPOtsSY',
                'video_duration': 1800,  # 30 dakika
                'is_mandatory': True,
            }
        )
        self.stdout.write(f'    📹 {lesson3_1.title}')
        
        # Modül 3 - Ders 2: Döngüler
        lesson3_2, _ = Lesson.objects.get_or_create(
            module=module3,
            order=2,
            defaults={
                'title': 'Döngüler (for ve while)',
                'description': 'for ve while döngüleri ile tekrarlayan işlemler',
                'content_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=94UHCEmprCY',
                'video_duration': 1500,  # 25 dakika
                'is_mandatory': True,
            }
        )
        self.stdout.write(f'    📹 {lesson3_2.title}')
        
        # Final Sınavı için Quiz oluştur
        final_quiz, final_created = Quiz.objects.get_or_create(
            course=course,
            title='Python Final Sınavı',
            defaults={
                'created_by': teacher,
                'description': 'Kurs tamamlama sınavı',
                'quiz_type': 'exam',
                'duration_minutes': 60,
                'is_published': True,
            }
        )
        
        if final_created:
            # Final soruları
            fq1 = QuizQuestion.objects.create(
                quiz=final_quiz,
                order=1,
                text='Python\'da yorum satırı yazmak için hangi karakter kullanılır?',
            )
            QuizChoice.objects.create(question=fq1, label='A', text='//')
            correct_fq1 = QuizChoice.objects.create(question=fq1, label='B', text='#')
            QuizChoice.objects.create(question=fq1, label='C', text='/*')
            QuizChoice.objects.create(question=fq1, label='D', text='--')
            fq1.correct_choice = correct_fq1
            fq1.save()
            
            fq2 = QuizQuestion.objects.create(
                quiz=final_quiz,
                order=2,
                text='Hangi veri tipi metin verisi saklar?',
            )
            QuizChoice.objects.create(question=fq2, label='A', text='int')
            QuizChoice.objects.create(question=fq2, label='B', text='float')
            correct_fq2 = QuizChoice.objects.create(question=fq2, label='C', text='str')
            QuizChoice.objects.create(question=fq2, label='D', text='bool')
            fq2.correct_choice = correct_fq2
            fq2.save()
            
            fq3 = QuizQuestion.objects.create(
                quiz=final_quiz,
                order=3,
                text='for döngüsü ile 1\'den 10\'a kadar sayılar yazdırmak için hangi kod kullanılır?',
            )
            QuizChoice.objects.create(question=fq3, label='A', text='for i in range(10):')
            correct_fq3 = QuizChoice.objects.create(question=fq3, label='B', text='for i in range(1, 11):')
            QuizChoice.objects.create(question=fq3, label='C', text='for i in (1, 10):')
            QuizChoice.objects.create(question=fq3, label='D', text='for i in 1..10:')
            fq3.correct_choice = correct_fq3
            fq3.save()
        
        # CourseExam oluştur
        exam, _ = CourseExam.objects.get_or_create(
            course=course,
            defaults={
                'quiz': final_quiz,
                'passing_score': 70.0,
                'max_attempts': 3,
                'duration_minutes': 60,
                'instructions': '''
Bu sınavı tamamlamak için tüm ders içeriğini bitirmiş olmalısınız.
- Toplam 3 deneme hakkınız vardır
- Geçme notu: 70
- Süre: 60 dakika
- Başarılı olursanız otomatik sertifika alacaksınız
''',
                'is_active': True,
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Örnek kurs başarıyla oluşturuldu!'))
        self.stdout.write(f'   Kurs: {course.code} - {course.name}')
        self.stdout.write(f'   Modül Sayısı: {course.modules.count()}')
        self.stdout.write(f'   Toplam Ders: {Lesson.objects.filter(module__course=course).count()}')
        self.stdout.write(f'   Final Sınavı: {exam}')
        self.stdout.write(self.style.SUCCESS(f'\n🎓 Kurs hazır! Admin panelden veya API üzerinden erişebilirsiniz.'))
