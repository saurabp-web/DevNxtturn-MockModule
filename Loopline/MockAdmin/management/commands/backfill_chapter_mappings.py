from django.core.management.base import BaseCommand
from MockAdmin.models import Question, QuestionChapterMapping


class Command(BaseCommand):
    help = "Backfill QuestionChapterMapping records from existing Question.chapter assignments."

    def handle(self, *args, **options):
        qs = Question.objects.filter(chapter__isnull=False)
        total = qs.count()
        self.stdout.write(f"Found {total} questions with chapters.")

        mappings = []
        created = 0
        for q in qs.iterator(chunk_size=1000):
            mappings.append(
                QuestionChapterMapping(
                    question_id=q.question_id,
                    chapter_id=q.chapter_id,
                    is_primary=True,
                    source="legacy",
                    confidence=100,
                )
            )
            if len(mappings) >= 1000:
                QuestionChapterMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                created += len(mappings)
                mappings = []

        if mappings:
            QuestionChapterMapping.objects.bulk_create(mappings, ignore_conflicts=True)
            created += len(mappings)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully backfilled mappings. Total mappings in DB: {QuestionChapterMapping.objects.count()}"
            )
        )
