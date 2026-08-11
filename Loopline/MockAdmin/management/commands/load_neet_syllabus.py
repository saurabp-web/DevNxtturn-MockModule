"""
Django management command: load_neet_syllabus

Reads the NEET UG syllabus JSON (produced by `scrape_neet_syllabus`) and
loads it into the database as:

    Exam (NEET UG, 2026)
      └── Subject (Physics / Biology / Chemistry)
            └── Chapter
                  └── Topic

USAGE
-----
    python manage.py load_neet_syllabus /path/to/neet_syllabus.json
    python manage.py load_neet_syllabus /path/to/neet_syllabus.json --dry-run
    python manage.py load_neet_syllabus /path/to/neet_syllabus.json --flush

The command is idempotent: running it twice will NOT create duplicate
Exam/Subject/Chapter/Topic rows — it uses get_or_create / update_or_create
matched on the natural keys (exam_code, subject name + exam, chapter name +
subject, topic name + chapter).

FIELD NAMES (confirmed against your real Exam/Subject models)
---------------------------------------------------------------
Everything model-specific is confined to the FIELD NAMES block and the
get_or_create_exam / get_or_create_subject helpers below.

Exam fields used: exam_code, exam_name, exam_year, conducting_body,
    exam_category, estimated_time_hours

Subject fields used: exam (FK), subject_name
(Subject.teacher is left as NULL — it isn't part of the syllabus import;
assign teachers separately if/when needed.)

INSTALLATION
------------
Place this file at: <your_app>/management/commands/load_neet_syllabus.py
(same app that already has scrape_neet_syllabus.py, or any app with access
to your models).

Update the import line below to point at wherever your Exam, Subject,
Chapter, Topic models actually live.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# --------------------------------------------------------------------- #
# EDIT THESE IMPORTS to match your actual app / models module.
# --------------------------------------------------------------------- #
from MockAdmin.models import Exam, Subject, Chapter, Topic  # noqa: E402

# --------------------------------------------------------------------- #
# ASSUMED FIELD NAMES — adjust here if your models differ.
# --------------------------------------------------------------------- #
LINK_SUBJECT_TO_EXAM = True  # set False if Subject has no `exam` FK

EXAM_DEFAULTS = {
    "exam_code": "NEET_UG",
    "exam_name": "National Eligibility cum Entrance Test (Undergraduate)",
    "exam_year": 2026,
    "conducting_body": "NTA",
    "exam_category": "Medical Entrance Exam",
    "estimated_time_hours": 3,
}


class Command(BaseCommand):
    help = "Load the scraped NEET UG syllabus JSON into Exam/Subject/Chapter/Topic tables."

    # Default path used when no json_file argument is passed on the command
    # line. Edit this to wherever your file actually lives.
    DEFAULT_JSON_PATH = r"C:\Users\hp\Desktop\nxtturn\nxtturn\Loopline\neet_syllabus.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            nargs="?",
            default=self.DEFAULT_JSON_PATH,
            help=(
                "Path to the neet_syllabus.json file (from scrape_neet_syllabus). "
                f"Defaults to: {self.DEFAULT_JSON_PATH}"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and print what WOULD be created/updated, without writing to the DB.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing Chapters/Topics for this Exam's subjects before loading "
            "(useful for re-importing a corrected syllabus). Exam/Subject rows are kept.",
        )

    def handle(self, *args, **options):
        json_path = Path(options["json_file"])
        dry_run = options["dry_run"]
        flush = options["flush"]

        if not json_path.exists():
            raise CommandError(f"File not found: {json_path}")

        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)

        subjects_data = data.get("subjects", {})
        if not subjects_data:
            raise CommandError("No 'subjects' key found in the JSON file.")

        if dry_run:
            self._dry_run_report(subjects_data)
            return

        with transaction.atomic():
            exam = self.get_or_create_exam()
            self.stdout.write(self.style.SUCCESS(f"Exam ready: {exam}"))

            if flush:
                self._flush_existing(exam, subjects_data.keys())

            total_subjects = 0
            total_chapters = 0
            total_topics = 0

            for subject_name, chapters in subjects_data.items():
                subject_obj = self.get_or_create_subject(exam, subject_name)
                total_subjects += 1

                for chapter_entry in chapters:
                    chapter_name = chapter_entry["chapter"].strip()
                    topics_list = chapter_entry.get("topics_list") or []

                    chapter_obj, _ = Chapter.objects.get_or_create(
                        subject=subject_obj,
                        chapter_name=chapter_name,
                    )
                    total_chapters += 1

                    for topic_name in topics_list:
                        topic_name = topic_name.strip()
                        if not topic_name:
                            continue
                        Topic.objects.get_or_create(
                            chapter=chapter_obj,
                            topic_name=topic_name,
                        )
                        total_topics += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Subjects: {total_subjects}, Chapters: {total_chapters}, "
                f"Topics: {total_topics}"
            )
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def get_or_create_exam(self):
        exam, created = Exam.objects.get_or_create(
            exam_code=EXAM_DEFAULTS["exam_code"],
            defaults=EXAM_DEFAULTS,
        )
        if created:
            self.stdout.write(f"  Created Exam: {exam}")
        else:
            self.stdout.write(f"  Found existing Exam: {exam}")
        return exam

    def get_or_create_subject(self, exam, subject_name):
        subject_name = subject_name.strip()
        if LINK_SUBJECT_TO_EXAM:
            subject_obj, created = Subject.objects.get_or_create(
                exam=exam,
                subject_name=subject_name,
            )
        else:
            subject_obj, created = Subject.objects.get_or_create(
                subject_name=subject_name,
            )
        if created:
            self.stdout.write(f"  Created Subject: {subject_obj}")
        return subject_obj

    def _flush_existing(self, exam, subject_names):
        if LINK_SUBJECT_TO_EXAM:
            subjects = Subject.objects.filter(exam=exam, subject_name__in=subject_names)
        else:
            subjects = Subject.objects.filter(subject_name__in=subject_names)

        chapter_qs = Chapter.objects.filter(subject__in=subjects)
        topic_count = Topic.objects.filter(chapter__in=chapter_qs).count()
        chapter_count = chapter_qs.count()

        Topic.objects.filter(chapter__in=chapter_qs).delete()
        chapter_qs.delete()

        self.stdout.write(
            self.style.WARNING(
                f"  --flush: removed {chapter_count} chapters and {topic_count} topics "
                f"for subjects {list(subject_names)}"
            )
        )

    def _dry_run_report(self, subjects_data):
        self.stdout.write(self.style.WARNING("DRY RUN — no database changes will be made.\n"))
        self.stdout.write(f"Exam: {EXAM_DEFAULTS['exam_name']} ({EXAM_DEFAULTS['exam_code']}, "
                           f"{EXAM_DEFAULTS['exam_year']})")
        for subject_name, chapters in subjects_data.items():
            topic_count = sum(len(c.get("topics_list") or []) for c in chapters)
            self.stdout.write(
                f"  Subject: {subject_name} -> {len(chapters)} chapters, {topic_count} topics"
            )
            for chapter_entry in chapters:
                n = len(chapter_entry.get("topics_list") or [])
                self.stdout.write(f"    - {chapter_entry['chapter']} ({n} topics)")


# ---------------------------------------------------------------------- #
# SETUP NOTES
# ---------------------------------------------------------------------- #
# 1. Fix the model import at the top:
#        from yourapp.models import Exam, Subject, Chapter, Topic
#
# 2. If your Exam/Subject field names differ from the ASSUMED FIELD NAMES
#    section above, update EXAM_DEFAULTS and get_or_create_subject().
#
# 3. Run:
#        python manage.py load_neet_syllabus neet_syllabus.json --dry-run
#    to preview, then without --dry-run to actually write to the DB.
# ---------------------------------------------------------------------- #