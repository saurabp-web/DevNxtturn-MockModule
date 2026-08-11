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
    Subject, Chapter, Question, QuestionOption, CorrectAnswer, Solution,MockExam
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
    CHANGED: the real QuestionOption model stores plain text options
    (option_a..option_e, lowercase) with no per-option image storage —
    the option_X_images fields from the previous version don't map to
    anything in this schema and have been dropped. Question.image_url
    covers one image for the whole question, not per-option.
    """
    class Meta:
        model = QuestionOption
        fields = ['option_id', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e']


class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        fields = ['solution_id', 'explaination_text', 'hints']


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

    class Meta:
        model = Question
        fields = [
            'question_id', 'question_text', 'difficulty_level',
            'language', 'question_type',
            'subject_name', 'chapter_name',
            'options', 'solution', 'correct_answer', 'hint',
        ]

    def get_language(self, obj):
        return 'English'

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
 
    NOTE: MockExam currently has no `difficulty`, `language`, or
    `question_count` fields in the schema (only exam_name, year,
    description, total_marks, duration_minutes). The frontend defaults
    these to "Medium" / "English" / 0 respectively, matching what the
    UI already showed before. If you want real per-test difficulty and
    a real question count, either:
      (a) add `difficulty` / `language` CharFields to MockExam, and a
          `mockexam` FK on Question so a per-test question_count can be
          annotated here the same way ExamListView annotates it, or
      (b) derive marks/questions from TestDefinition rows of
          test_type='Mock' linked via the same mockexam_id, if that's
          where your question sets actually live.
    """
    exam_id = serializers.IntegerField(source='exam.exam_id', read_only=True)
    exam_code = serializers.CharField(source='exam.exam_code', read_only=True)
 
    class Meta:
        model = MockExam
        fields = (
            'mockexam_id', 'exam_id', 'exam_code', 'mockexam_name', 'year',
            'description', 'total_marks', 'duration_minutes',
            'is_active', 'created_at', 'updated_at',
        )