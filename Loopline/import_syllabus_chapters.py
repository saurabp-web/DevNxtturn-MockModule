"""
Bulk-imports (ExamName, SubjectName, ChapterName) rows from a syllabus
spreadsheet into the real Chapter table, filling in exactly the kind of
gap that leaves a subject with nothing but the "Imported (Ungrouped)"
fallback chapter.

Safe to re-run: existing (subject, chapter_name) pairs are skipped, not
duplicated. Reuses the exact same exam/subject matching the rest of the
app uses, so it never creates a stray duplicate Subject row.

Usage (inside the container):
    docker cp NEET_Botany_Zoology_Syllabus.xlsx nxtturn_backend:/app/syllabus.xlsx
    docker cp import_syllabus_chapters.py nxtturn_backend:/app/import_syllabus_chapters.py
    docker exec -it nxtturn_backend python manage.py shell -c "exec(open('/app/import_syllabus_chapters.py').read())"

To point at a different file, edit SYLLABUS_PATH below before copying in,
or set the SYLLABUS_PATH env var before running the shell command.
"""
import os
import openpyxl
from MockAdmin.models import Exam, Subject, Chapter

SYLLABUS_PATH = os.environ.get("SYLLABUS_PATH", "/app/syllabus.xlsx")

# Same normalisation the app's own _find_subject() applies: exact match,
# then a couple of common synonyms. Extend this if your data uses other
# spellings.
_SUBJECT_SYNONYMS = {
    "biology": None,  # NEET's "Biology" maps to Botany/Zoology individually below,
                       # never auto-created as its own subject here.
    "maths": "mathematics",
    "math": "mathematics",
}


def find_subject(exam, subject_name):
    name = (subject_name or "").strip()
    if not name:
        return None
    for candidate in (name, _SUBJECT_SYNONYMS.get(name.lower())):
        if not candidate:
            continue
        subj = Subject.objects.filter(exam=exam, subject_name__iexact=candidate).first()
        if subj:
            return subj
    return None


def run():
    wb = openpyxl.load_workbook(SYLLABUS_PATH)
    ws = wb.worksheets[0]

    created_subjects = 0
    created_chapters = 0
    skipped_existing = 0
    missing_exam = set()

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        exam_name, subject_name, chapter_name = (row + (None, None, None))[:3]
        if not (exam_name and subject_name and chapter_name):
            continue

        # Match loosely on exam name: strip spaces/hyphens so "NEET UG",
        # "NEET-UG", and "NEET_UG" all resolve to whatever the DB actually
        # calls it, instead of requiring an exact string match.
        target = str(exam_name).strip().lower().replace("-", "").replace(" ", "").replace("_", "")
        exam = next(
            (e for e in Exam.objects.all()
             if (e.exam_name or "").lower().replace("-", "").replace(" ", "").replace("_", "") == target),
            None,
        )
        if not exam:
            missing_exam.add(exam_name)
            continue

        subject = find_subject(exam, subject_name)
        if not subject:
            subject = Subject.objects.create(
                exam=exam, subject_name=str(subject_name).strip()
            )
            created_subjects += 1
            print(f"  + created Subject '{subject.subject_name}' under {exam.exam_name}")

        chapter_name = str(chapter_name).strip()
        exists = Chapter.objects.filter(
            subject=subject, chapter_name__iexact=chapter_name
        ).exists()
        if exists:
            skipped_existing += 1
            continue

        Chapter.objects.create(
            subject=subject, chapter_name=chapter_name, is_active=True
        )
        created_chapters += 1

    print("=" * 60)
    print(f"New subjects created:  {created_subjects}")
    print(f"New chapters created:  {created_chapters}")
    print(f"Already existed (skipped): {skipped_existing}")
    if missing_exam:
        print(f"WARNING - exam name(s) not found in DB, rows skipped: {missing_exam}")
    print("=" * 60)


run()
