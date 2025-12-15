from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.users.models import UserProfile
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.courses.models import (
    Course,
    CourseGroup,
    Enrollment,
    Assignment,
    Submission,
    Announcement,
    CourseContent,
)
from apps.notes.models import Note
from apps.gradebook.models import GradeCategory, GradeItem, Grade
from apps.forum.models import DirectMessage, MessageThread


User = get_user_model()


class Command(BaseCommand):
    """
    Demo/Sample verilerini temizler.

    Neleri siler?
    - create_sample_data komutunun oluşturduğu kullanıcılar:
      admin, teacher1/2, student1/2/3 ve onların UserProfile kayıtları
    - BM101 / BM201 / BM301 dersleri ve bağlı tüm gruplar, kayıtlar, ödevler,
      teslimler, duyurular, ders içerikleri
    - Bu demo ders/gruplara bağlı tüm notlar (Note, GradeCategory, GradeItem, Grade)
    - Demo kullanıcılar arasındaki mesajlaşmalar (DirectMessage, MessageThread)

    Gerçek (kendi eklediğiniz) kullanıcı, ders ve veriler bu komuttan etkilenmez
    (farklı kullanıcı adları ve ders kodları kullandığınız sürece).
    """

    help = "create_sample_data tarafından oluşturulan demo verileri temizler"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Demo/sample veriler temizleniyor..."))

        demo_usernames = ["admin", "teacher1", "teacher2", "student1", "student2", "student3"]
        demo_course_codes = ["BM101", "BM201", "BM301"]

        # 1) Demo kullanıcıları bul
        demo_users = User.objects.filter(username__in=demo_usernames)
        demo_user_ids = list(demo_users.values_list("id", flat=True))

        # 2) Demo öğretmen ve öğrenciler
        demo_teachers = Teacher.objects.filter(user_id__in=demo_user_ids)
        demo_students = Student.objects.filter(user_id__in=demo_user_ids)

        # 3) Demo dersler ve gruplar
        demo_courses = Course.objects.filter(code__in=demo_course_codes)
        demo_groups = CourseGroup.objects.filter(course__in=demo_courses) | CourseGroup.objects.filter(
            teacher__in=demo_teachers
        )
        demo_groups = demo_groups.distinct()

        group_ids = list(demo_groups.values_list("id", flat=True))
        course_ids = list(demo_courses.values_list("id", flat=True))

        # 4) Bu gruplara bağlı kayıtlar
        demo_enrollments = Enrollment.objects.filter(group_id__in=group_ids)

        # 5) Bu gruplara bağlı ödev/duyuru/içerik ve teslimler
        demo_assignments = Assignment.objects.filter(group_id__in=group_ids)
        demo_submissions = Submission.objects.filter(assignment__in=demo_assignments)
        demo_announcements = Announcement.objects.filter(group_id__in=group_ids)
        demo_contents = CourseContent.objects.filter(course_id__in=course_ids)

        # 6) Bu dersler ve öğrenciler için klasik notlar (Note)
        demo_notes = Note.objects.filter(course_id__in=course_ids) | Note.objects.filter(
            teacher_id__in=demo_user_ids
        )
        demo_notes = demo_notes.distinct()

        # 7) Gradebook verileri
        demo_categories = GradeCategory.objects.filter(course_group_id__in=group_ids)
        demo_items = GradeItem.objects.filter(category__in=demo_categories)
        demo_grades = Grade.objects.filter(item__in=demo_items)

        # 8) Demo kullanıcılar arasındaki mesajlaşmalar
        demo_threads = MessageThread.objects.filter(
            sender_id__in=demo_user_ids
        ) | MessageThread.objects.filter(recipient_id__in=demo_user_ids)
        demo_threads = demo_threads.distinct()
        demo_messages = DirectMessage.objects.filter(
            sender_id__in=demo_user_ids
        ) | DirectMessage.objects.filter(recipient_id__in=demo_user_ids)
        demo_messages = demo_messages.distinct()

        # SİLME SIRASI (FK hatası yaşamamak için ters sıradan başlayalım)
        counts = {}

        # Mesajlar
        counts["direct_messages"] = demo_messages.count()
        demo_messages.delete()
        counts["message_threads"] = demo_threads.count()
        demo_threads.delete()

        # Gradebook
        counts["grades"] = demo_grades.count()
        demo_grades.delete()
        counts["grade_items"] = demo_items.count()
        demo_items.delete()
        counts["grade_categories"] = demo_categories.count()
        demo_categories.delete()

        # Notlar
        counts["notes"] = demo_notes.count()
        demo_notes.delete()

        # Ödev teslimleri / ödevler / duyurular / içerikler
        counts["submissions"] = demo_submissions.count()
        demo_submissions.delete()
        counts["assignments"] = demo_assignments.count()
        demo_assignments.delete()
        counts["announcements"] = demo_announcements.count()
        demo_announcements.delete()
        counts["contents"] = demo_contents.count()
        demo_contents.delete()

        # Kayıtlar ve gruplar
        counts["enrollments"] = demo_enrollments.count()
        demo_enrollments.delete()
        counts["course_groups"] = demo_groups.count()
        demo_groups.delete()

        # Dersler
        counts["courses"] = demo_courses.count()
        demo_courses.delete()

        # Öğrenci & öğretmen modelleri
        counts["students"] = demo_students.count()
        demo_students.delete()
        counts["teachers"] = demo_teachers.count()
        demo_teachers.delete()

        # UserProfile ve User
        profiles = UserProfile.objects.filter(user_id__in=demo_user_ids)
        counts["profiles"] = profiles.count()
        profiles.delete()

        counts["users"] = demo_users.count()
        demo_users.delete()

        # Özet
        self.stdout.write(self.style.SUCCESS("Demo verileri temizlendi. Silinen kayıt sayıları:"))
        for key, value in counts.items():
            self.stdout.write(f"  - {key}: {value}")

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Artık sistemde sadece sizin manuel eklediğiniz gerçek dersler / notlar / ödevler kalmış olmalı.\n"
                "Gerekirse create_sample_data komutunu bir daha ÇALIŞTIRMAYIN; sadece gerçek verilerinizi kullanın."
            )
        )

