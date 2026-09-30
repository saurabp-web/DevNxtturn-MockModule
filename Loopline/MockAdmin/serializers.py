# from rest_framework import serializers
# from .models import (
#     State, Board, Stream, Field, SubField, EducationLevel,
#     ExamType, SchoolExamCategory, EntranceExamCategory,
#     JobCategory, JobExamCategory, ExamLevel, Exam,Subject, Chapter, Question, QuestionOption, Solution, CorrectAnswer
# )
# class ExamSerializer(serializers.ModelSerializer):
#     question_count   = serializers.IntegerField(read_only=True)  # from annotate()
#     duration_minutes = serializers.SerializerMethodField()
#     difficulty       = serializers.SerializerMethodField()
#     language         = serializers.SerializerMethodField()
#     is_bookmarked    = serializers.SerializerMethodField()

#     class Meta:
#         model  = Exam
#         fields = [
#             'exam_id', 'exam_code','exam_name', 'exam_year', 'conducting_body',
#             'exam_category', 'question_count', 'duration_minutes',
#             'difficulty', 'language', 'is_bookmarked',
#         ]

#     def get_duration_minutes(self, obj):
#         return (obj.estimated_time_hours or 0) * 60

#     def get_difficulty(self, obj):
#         # Exam has no difficulty field itself — default until you decide
#         # how to derive it (e.g. majority of its Questions.difficulty_level).
#         return 'medium'

#     def get_language(self, obj):
#         return 'English'

#     def get_is_bookmarked(self, obj):
#         # No bookmark table yet — frontend currently toggles this locally
#         # only (see ExamView.vue onBookmark), so False is a safe default.
#         return False


# class SubjectSerializer(serializers.ModelSerializer):
#     id         = serializers.IntegerField(source='subject_id')
#     label      = serializers.CharField(source='subject_name')
#     test_count = serializers.IntegerField(source='chapter_count', read_only=True)

#     class Meta:
#         model  = Subject
#         fields = ['id', 'label', 'test_count']


# class ChapterSerializer(serializers.ModelSerializer):
#     id             = serializers.IntegerField(source='chapter_id')
#     label          = serializers.CharField(source='chapter_name')
#     question_count = serializers.IntegerField(read_only=True)

#     class Meta:
#         model  = Chapter
#         fields = ['id', 'label', 'question_count']


# class QuestionOptionSerializer(serializers.ModelSerializer):
#     option_A_images = serializers.SerializerMethodField()
#     option_B_images = serializers.SerializerMethodField()
#     option_C_images = serializers.SerializerMethodField()
#     option_D_images = serializers.SerializerMethodField()

#     class Meta:
#         model = QuestionOption
#         fields = ['option_id', 'option_A', 'option_B', 'option_C', 'option_D',
#                   'option_A_images', 'option_B_images', 'option_C_images', 'option_D_images']

#     def _abs(self, paths):
#         request = self.context.get('request')
#         if not paths:
#             return []
#         urls = paths.get('images', []) if isinstance(paths, dict) else []
#         return [request.build_absolute_uri(u) if request else u for u in urls]

#     def get_option_A_images(self, obj): return self._abs(obj.option_A_images)
#     def get_option_B_images(self, obj): return self._abs(obj.option_B_images)
#     def get_option_C_images(self, obj): return self._abs(obj.option_C_images)
#     def get_option_D_images(self, obj): return self._abs(obj.option_D_images)

# class SolutionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model  = Solution
#         fields = ['explaination_text', 'hints']


# class CorrectAnswerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model  = CorrectAnswer
#         fields = ['answer_value', 'answer_type']


# class QuestionSerializer(serializers.ModelSerializer):
#     options        = QuestionOptionSerializer(source='questionoption_set', many=True)
#     solution       = SolutionSerializer(source='solution_set', many=True)
#     correct_answer = CorrectAnswerSerializer(source='correctanswer_set', many=True)
#     subject_name   = serializers.CharField(source='subject.subject_name', read_only=True)
#     chapter_name   = serializers.CharField(source='chapter.chapter_name', read_only=True)
#     hint           = serializers.SerializerMethodField()

#     class Meta:
#         model  = Question
#         fields = [
#             'question_id', 'question_text', 'difficulty_level',
#             'language', 'question_type',
#             'subject_name', 'chapter_name',
#             'options', 'solution', 'correct_answer', 'hint',
#         ]

#     def get_hint(self, obj):
#         # Hints are safe to expose in BOTH modes — they nudge without
#         # revealing the answer or the full explanation.
#         sol = obj.solution_set.first()
#         return sol.hints if sol else ''

#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         mode = self.context.get('mode', 'practice')
#         if mode == 'test':
#             # Hide the correct answer & explanation until submitted.
#             # `hint` is intentionally left untouched — it's always available.
#             data['correct_answer'] = []
#             data['solution']       = []
#         return data

## ====================== SERIALIZER NEW CODE UPDATE ================================

from rest_framework import serializers

from .models import (
    State, Board, Stream, Field, SubField, EducationLevel,
    ExamType, SchoolExamCategory, EntranceExamCategory,
    JobCategory, JobExamCategory, ExamLevel, Exam,
    Subject, Chapter, Question, QuestionOption, CorrectAnswer, Solution,MockExam,TestDefinition,
)


# ─────────────────────────────────────────────
# FILTER DROPDOWN SERIALIZERS  ("Apply Filters" panel)
# ─────────────────────────────────────────────

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['state_id', 'state_name', 'state_code']


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['board_id', 'state', 'board_name', 'board_code']


class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ['stream_id', 'stream_name']


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ['field_id', 'stream', 'field_name']


class SubFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubField
        fields = ['sub_field_id', 'field', 'sub_field_name']


class FieldWithSubFieldsSerializer(serializers.ModelSerializer):
    sub_fields = SubFieldSerializer(many=True, source='subfield_set')
 
    class Meta:
        model = Field
        fields = ['field_id', 'field_name', 'sub_fields']


class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = ['education_level_id', 'education_level', 'description']


class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamType
        fields = ['exam_type_id', 'type_name', 'description']


class SchoolExamCategorySerializer(serializers.ModelSerializer):
    exam_type_name = serializers.CharField(source="exam_type.type_name", read_only=True)
    education_level_name = serializers.CharField(source="education_level.education_level", read_only=True)

    class Meta:
        model = SchoolExamCategory
        fields = [
            "category_id",
            "exam_type",
            "exam_type_name",
            "education_level",
            "education_level_name",
            "category_name",
            "description",
        ]

class EntranceExamCategorySerializer(serializers.ModelSerializer):
    education_level_name = serializers.CharField(
        source="education_level.education_level",
        read_only=True
    )

    class Meta:
        model = EntranceExamCategory
        fields = [
            "category_id",
            "exam_type",
            "education_level",
            "education_level_name",
            "category_name",
            "description",
        ]

class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['job_category_id', 'job_category_name', 'description']


class JobExamCategorySerializer(serializers.ModelSerializer):
    exam_type_name = serializers.CharField(
        source="exam_type.type_name",
        read_only=True
    )
    job_category_name = serializers.CharField(
        source="job_category.job_category_name",
        read_only=True
    )

    class Meta:
        model = JobExamCategory
        fields = [
            "category_id",
            "exam_type",
            "exam_type_name",
            "job_category",
            "job_category_name",
            "category_name",
            "description",
        ]


class ExamLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamLevel
        fields = ['level_id', 'level_name', 'description']


def resolve_category_name(exam):
    """
    exam.category_id is a plain integer pointing into whichever of the
    three category tables matches exam.exam_type.type_name:
        School   -> SchoolExamCategory
        Entrance -> EntranceExamCategory
        Job      -> JobExamCategory
    There is no real FK here, so it has to be resolved manually.
    """
    if not exam.category_id or not exam.exam_type_id:
        return None
    type_name = (exam.exam_type.type_name or '').strip().lower()
    model = {
        'school': SchoolExamCategory,
        'entrance': EntranceExamCategory,
        'job': JobExamCategory,
    }.get(type_name)
    if not model:
        return None
    try:
        return model.objects.get(pk=exam.category_id).category_name
    except model.DoesNotExist:
        return None


# ─────────────────────────────────────────────
# EXAM
# ─────────────────────────────────────────────

class ExamSerializer(serializers.ModelSerializer):
    """
    CHANGED FROM THE PREVIOUS VERSION:
    - `exam_category` (free text), `exam_year`, and `estimated_time_hours`
      do not exist on the current Exam model — they've been replaced by
      the real filter fields below (exam_type, category_id resolved via
      the three category tables, education_level, stream, field,
      sub_field, board, state, level).
    - `duration_minutes` now pulls from the exam's related TestDefinition
      (Mock preferred) instead of a nonexistent estimated_time_hours field,
      since duration actually lives per-test, not per-exam.
    """
    question_count = serializers.IntegerField(read_only=True, default=0)  # from annotate()

    exam_type_name = serializers.CharField(source='exam_type.type_name', read_only=True, default=None)
    category_name = serializers.SerializerMethodField()
    # CHANGED: education_level/stream are now M2M (see models.py) — a single
    # exam can carry several of each, so these are lists, not single values.
    education_levels = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    education_level_names = serializers.SerializerMethodField()
    streams = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    stream_names = serializers.SerializerMethodField()
    field_name = serializers.CharField(source='field.field_name', read_only=True, default=None)
    sub_field_name = serializers.CharField(source='sub_field.sub_field_name', read_only=True, default=None)
    board_name = serializers.CharField(source='board.board_name', read_only=True, default=None)
    state_name = serializers.CharField(source='state.state_name', read_only=True, default=None)
    level_name = serializers.CharField(source='level.level_name', read_only=True, default=None)

    duration_minutes = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            'exam_id', 'exam_code', 'exam_name', 'conducting_body','logo',
            'exam_type', 'exam_type_name',
            'category_id', 'category_name',
            'education_levels', 'education_level_names',
            'streams', 'stream_names',
            'field', 'field_name',
            'sub_field', 'sub_field_name',
            'board', 'board_name',
            'state', 'state_name',
            'level', 'level_name',
            'question_count', 'duration_minutes',
            'difficulty', 'language', 'is_bookmarked',
            'is_active',
        ]

    def get_category_name(self, obj):
        return resolve_category_name(obj)

    def get_education_level_names(self, obj):
        return [el.education_level for el in obj.education_levels.all()]

    def get_stream_names(self, obj):
        return [s.stream_name for s in obj.streams.all()]

    def get_duration_minutes(self, obj):
        test = obj.testdefinition_set.filter(test_type='Mock').first() \
            or obj.testdefinition_set.first()
        return test.duration_minutes if test else None

    def get_difficulty(self, obj):
        # Exam has no difficulty field itself — default until you decide
        # how to derive it (e.g. majority of its Questions.difficulty_level).
        return 'medium'

    def get_language(self, obj):
        return 'English'

    def get_is_bookmarked(self, obj):
        # No bookmark table yet — frontend currently toggles this locally
        # only, so False is a safe default.
        return False


class SubjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='subject_id')
    label = serializers.CharField(source='subject_name')
    test_count = serializers.IntegerField(source='chapter_count', read_only=True, default=0)

    class Meta:
        model = Subject
        fields = ['id', 'label', 'test_count']


class ChapterSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='chapter_id')
    label = serializers.CharField(source='chapter_name')
    question_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Chapter
        fields = ['id', 'label', 'question_count']


class QuestionOptionSerializer(serializers.ModelSerializer):
    """
    UPDATED: QuestionOption now has an `option_images` JSONField —
    {"A": "<url>", "B": "<url>", ...}, only for letters that are actually
    graph-style options (plain-text options simply don't appear in the
    dict). Added to `fields` below so it's no longer silently stripped
    from the API response — it existed in the DB but was never being
    sent to the frontend.

    NEW: option_{a..d}_latex columns (see Import_Mock.py's to_latex() /
    Mathpix OCR fallback) were being written to the DB but never
    serialized, so the frontend had no way to ever receive them — every
    option fell back to raw plain text (including the badly-scrambled
    ones the OCR fallback exists specifically to fix). Adding them here
    is what actually turns that pipeline on end-to-end.

    These columns may not exist on every deployment yet (they're an
    opt-in migration per Import_Mock.py's own docstring), so each is
    declared with a SerializerMethodField that degrades to '' via
    getattr(..., default='') instead of a plain ModelSerializer field —
    a bare model field reference would raise ImproperlyConfigured at
    import time on any DB that hasn't run that migration.
    """
    option_a_latex = serializers.SerializerMethodField()
    option_b_latex = serializers.SerializerMethodField()
    option_c_latex = serializers.SerializerMethodField()
    option_d_latex = serializers.SerializerMethodField()

    class Meta:
        model = QuestionOption
        fields = [
            'option_id', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'option_images',
            'option_a_latex', 'option_b_latex', 'option_c_latex', 'option_d_latex',
        ]

    def _latex(self, obj, letter):
        return getattr(obj, f'option_{letter}_latex', '') or ''

    def get_option_a_latex(self, obj): return self._latex(obj, 'a')
    def get_option_b_latex(self, obj): return self._latex(obj, 'b')
    def get_option_c_latex(self, obj): return self._latex(obj, 'c')
    def get_option_d_latex(self, obj): return self._latex(obj, 'd')


class SolutionSerializer(serializers.ModelSerializer):
    """
    NEW: explaination_text_latex (see Import_Mock.py — written only when
    the column exists on the model) is exposed the same defensive way as
    the option latex fields above, so it degrades to '' rather than
    breaking on a DB that hasn't added the column yet.
    """
    explaination_text_latex = serializers.SerializerMethodField()

    class Meta:
        model = Solution
        fields = ['solution_id', 'explaination_text', 'explaination_text_latex', 'hints', 'image_url']

    def get_explaination_text_latex(self, obj):
        return getattr(obj, 'explaination_text_latex', '') or ''


class CorrectAnswerSerializer(serializers.ModelSerializer):
    """
    CHANGED: previous version referenced answer_value/answer_type, which
    don't exist. The real model stores the correct option as a string in
    `option_id` (e.g. 'A', 'B', or 'A,C' for MSQ).
    """
    class Meta:
        model = CorrectAnswer
        fields = ['correct_answer_id', 'option_id']


class QuestionSerializer(serializers.ModelSerializer):
    """
    CHANGED: Question has no direct `subject` FK — it only has `chapter`,
    and chapter -> subject. `subject_name` is resolved through that path.
    `language` isn't a real column, so it stays a static default like
    on ExamSerializer. `hint` is a genuine field directly on Question,
    so it's now included as-is instead of being derived from Solution.
    """
    options = QuestionOptionSerializer(source='questionoption_set', many=True, read_only=True)
    solution = SolutionSerializer(source='solution_set', many=True, read_only=True)
    correct_answer = CorrectAnswerSerializer(source='correctanswer_set', many=True, read_only=True)

    subject_name = serializers.CharField(source='chapter.subject.subject_name', read_only=True, default=None)
    chapter_name = serializers.CharField(source='chapter.chapter_name', read_only=True, default=None)
    language = serializers.SerializerMethodField()
    # NEW: question_text_latex (see Import_Mock.py's to_latex() pass over
    # the stem) — same defensive getattr pattern as the option/solution
    # latex fields, since this column is an opt-in migration.
    question_text_latex = serializers.SerializerMethodField()
    # PYQ (Previous Year Question) source metadata.
    is_pyq = serializers.BooleanField(source='is_previousyear', read_only=True)
    pyq_exam_name = serializers.CharField(source='pyq_exam.exam_name', read_only=True, default=None)

    class Meta:
        model = Question
        fields = [
            'question_id', 'question_text', 'difficulty_level',
            'language', 'question_type',
            'subject_name', 'chapter_name',
            'options', 'solution', 'correct_answer', 'hint',
            # NEW: {"images": ["<url>", ...]} — was missing from `fields`
            # entirely, so it existed on the model/DB but never reached
            # the API response.
            'image_url',
            'question_text_latex',
            'is_pyq', 'pyq_exam', 'pyq_exam_name', 'pyq_year', 'pyq_session',
        ]

    def get_language(self, obj):
        return 'English'

    def get_question_text_latex(self, obj):
        return getattr(obj, 'question_text_latex', '') or ''

    def to_representation(self, instance):
        data = super().to_representation(instance)
        mode = self.context.get('mode', 'practice')
        if mode == 'test':
            # Hide the correct answer & explanation until submitted.
            # `hint` is intentionally left untouched — it's always available.
            data['correct_answer'] = []
            data['solution'] = []
        return data


class MockExamSerializer(serializers.ModelSerializer):
    """
    Serializes MockExam rows for the Select Mock Test screen.
 
    NOTE: `question_count` is annotated on the queryset in
    MockExamListView (Count over Question.mock_exam, is_active=True
    only) and surfaced here as a plain read-only IntegerField.
    `difficulty` / `language` still don't exist on MockExam -- the
    frontend defaults those to "Medium" / "English".
    """
    exam_id = serializers.IntegerField(source='exam.exam_id', read_only=True)
    exam_code = serializers.CharField(source='exam.exam_code', read_only=True)
    question_count = serializers.IntegerField(read_only=True, default=0)

    # NEW — populates the "Exam Type" column on the admin table.
    # Assumes Exam has a FK `exam_type` -> ExamType with `type_name`.
    exam_type_name = serializers.CharField(source='exam.exam_type.type_name', read_only=True, default=None)
 
    # NEW — populates the "Category" column.
    # CHANGED: Exam has no real `category` relation to source from —
    # `Exam.category_id` is a plain IntegerField, a manual polymorphic
    # pointer into one of SchoolExamCategory / EntranceExamCategory /
    # JobExamCategory depending on exam_type (see ExamCategoryListView's
    # dispatch logic, which this mirrors). The previous
    # `source='exam.category.category_name'` CharField always silently
    # returned its `default=None` — 'category' doesn't exist as an
    # attribute on Exam, and worse, the equivalent select_related() path
    # used to eagerly load it in MockExamDetailView raised a hard
    # FieldError (that was the actual cause of the 500 on
    # GET /mockexams/<id>/, now fixed in _annotated_mockexam()).
    category_name = serializers.SerializerMethodField()

    def get_category_name(self, obj):
        exam = getattr(obj, 'exam', None)
        if not exam or not exam.category_id:
            return None
        exam_type = getattr(exam, 'exam_type', None)
        type_name = (exam_type.type_name or '').strip().lower() if exam_type else ''

        category_model = {
            'school': SchoolExamCategory,
            'entrance': EntranceExamCategory,
            'job': JobExamCategory,
        }.get(type_name)
        if category_model is None:
            return None

        try:
            return category_model.objects.get(pk=exam.category_id).category_name
        except category_model.DoesNotExist:
            return None
 
    # NEW — populates the "Subjects" column. This assumes the pattern
    # (totalQuestions/marksPerQuestion/subjects/...) captured in
    # SetPatternStep is persisted on MockExam as a JSONField called
    # `pattern`, matching what MockExamCreateUpdateSerializer accepts on
    # POST. If it's stored as a related model instead (e.g.
    # MockExamSubjectPattern rows via a FK), swap this for:
    #   subjects_count = serializers.IntegerField(
    #       source='subject_patterns.count', read_only=True
    #   )
    subjects_count = serializers.SerializerMethodField()

    def get_subjects_count(self, obj):
        pattern = getattr(obj, 'pattern', None) or {}
        subjects = pattern.get('subjects') if isinstance(pattern, dict) else None
        return len(subjects) if subjects else 0

    class Meta:
        model = MockExam
        fields = (
            'mockexam_id', 'exam_id', 'exam_code', 'mockexam_name', 'year',
            'description', 'total_marks', 'duration_minutes', 'question_count',
            'is_active', 'created_at', 'updated_at','exam_type_name','category_name',
            'subjects_count',
        )

class MockExamCreateUpdateSerializer(serializers.ModelSerializer):
    """
    NEW: backs POST /api/mockexams/ (create) and PUT/PATCH
    /api/mockexams/<id>/ (edit), used by the Create Mock Test wizard
    (BasicDetailsStep + SelectExamStep + SetPatternStep -> Review &
    Confirm's "Confirm & Create" button).

    `exam` is write-only here (input is the parent Exam's PK, chosen in
    SelectExamStep) — the read side of a mock exam already goes through
    MockExamSerializer above, which exposes exam_id/exam_code instead.

    `pattern` is accepted and stored as-is (see the JSONField comment
    on the model) — this is intentionally schema-flexible so the
    frontend's exact subject-row shape doesn't need a matching
    serializer field for every key.
    """
    class Meta:
        model = MockExam
        fields = (
            'mockexam_id', 'exam', 'mockexam_name', 'year', 'description',
            'total_marks', 'duration_minutes', 'pattern', 'is_active',
        )
        extra_kwargs = {
            'exam': {'write_only': True},
        }

    def validate_mockexam_name(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Mock test name is required.')
        return value

# ─────────────────────────────────────────────
# DASHBOARD — Recent Test Activity ("adminDummyData.recentTestActivity")
# ─────────────────────────────────────────────
 
class TestDefinitionSerializer(serializers.ModelSerializer):
    """
    NEW: shapes a TestDefinition row to exactly match the frontend's
    dummy `recentTestActivity` objects: { name, exam, type, questions,
    duration, status, updatedOn }. `questions` is annotated on the
    queryset (Count of related questions) in the dashboard view rather
    than computed here, since TestDefinition has no direct question
    count field.
    """
    name = serializers.CharField(source='test_name', read_only=True)
    exam = serializers.CharField(source='exam.exam_name', read_only=True)
    type = serializers.CharField(source='test_type', read_only=True)
    questions = serializers.IntegerField(read_only=True, default=0)
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    updatedOn = serializers.SerializerMethodField()
 
    class Meta:
        model = TestDefinition
        fields = ['name', 'exam', 'type', 'questions', 'duration', 'status', 'updatedOn']
 
    def get_duration(self, obj):
        return f"{obj.duration_minutes} Min" if obj.duration_minutes else ''
 
    def get_status(self, obj):
        return 'Published' if obj.is_active else 'Draft'

    def get_updatedOn(self, obj):
        return obj.created_at.strftime('%d %b %Y') if obj.created_at else ''


