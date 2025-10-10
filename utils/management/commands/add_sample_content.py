from django.core.management.base import BaseCommand
from apps.courses.models import Course, CourseContent
from apps.teachers.models import Teacher
import random

class Command(BaseCommand):
    help = 'Derslere örnek haftalık içerik ekler'

    def handle(self, *args, **kwargs):
        # Örnek içerik başlıkları ve açıklamaları
        content_templates = [
            {
                'title': 'Giriş ve Temel Kavramlar',
                'description': 'Bu hafta dersin temel kavramlarını ve genel çerçevesini öğreneceğiz. Ders materyallerini inceleyiniz.',
                'type': 'lecture'
            },
            {
                'title': 'Teorik Temeller',
                'description': 'Konunun teorik altyapısı ve temel prensipleri. Sunum dosyasını mutlaka inceleyin.',
                'type': 'presentation'
            },
            {
                'title': 'Uygulama Örnekleri',
                'description': 'Gerçek dünya uygulamaları ve örnek çalışmalar. Video içeriğini izleyiniz.',
                'type': 'video'
            },
            {
                'title': 'İleri Düzey Konular',
                'description': 'Konunun daha detaylı incelenmesi ve ileri düzey örnekler.',
                'type': 'document'
            },
            {
                'title': 'Pratik Uygulamalar',
                'description': 'Öğrendiklerinizi pratiğe dökme zamanı. Örnek uygulamaları inceleyiniz.',
                'type': 'lecture'
            },
            {
                'title': 'Vaka Çalışmaları',
                'description': 'Gerçek vaka analizleri ve problem çözme yaklaşımları.',
                'type': 'presentation'
            },
            {
                'title': 'Ara Değerlendirme',
                'description': 'İlk yarının özeti ve ara değerlendirme. Tüm materyalleri gözden geçirin.',
                'type': 'document'
            },
            {
                'title': 'Yeni Yaklaşımlar',
                'description': 'Konuya modern yaklaşımlar ve güncel gelişmeler.',
                'type': 'lecture'
            },
            {
                'title': 'Karşılaştırmalı Analiz',
                'description': 'Farklı yöntemlerin karşılaştırılması ve değerlendirilmesi.',
                'type': 'presentation'
            },
            {
                'title': 'Proje Çalışması',
                'description': 'Grup projesi için gerekli bilgiler ve yönergeler.',
                'type': 'document'
            },
            {
                'title': 'İleri Teknikler',
                'description': 'Uzman seviyesi teknikler ve optimizasyon yöntemleri.',
                'type': 'lecture'
            },
            {
                'title': 'Endüstri Uygulamaları',
                'description': 'Sektördeki gerçek uygulamalar ve deneyimler.',
                'type': 'video'
            },
            {
                'title': 'Araştırma Metodları',
                'description': 'Bilimsel araştırma yöntemleri ve akademik çalışma teknikleri.',
                'type': 'document'
            },
            {
                'title': 'Final Hazırlık',
                'description': 'Dönem sonu değerlendirmesi için hazırlık materyalleri. Tüm konuları tekrar edin.',
                'type': 'presentation'
            }
        ]

        courses = Course.objects.all()
        
        if not courses.exists():
            self.stdout.write(self.style.WARNING('Hiç ders bulunamadı!'))
            return

        added_count = 0
        
        for course in courses:
            self.stdout.write(f'\n{course.code} - {course.name} için içerik ekleniyor...')
            
            # Her ders için 14 haftalık içerik ekle
            for week in range(1, 15):
                # Bu hafta için içerik var mı kontrol et
                existing = CourseContent.objects.filter(
                    course=course,
                    week_number=week
                ).first()
                
                if existing:
                    self.stdout.write(f'  Hafta {week}: Zaten mevcut, atlanıyor')
                    continue
                
                # Rastgele bir şablon seç
                template = content_templates[week - 1] if week <= len(content_templates) else random.choice(content_templates)
                
                # İçerik oluştur
                content = CourseContent.objects.create(
                    course=course,
                    week_number=week,
                    title=f"Hafta {week}: {template['title']}",
                    description=template['description'],
                    content_type=template['type'],
                    url=f'https://example.com/course/{course.code}/week{week}',
                    is_active=True
                )
                
                added_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [OK] Hafta {week}: {content.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nToplam {added_count} icerik eklendi!'))

