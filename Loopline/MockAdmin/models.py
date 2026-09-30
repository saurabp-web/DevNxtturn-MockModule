# =============New Models for Loopline/MockAdmin =====================    

from datetime import timezone

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ─────────────────────────────────────────────
# 2. MASTER / REFERENCE DATA
# ─────────────────────────────────────────────

class State(models.Model):
    state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=100)
    state_code = models.CharField(max_length=10)

    class Meta:
        db_table = 'states'

    def __str__(self):
        return self.state_name


class Board(models.Model):
    board_id = models.AutoField(primary_key=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, db_column='state_id')
    board_name = models.CharField(max_length=255)
    board_code = models.CharField(max_length=50)

    class Meta:
        db_table = 'boards'

    def __str__(self):
        return self.board_name


class Stream(models.Model):
    stream_id = models.AutoField(primary_key=True)
    stream_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'streams'

    def __str__(self):
        return self.stream_name


class Field(models.Model):
    field_id = models.AutoField(primary_key=True)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, db_column='stream_id')
    field_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'fields'

    def __str__(self):
        return self.field_name


class SubField(models.Model):
    sub_field_id = models.AutoField(primary_key=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, db_column='field_id')
    sub_field_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'sub_fields'

    def __str__(self):
        return self.sub_field_name


class EducationLevel(models.Model):
    education_level_id = models.AutoField(primary_key=True)
    education_level = models.CharField(max_length=100)  # 10th / 12th / Graduation / PG
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'education_levels'

    def __str__(self):
        return self.education_level


# ─────────────────────────────────────────────
# 4. EXAM CLASSIFICATION
# ─────────────────────────────────────────────

class ExamType(models.Model):
    exam_type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100)   # School / Entrance / Job
    description = models.TextField(null=True, blank=True)
    # FIX: EducationLevelListView (views.py) filters on
    # `exam_types__exam_type_id`, which requires this reverse relation to
    # exist. It was missing from this file, causing:
    #   FieldError: Cannot resolve keyword 'exam_types' into field.
    # NOTE: migrations 0012 and 0014 (MockAdmin/migrations) already add
    # this exact field to the database — showmigrations confirms both are
    # applied. So the DB column/through-table already exist; only the
    # Python model class was missing this declaration. No new migration
    # needed — just add this field back here and restart the app so
    # Django reloads the model with it.
    education_levels = models.ManyToManyField(
        EducationLevel, related_name='exam_types', blank=True,
    )

    class Meta:
        db_table = 'exam_types'

    def __str__(self):
        return self.type_name


class SchoolExamCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, db_column='exam_type_id')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, db_column='education_level_id')
    category_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'school_exam_categories'

    def __str__(self):
        return self.category_name


class EntranceExamCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, db_column='exam_type_id')
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, db_column='education_level_id')
    category_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'entrance_exam_categories'

    def __str__(self):
        return self.category_name


class JobCategory(models.Model):
    job_category_id = models.AutoField(primary_key=True)
    job_category_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'job_category'

    def __str__(self):
        return self.job_category_name


class JobExamCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, db_column='exam_type_id')
    job_category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, db_column='job_category_id')
    category_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'job_exam_categories'

    def __str__(self):
        return self.category_name


# ─────────────────────────────────────────────
# 3. EXAMS CATALOG
# ─────────────────────────────────────────────

class ExamLevel(models.Model):
    level_id = models.AutoField(primary_key=True)
    level_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)  # Central / State / University

    class Meta:
        db_table = 'exam_levels'

    def __str__(self):
        return self.level_name


class Exam(models.Model):
    exam_id = models.AutoField(primary_key=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, null=True, blank=True, db_column='exam_type_id')
    category_id = models.IntegerField(null=True, blank=True)   # generic FK to one of the 3 category tables
    # CHANGED: was a single ForeignKey (education_level_id / stream_id columns).
    # Source data (exams_by_type_merged.json) carries MULTIPLE education levels
    # and streams per exam (e.g. JEE Main -> streams: [science, cse, mechanical,
    # civil, electrical, ece, it, chemical, aerospace]). A single FK can only
    # hold one value, so the importer was forced to keep just the first tag and
    # silently drop the rest — meaning filtering by any non-first tag (e.g.
    # stream=mechanical) returned zero matches even though the exam applies.
    # M2M lets every tag be stored and filtered on. Django auto-creates a
    # 'exams_education_levels' / 'exams_streams' through-table (no db_column
    # needed here — that only applies to FK/O2O columns on this table).
    education_levels = models.ManyToManyField(EducationLevel, blank=True, related_name='exams')
    streams = models.ManyToManyField(Stream, blank=True, related_name='exams')
    field = models.ForeignKey(Field, on_delete=models.SET_NULL, null=True, blank=True, db_column='field_id')
    sub_field = models.ForeignKey(SubField, on_delete=models.SET_NULL, null=True, blank=True, db_column='sub_field_id')
    board = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True, blank=True, db_column='board_id')
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, db_column='state_id')
    level = models.ForeignKey(ExamLevel, on_delete=models.SET_NULL, null=True, blank=True, db_column='level_id')
    exam_name = models.CharField(max_length=255)
    exam_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    conducting_body = models.CharField(max_length=255, null=True, blank=True)
    exam_pattern = models.TextField(null=True, blank=True)
    logo = models.URLField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_trending = models.BooleanField(default=False, db_index=True)
    trending_score = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'exams'

    def __str__(self):
        return f"{self.exam_code} - {self.exam_name}"
    

class MockExam(models.Model):
    mockexam_id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, db_column='exam_id')
    mockexam_name = models.CharField(max_length=255)
    year = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    # ADDED: Create Mock Test wizard's "Set Pattern" step (step 3) collects
    # total_questions, marks_per_question, negative_marking,
    # sectional_time_minutes, and a per-subject breakdown
    # (e.g. [{"subject_id": 1, "name": "Physics", "questions": 30, "marks": 120}]).
    # None of that maps onto an existing column/table — storing it as one
    # JSONField here avoids a new join table for what is fundamentally a
    # denormalized "test blueprint" the frontend only ever reads/writes as
    # a whole, not queries into individually.
    pattern = models.JSONField(default=dict, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = 'mockexams'
 
    def __str__(self):
        return f"{self.mockexam_name} ({self.year})"


class Subject(models.Model):
    subject_id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, db_column='exam_id')
    subject_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return f"{self.subject_name} ({self.exam})"

class Chapter(models.Model):
    chapter_id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, db_column='subject_id')
    chapter_name = models.CharField(max_length=255)
    chapter_order = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'chapters'

    def __str__(self):
        return f"{self.chapter_name} ({self.subject})"


# ─────────────────────────────────────────────
# 5. QUESTION BANK (CORE)
# ─────────────────────────────────────────────

from django.utils import timezone


class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, db_column='exam_id', null=True, blank=True)
    mock_exam = models.ForeignKey(MockExam, on_delete=models.CASCADE, db_column='mockexam_name', null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, db_column='chapter_id', null=True, blank=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, null=True, blank=True)  # MCQ / MSQ / Numeric
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # CHANGED: was ImageField (single file only). Import_Mock.py needs to
    # store MULTIPLE stem diagram URLs per question — {"images": [url, ...]}
    # — same pattern as Solution.image_url below. A single ImageField can't
    # hold a dict, which is what caused:
    #   AttributeError: 'dict' object has no attribute 'name'
    # at question.save() during import.
    image_url = models.JSONField(default=dict, null=True, blank=True)
    hint = models.TextField(null=True, blank=True)
    difficulty_level = models.CharField(max_length=50, null=True, blank=True)
    is_previousyear = models.BooleanField(default=False)
    # PYQ (Previous Year Question) source metadata — only meaningful when
    # is_previousyear=True. All nullable since a non-PYQ question has none
    # of these, and pyq_session is optional even on PYQ questions.
    pyq_exam = models.ForeignKey(
        Exam, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='pyq_exam_id', related_name='pyq_questions'
    )
    pyq_year = models.IntegerField(null=True, blank=True)
    pyq_session = models.CharField(max_length=50, null=True, blank=True)  # e.g. 'Shift 1', 'Shift 2'

     # ── ADDED: duplicate detection ────────────────────────────────────
    # Fingerprints of the normalised text. text_hash = stem only,
    # content_hash = stem + options. Indexed so the "does this question
    # already exist?" lookup is one fast query.
    text_hash = models.CharField(max_length=64, db_index=True, blank=True, default='')
    content_hash = models.CharField(max_length=64, db_index=True, blank=True, default='')

     # ── ADDED: every exam/year this question appeared in ──────────────
    # List of dicts, e.g.
    # [
    #   {"exam_id": 1, "exam_code": "JEE_MAIN", "exam_name": "JEE Main", "year": 2024, "session": "",        "question_number": 12, "source": "pdf"},
    #   {"exam_id": 1, "exam_code": "JEE_MAIN", "exam_name": "JEE Main", "year": 2019, "session": "Shift 1", "question_number": null, "source": "manual"},
    #   {"exam_id": 2, "exam_code": "NEET",     "exam_name": "NEET",     "year": 2015, "session": "",        "question_number": null, "source": "pdf"}
    # ]
    # Exam name/code are stored inside each entry so the UI can show them
    # without extra joins.
    appearances = models.JSONField(default=list, blank=True)
    # ── ADDED: where this question is available / used ────────────────
    # Default False. Set by the "Add to Test" flow (see add_to_tests below).
    # These are per-QUESTION availability flags, not per-user.
    is_practice = models.BooleanField(default=False, db_index=True)  # shown in Practice tests (needs chapter)
    is_custom = models.BooleanField(default=False, db_index=True)    # selectable in Custom tests (needs chapter)
    is_mock = models.BooleanField(default=False, db_index=True)      # part of a PYQ Mock test

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)


    class Meta:
        db_table = 'questions'

    def add_appearance(self, exam, year, session="", question_number=None,
                       source="pdf", paper="", mock_exam=None,
                       source_file="", added_at=None):
        """
        Record that this question appeared in (exam, year, session, paper).
        Returns True if anything on the row changed, so the caller knows to save.
        - Same exam/year/session/paper (and same mock) is never added twice;
          if it already exists, its details are refreshed instead.
        - Also keeps the legacy pyq_exam / pyq_year / pyq_session fields
          pointing at the first appearance.
        - Each entry also stores display fields: year_label ("2012 (26 May)")
          and appearance ("Q58").
        """
        session = session or ""
        paper = paper or ""
        mock_id = mock_exam.pk if mock_exam is not None else None

        apps = list(self.appearances or [])
        changed = False

        def same_paper(a):
            return (a.get("exam_id") == exam.pk
                    and a.get("year") == year
                    and (a.get("session") or "") == session
                    and (a.get("paper") or "") == paper)

        # NEW: builds the display fields for one entry
        def display_fields(a):
            extra = " ".join(x for x in [(a.get("session") or "").strip(),
                                         (a.get("paper") or "").strip()] if x)
            qn = a.get("question_number")
            return {
                "year_label": f"{a.get('year')} ({extra})" if extra else a.get("year"),
                "appearance": f"Q{qn}" if qn not in (None, "") else "",
            }

        entry = None
        for a in apps:
            if same_paper(a) and a.get("mock_exam_id") == mock_id:
                entry = a
                break
        if entry is None and mock_id is not None:
            # Same paper saved earlier without a mock: attach the mock to it.
            for a in apps:
                if same_paper(a) and a.get("mock_exam_id") is None:
                    a["mock_exam_id"] = mock_id
                    entry = a
                    changed = True
                    break

        if entry is None:
            entry = {
                "exam_id": exam.pk,
                "exam_name": getattr(exam, "exam_name", None) or str(exam),
                "year": year,
                "session": session,
                "paper": paper,
                "question_number": question_number,
                "mock_exam_id": mock_id,
                "source": source,
                "source_file": source_file or "",
                "added_at": added_at or timezone.now().isoformat(),
            }
            apps.append(entry)
            changed = True
        else:
            # Edited paper details / re-upload: update the existing entry.
            for key, val in (("question_number", question_number),
                             ("source_file", source_file or "")):
                if val not in (None, "") and entry.get(key) != val:
                    entry[key] = val
                    changed = True

        # NEW: set/refresh display fields (also backfills older entries
        # that were saved before these keys existed)
        for k, v in display_fields(entry).items():
            if entry.get(k) != v:
                entry[k] = v
                changed = True

        if changed:
            self.appearances = apps

        if not self.is_previousyear:
            self.is_previousyear = True
            changed = True
        if not self.pyq_exam_id:
            self.pyq_exam = exam
            self.pyq_year = year
            self.pyq_session = session or None
            changed = True

        return changed


    def __str__(self):
        return f"Q{self.question_id}: {self.question_text[:60]}..."


class QuestionChapterMapping(models.Model):
    """
    Many-to-many bridge: one Question can be mapped to multiple Chapters
    across multiple exams/syllabi.

    Examples:
      • JEE Main 2021 Q3  → Chapter "Laws of Motion"   (Physics, JEE Main)
      • Same question     → Chapter "Newton's Laws"     (Physics, NEET)
      • Same question     → Chapter "Dynamics"          (Physics, JEE Advanced)

    is_primary: True for the chapter assigned at import time (the "home" chapter
                for Practice test filtering). Only one row per question should
                be primary=True, enforced at the application layer.

    source:     "ai"      - mapped by OpenRouter AI
                "rules"   - mapped by keyword/rule engine
                "manual"  - admin override in the review UI
                "legacy"  - the old Question.chapter FK value (migrated)
    """
    mapping_id   = models.AutoField(primary_key=True)
    question     = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='chapter_mappings', db_column='question_id'
    )
    chapter      = models.ForeignKey(
        Chapter, on_delete=models.CASCADE,
        related_name='question_mappings', db_column='chapter_id'
    )
    is_primary   = models.BooleanField(default=True)
    source       = models.CharField(
        max_length=20,
        choices=[("ai", "AI"), ("rules", "Rules"), ("manual", "Manual"), ("legacy", "Legacy")],
        default="ai"
    )
    confidence   = models.SmallIntegerField(default=0)   # 0–100
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'question_chapter_mappings'
        unique_together = [('question', 'chapter')]     # no duplicate pairs

    def __str__(self):
        return f"Q{self.question_id} → {self.chapter.chapter_name} ({'primary' if self.is_primary else 'secondary'})"



class QuestionOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    option_e = models.TextField(null=True, blank=True)
    # ADDED: previously QuestionOption had no way to store an image at all,
    # so graph-based options (e.g. a question where A/B/C/D are each a
    # different graph, not text) were silently dropped on import — logged
    # as a warning and never persisted. One JSONField holding
    # {"A": url, "B": url, ...} covers all four/five options without
    # needing four separate image columns.
    option_images = models.JSONField(default=dict, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'question_options'

    def __str__(self):
        return f"Options for Question {self.question_id}"


class CorrectAnswer(models.Model):
    correct_answer_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    option_id = models.TextField()    # e.g. 'A', 'B', 'A,C' for MSQ, or numeric value

    class Meta:
        db_table = 'correct_answers'

    def __str__(self):
        return f"Answer for Q{self.question_id}: {self.option_id}"


class Solution(models.Model):
    solution_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id',null=True, blank=True)
    explaination_text = models.TextField()
    image_url = models.JSONField(default=dict,null=True, blank=True)
    hints = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'solution'

    def __str__(self):
        return f"Solution for Question {self.question_id}"


class QuestionAnalytics(models.Model):
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='question_id'
    )
    total_attempts = models.IntegerField(default=0)
    correct_attempts = models.IntegerField(default=0)
    wrong_attempts = models.IntegerField(default=0)
    skipped_attempts = models.IntegerField(default=0)
    accuracy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    avg_time_taken = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    difficulty_index = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'question_analytics'

    def __str__(self):
        return f"Analytics for Q{self.pk}"


# ─────────────────────────────────────────────
# 6. TEST & ATTEMPT SYSTEM
# ─────────────────────────────────────────────

class TestDefinition(models.Model):
    TEST_TYPE_CHOICES = [
        ('Practice', 'Practice'),
        ('Custom', 'Custom'),
        ('Mock', 'Mock'),
    ]
    test_id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, db_column='exam_id')
    mockexam = models.ForeignKey(MockExam, on_delete=models.SET_NULL, null=True, blank=True, db_column='mockexam_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, db_column='user_id')
    test_name = models.CharField(max_length=255)
    test_type = models.CharField(max_length=50, choices=TEST_TYPE_CHOICES)
    description = models.TextField(null=True, blank=True)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_definitions'

    def __str__(self):
        return f"{self.test_name} ({self.test_type})"


class TestSession(models.Model):
    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    session_id = models.AutoField(primary_key=True)
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, db_column='test_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Progress')
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'test_sessions'

    def __str__(self):
        return f"Session {self.session_id} - {self.user} - {self.test}"



# ─────────────────────────────────────────────
# 7. QUESTION REPORT
# ─────────────────────────────────────────────

class QuestionReport(models.Model):
    report_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    session = models.ForeignKey(TestSession, on_delete=models.SET_NULL, null=True, blank=True, db_column='session_id')
    reason = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'question_reports'

    def __str__(self):
        return f"Report {self.report_id} on Q{self.question_id} by {self.user}"


# ─────────────────────────────────────────────
# 8. FEEDBACK
# ─────────────────────────────────────────────

class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    result = models.ForeignKey(TestSession, on_delete=models.CASCADE, db_column='result_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    stars = models.PositiveSmallIntegerField()   # 1-5
    feedback_text = models.TextField(null=True, blank=True)
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback'

    def __str__(self):
        return f"Feedback {self.feedback_id} by {self.user} - {self.stars} stars"