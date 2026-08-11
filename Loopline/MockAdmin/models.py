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

class Question(models.Model):
    question_id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, db_column='exam_id', null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, db_column='chapter_id', null=True, blank=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=50, null=True, blank=True)  # MCQ / MSQ / Numeric
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    image_url = models.ImageField(upload_to='question_images/', null=True, blank=True)
    hint = models.TextField(null=True, blank=True)
    difficulty_level = models.CharField(max_length=50, null=True, blank=True)
    is_previousyear = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'questions'

    def __str__(self):
        return f"Q{self.question_id}: {self.question_text[:60]}..."


class QuestionOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    option_e = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'question_options'

    def __str__(self):
        return f"Options for Question {self.question_id}"


class CorrectAnswer(models.Model):
    correct_answer_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='question_id')
    option_id = models.CharField(max_length=10)   # e.g. 'A', 'B', 'A,C' for MSQ, or numeric value

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