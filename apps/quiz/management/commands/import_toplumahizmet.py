import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.quiz.models import QuestionBank, Question


ANSWER_RE = re.compile(r"^\s*(ANSWER|Answer|Cevap)\s*:\s*([A-Za-z])\s*$")
OPTION_RE = re.compile(r"^\s*([A-Ea-e])\)\s*(.+?)\s*$")


class Command(BaseCommand):
    help = "Import toplumahizmet.txt into a QuestionBank"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            dest="file",
            default=r"c:\\Users\\mtn2\\Downloads\\OKULPROJE\\toplumahizmet.txt",
            help="Path to toplumahizmet.txt",
        )
        parser.add_argument(
            "--bank",
            dest="bank",
            default="Topluma Hizmet",
            help="Question bank name",
        )
        parser.add_argument(
            "--shared",
            action="store_true",
            help="Create bank as shared",
        )
        parser.add_argument(
            "--owner",
            dest="owner",
            default="teacher1",
            help="Username of bank owner (teacher1/admin)",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        User = get_user_model()
        owner_username = options["owner"]
        owner = User.objects.filter(username=owner_username).first() or User.objects.filter(username="admin").first()

        bank, _ = QuestionBank.objects.get_or_create(
            name=options["bank"],
            defaults={
                "description": "Topluma Hizmet dersinden içe aktarılan sorular",
                "created_by": owner,
                "is_shared": bool(options.get("shared")) or True,
            },
        )

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

        created = 0
        skipped = 0

        for block in blocks:
            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if not lines:
                continue

            question_text = lines[0]
            options_map = {}
            answer_letter = None

            for ln in lines[1:]:
                m_ans = ANSWER_RE.match(ln)
                if m_ans:
                    answer_letter = m_ans.group(2).upper()
                    continue

                m_opt = OPTION_RE.match(ln)
                if m_opt:
                    options_map[m_opt.group(1).upper()] = m_opt.group(2).strip()

            # Determine type
            if options_map and answer_letter in {"A", "B", "C", "D", "E"}:
                q_type = "multiple_choice"
                correct = answer_letter
            else:
                # fallback
                q_type = "short_answer"
                correct = answer_letter or ""

            # idempotent: avoid duplicates by question text in same bank
            if Question.objects.filter(bank=bank, question_text=question_text).exists():
                skipped += 1
                continue

            q = Question.objects.create(
                bank=bank,
                question_type=q_type,
                difficulty="medium",
                question_text=question_text,
                points=1,
                option_a=options_map.get("A", ""),
                option_b=options_map.get("B", ""),
                option_c=options_map.get("C", ""),
                option_d=options_map.get("D", ""),
                option_e=options_map.get("E", ""),
                correct_answer=correct,
                explanation="",
                tags="topluma-hizmet",
            )
            created += 1

        # keep bank shared flag consistent
        if options.get("shared") and not bank.is_shared:
            bank.is_shared = True
            bank.save(update_fields=["is_shared"])

        self.stdout.write(self.style.SUCCESS(
            f"Imported to bank '{bank.name}': created={created}, skipped={skipped}"
        ))
