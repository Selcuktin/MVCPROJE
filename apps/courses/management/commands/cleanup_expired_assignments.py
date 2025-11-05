from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import Assignment


class Command(BaseCommand):
    help = "Delete assignments whose due_date is older than 7 days"

    def handle(self, *args, **options):
        threshold = timezone.now() - timezone.timedelta(days=7)
        qs = Assignment.objects.filter(due_date__lt=threshold)
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired assignments."))


