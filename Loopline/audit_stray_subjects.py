"""
Read-only audit: finds Subject rows that don't belong under their Exam,
by comparing against your master syllabus spreadsheets.

Run inside the container:
    docker exec -it nxtturn_backend python manage.py shell < audit_stray_subjects.py

Or paste into `docker exec -it nxtturn_backend python manage.py shell`.

This does NOT modify anything - it only prints a report.
"""
from MockAdmin.models import Exam, Subject, Chapter, Question

# Expected subjects per exam, from your syllabus spreadsheets.
# JEE_MAIN sheet only lists: Physics, Chemistry, Mathematics
# NEET_UG sheet only lists: Physics, Chemistry, Biology (your app splits
# Biology into Botany/Zoology, so both count as "expected" for NEET)
EXPECTED = {
    "JEE Main": {"physics", "chemistry", "mathematics"},
    "NEET UG":  {"physics", "chemistry", "biology", "botany", "zoology"},
}

print("=" * 70)
print("STRAY SUBJECT AUDIT")
print("=" * 70)

for exam in Exam.objects.all():
    expected = None
    for key, subs in EXPECTED.items():
        if key.lower() in (exam.exam_name or "").lower():
            expected = subs
            break
    if expected is None:
        continue  # skip exams we don't have a syllabus reference for

    subjects = Subject.objects.filter(exam=exam)
    for subj in subjects:
        norm = (subj.subject_name or "").strip().lower()
        chapters = Chapter.objects.filter(subject=subj)
        n_chapters = chapters.count()
        n_questions = Question.objects.filter(chapter__subject=subj).count()
        flag = "" if norm in expected else "  <-- STRAY (not in this exam's syllabus)"
        print(f"[{exam.exam_name}] {subj.subject_name!r} "
              f"({n_chapters} chapters, {n_questions} questions){flag}")

print("=" * 70)
print("Review the STRAY lines above before deciding whether to merge or delete.")
print("A stray subject with 0 or very few questions is likely safe to")
print("reassign - a stray subject with many questions may indicate a real")
print("exam-selection mistake during import that needs manual review.")
