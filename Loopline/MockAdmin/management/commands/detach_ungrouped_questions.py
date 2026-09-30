# MockAdmin/management/commands/detach_ungrouped_questions.py
#
# One-off cleanup for questions that were ALREADY imported under the
# "Imported (Ungrouped)" chapter. They are removed from Practice (chapter link)
# and from the auto "Imported Questions" custom test, but stay in their mock
# tests (occurrences / mock_exam links are untouched).
#
#   python manage.py detach_ungrouped_questions            # dry run (prints counts)
#   python manage.py detach_ungrouped_questions --apply    # actually do it
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Detach 'Imported (Ungrouped)' questions from Practice and Custom tests."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write changes (default is a dry run).")

    def handle(self, *args, **opts):
        from ...models import Question, QuestionChapterMapping, TestDefinition
        from ...views import IMPORTED_CHAPTER_NAME, _custom_ids, _set_custom_ids

        qs = Question.objects.filter(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)
        q_ids = set(qs.values_list("pk", flat=True))
        maps = QuestionChapterMapping.objects.filter(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)
        customs = TestDefinition.objects.filter(test_type="Custom", test_name="Imported Questions")

        self.stdout.write(f"Questions under ungrouped chapter: {len(q_ids)}")
        self.stdout.write(f"Chapter mappings to remove:        {maps.count()}")
        self.stdout.write(f"Custom tests to clean:             {customs.count()}")

        if not opts["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to make changes."))
            return

        with transaction.atomic():
            maps.delete()
            qs.update(chapter=None)
            for t in customs:
                ids = _custom_ids(t)
                kept = [i for i in ids if i not in q_ids]
                if len(kept) != len(ids):
                    _set_custom_ids(t, kept)
        self.stdout.write(self.style.SUCCESS("Done."))