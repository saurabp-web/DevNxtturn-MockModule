# <your_app>/management/commands/backfill_pyq_occurrences.py
# (create empty __init__.py in management/ and management/commands/ if they do not exist)
#
#   python manage.py backfill_pyq_occurrences            # hashes + occurrences
#   python manage.py backfill_pyq_occurrences --seed-standard-chapters
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Fill duplicate-detection hashes and create QuestionOccurrence rows for existing PYQ questions."

    def add_arguments(self, parser):
        parser.add_argument("--seed-standard-chapters", action="store_true",
                            help="Group chapters under StandardChapter using the topic-engine aliases.")

    def handle(self, *args, **opts):
        from ...views import _backfill_pyq_occurrences, _seed_standard_chapters
        with transaction.atomic():
            result = _backfill_pyq_occurrences()
            self.stdout.write(self.style.SUCCESS(f"Backfill done: {result}"))
            if opts["seed_standard_chapters"]:
                linked = _seed_standard_chapters()
                self.stdout.write(self.style.SUCCESS(f"Chapters linked to a StandardChapter: {linked}"))