from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny,IsAdminUser
from django.db.models import Count, Q,ProtectedError
from django.core.paginator import Paginator
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging
import io
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from collections import Counter

import uuid
import re
import json
from pathlib import Path
from django.core.cache import cache
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import Exam, Subject,Chapter, Question, QuestionOption,CorrectAnswer, MockExam,QuestionChapterMapping

logger = logging.getLogger(__name__)

from .models import (
    State, Board, Stream, Field, SubField, EducationLevel,
    ExamType, SchoolExamCategory, EntranceExamCategory,
    JobCategory, JobExamCategory, ExamLevel, Exam,
    Subject, Chapter, Question,MockExam,QuestionOption,
    TestDefinition,Solution,CorrectAnswer, QuestionChapterMapping
)
from .serializers import (
    StateSerializer, BoardSerializer, StreamSerializer, FieldSerializer,
    SubFieldSerializer,FieldWithSubFieldsSerializer, EducationLevelSerializer, ExamTypeSerializer,
    SchoolExamCategorySerializer, EntranceExamCategorySerializer,MockExamCreateUpdateSerializer,
    JobCategorySerializer, JobExamCategorySerializer, ExamLevelSerializer,QuestionOptionSerializer,
    ExamSerializer, SubjectSerializer, ChapterSerializer, QuestionSerializer,MockExamSerializer,
    TestDefinitionSerializer
)

# ─────────────────────────────────────────────────────────────
# APPLY FILTERS — cascading dropdown data (Process Flow steps 1-9)
# ─────────────────────────────────────────────────────────────

class ExamTypeListView(generics.ListAPIView):
    """GET /api/filters/exam-types/"""
    queryset = ExamType.objects.all()
    serializer_class = ExamTypeSerializer
    # CHANGED: was missing this — every other filter-dropdown endpoint
    # (ExamLevelListView, etc.) explicitly disables pagination since
    # they feed <select> dropdowns that expect a plain array. Without
    # it, DRF's global pagination wraps the response as
    # {count, next, previous, results: [...]}, which breaks
    # filtersApi.ts's `data.map(...)` call — and since
    # StepClassification.vue fetches exam-types and exam-levels via
    # Promise.all, that one failure silently emptied BOTH dropdowns.
    pagination_class = None


class OptionListView(generics.ListAPIView):
    queryset = QuestionOption.objects.all()
    serializer_class = QuestionOptionSerializer
    pagination_class = None  # Return all options without pagination



class ExamCategoryListView(APIView):
    """
    GET /api/filters/exam-categories/?exam_type_id=&education_level_id=
    GET /api/filters/exam-categories/?exam_type_id=&job_category_id=
    """

    def get(self, request):
        exam_type_id = request.query_params.get("exam_type_id")
        education_level_id = request.query_params.get("education_level_id")
        job_category_id = request.query_params.get("job_category_id")

        if not exam_type_id:
            return Response(
                {"error": "exam_type_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exam_type = ExamType.objects.get(pk=exam_type_id)
        except ExamType.DoesNotExist:
            return Response(
                {"error": "Invalid exam_type_id"},
                status=status.HTTP_404_NOT_FOUND
            )

        type_name = exam_type.type_name.strip().lower()

        if type_name == "school":
            qs = SchoolExamCategory.objects.select_related(
                "education_level",
                "exam_type"
            ).filter(exam_type=exam_type)

            if education_level_id:
                qs = qs.filter(education_level_id=education_level_id)

            data = SchoolExamCategorySerializer(qs, many=True).data

        elif type_name == "entrance":
            qs = EntranceExamCategory.objects.select_related(
                "education_level",
                "exam_type"
            ).filter(exam_type=exam_type)

            if education_level_id:
                qs = qs.filter(education_level_id=education_level_id)

            data = EntranceExamCategorySerializer(qs, many=True).data

        elif type_name == "job":
            qs = JobExamCategory.objects.select_related(
                "exam_type",
                "job_category"
            ).filter(exam_type=exam_type)

            if job_category_id:
                qs = qs.filter(job_category_id=job_category_id)

            data = JobExamCategorySerializer(qs, many=True).data

        else:
            return Response(
                {"error": f"Unknown exam type '{exam_type.type_name}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(data, status=status.HTTP_200_OK)


class EducationLevelListView(generics.ListAPIView):
    """
    GET /api/filters/education-levels/
    GET /api/filters/education-levels/?exam_type_id=  → only levels valid
        for that exam type, per the curated ExamType.education_levels M2M
        (seeded via data migration) — not derived from existing Exam rows,
        since that broke for exam types with no exams created yet.
    """
    serializer_class = EducationLevelSerializer
    pagination_class = None  # Return all education levels without pagination

    def get_queryset(self):
        qs = EducationLevel.objects.all()
        exam_type_id = self.request.query_params.get('exam_type_id')
        if exam_type_id:
            qs = qs.filter(exam_types__exam_type_id=exam_type_id)
        return qs


class StreamListView(generics.ListAPIView):
    """
    GET /api/filters/streams/
    GET /api/filters/streams/?exam_type_id=  → only streams actually used
        by at least one Exam of that type
    GET /api/filters/streams/?education_level_id=  → only streams actually
        used by at least one Exam with that education level
    Both params can be combined (AND).
    """
    serializer_class = StreamSerializer
    pagination_class = None  # Return all streams without pagination

    def get_queryset(self):
        qs = Stream.objects.all()
        exam_type_id = self.request.query_params.get('exam_type_id')
        education_level_id = self.request.query_params.get('education_level_id')
        # CHANGED: there's no direct Stream -> EducationLevel relationship
        # in the schema (Stream has no education_level FK). The only link
        # is through Exam, which has both as M2M fields — same approach
        # already used for the exam_type_id filter below.
        if exam_type_id or education_level_id:
            exam_filter = {'streams__isnull': False}
            if exam_type_id:
                exam_filter['exam_type_id'] = exam_type_id
            if education_level_id:
                exam_filter['education_levels__education_level_id'] = education_level_id
            used_ids = (
                Exam.objects
                .filter(**exam_filter)
                .values_list('streams__stream_id', flat=True)
                .distinct()
            )
            qs = qs.filter(pk__in=used_ids)
        return qs


class FieldListView(generics.ListAPIView):
    """GET /api/filters/fields/?stream_id="""
    serializer_class = FieldSerializer
    pagination_class = None  # Return all fields without pagination

    def get_queryset(self):
        qs = Field.objects.all()
        stream_id = self.request.query_params.get('stream_id')
        if stream_id:
            qs = qs.filter(stream_id=stream_id)
        return qs


class SubFieldListView(generics.GenericAPIView):
    """
    GET /api/filters/sub-fields/              → all fields with their subfields
    GET /api/filters/sub-fields/?field_id=23  → only that field's subfields
    GET /api/filters/sub-fields/?field_id=23,24  → comma-separated
    """
    pagination_class = None
    queryset = Field.objects.none()

    def get(self, request, *args, **kwargs):
        field_id_param = request.query_params.get('field_id', '').strip()

        if field_id_param:
            # Filter by specific field_id(s)
            field_ids = [fid.strip() for fid in field_id_param.split(',') if fid.strip()]
            fields = (
                Field.objects
                .filter(field_id__in=field_ids)
                .prefetch_related('subfield_set')
                .order_by('field_name')
            )
        else:
            # No field_id passed — return everything
            fields = (
                Field.objects
                .all()
                .prefetch_related('subfield_set')
                .order_by('field_name')
            )

        serializer = FieldWithSubFieldsSerializer(fields, many=True)
        return Response(serializer.data)


class BoardListView(generics.ListAPIView):
    """GET /api/filters/boards/?state_id=&exam_type_id="""
    serializer_class = BoardSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Board.objects.all()
        state_id = self.request.query_params.get('state_id')
        if state_id:
            qs = qs.filter(state_id=state_id)
        exam_type_id = self.request.query_params.get('exam_type_id')
        if exam_type_id:
            used_ids = (
                Exam.objects
                .filter(exam_type_id=exam_type_id, board_id__isnull=False)
                .values_list('board_id', flat=True)
                .distinct()
            )
            qs = qs.filter(pk__in=used_ids)
        return qs


class StateListView(generics.ListAPIView):
    """
    GET /api/filters/states/
    GET /api/filters/states/?exam_type_id=  → only states actually used
        by at least one Exam of that type
    """
    serializer_class = StateSerializer
    pagination_class = None

    def get_queryset(self):
        qs = State.objects.all()
        exam_type_id = self.request.query_params.get('exam_type_id')
        if exam_type_id:
            used_ids = (
                Exam.objects
                .filter(exam_type_id=exam_type_id, state_id__isnull=False)
                .values_list('state_id', flat=True)
                .distinct()
            )
            qs = qs.filter(pk__in=used_ids)
        return qs


class ExamLevelListView(generics.ListAPIView):
    """
    GET /api/filters/exam-levels/
    GET /api/filters/exam-levels/?exam_type_id=  → only levels actually used
        by at least one Exam of that type
    """
    serializer_class = ExamLevelSerializer
    pagination_class = None

    def get_queryset(self):
        qs = ExamLevel.objects.all()
        exam_type_id = self.request.query_params.get('exam_type_id')
        if exam_type_id:
            used_ids = (
                Exam.objects
                .filter(exam_type_id=exam_type_id, level_id__isnull=False)
                .values_list('level_id', flat=True)
                .distinct()
            )
            qs = qs.filter(pk__in=used_ids)
        return qs


class JobCategoryListView(generics.ListAPIView):
    """GET /api/filters/job-categories/"""
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    pagination_class = None  # Return all job categories without pagination


# class FilterOptionsView(APIView):
#     """
#     GET /api/filters/options/
#     Every non-dependent dropdown in one call. Dependent ones (categories,
#     fields, sub-fields, boards) still need their own endpoint once the
#     parent is picked.
#     """
#     def get(self, request):
#         return Response({
#             'exam_types': ExamTypeSerializer(ExamType.objects.all(), many=True).data,
#             'education_levels': EducationLevelSerializer(EducationLevel.objects.all(), many=True).data,
#             'streams': StreamSerializer(Stream.objects.all(), many=True).data,
#             'states': StateSerializer(State.objects.all(), many=True).data,
#             'exam_levels': ExamLevelSerializer(ExamLevel.objects.all(), many=True).data,
#             'job_categories': JobCategorySerializer(JobCategory.objects.all(), many=True).data,
#         })

class ExamFilterView(APIView):
    """
    GET /api/exams/filter/
 
    Universal exam filter endpoint. All params are optional and combinable.
    Covers every scenario across School, Entrance and Job exam types.
 
    ┌─────────────────────────────────────────────────────────────────────┐
    │  PARAM             TYPE      DESCRIPTION                           │
    ├─────────────────────────────────────────────────────────────────────┤
    │  exam_type_id      int       ExamType PK  (1=School,2=Entrance,    │
    │                              3=Job — depends on your seed data)    │
    │  category_id       int       JobExamCategory / SchoolExamCategory  │
    │                              / EntranceExamCategory PK             │
    │  job_category_id   int       JobCategory PK  (Job type only)       │
    │  education_level_id int      EducationLevel PK (School/Entrance)   │
    │  stream_id         int       Stream PK  (Entrance / School)        │
    │  field_id          int       Field PK                              │
    │  sub_field_id      int       SubField PK                           │
    │  board_id          int       Board PK  (School type)               │
    │  state_id          int       State PK                              │
    │  level_id          int       ExamLevel PK (Central/State/Univ)     │
    │  search            str       icontains on name/code/body           │
    │  page              int       page number (default 1)               │
    │  page_size         int       results per page (default 10, max 50) │
    └─────────────────────────────────────────────────────────────────────┘
 
    SCENARIOS COVERED
    ─────────────────
    1.  No params            → all active exams (paginated)
    2.  exam_type_id only    → all exams of that type
    3.  School + education_level_id          → board exams by level
    4.  School + education_level_id + board_id → board-specific
    5.  School + education_level_id + state_id → state board exams
    6.  School + category_id                  → specific school category
    7.  Entrance + education_level_id         → entrance by level
    8.  Entrance + stream_id                  → stream-specific entrance
    9.  Entrance + field_id                   → field-specific entrance
    10. Entrance + sub_field_id               → sub-field specific
    11. Entrance + stream_id + field_id       → narrowed entrance
    12. Entrance + category_id                → specific entrance category
    13. Job only                              → all job exams
    14. Job + job_category_id                 → exams under that job category
    15. Job + category_id                     → specific exam category
    16. Job + job_category_id + category_id   → exact job exam
    17. Job + level_id                        → central/state/univ level
    18. Job + state_id                        → state-specific job exams
    19. Any type + search                     → text search within type
    20. Any type + level_id                   → filter by exam level
    21. Cross-type search (no exam_type_id)   → search across all types
    22. Pagination (page + page_size)         → any of the above, paged
    23. Invalid integer params                → 400 with clear message
    24. Non-existent FK values                → empty results (not error)
    25. page_size capped at 50               → safe response size
    """
 
    PAGE_SIZE_DEFAULT = 10
    PAGE_SIZE_MAX = 50
 
    # Simple integer FK filters: query_param → ORM field
    # CHANGED: education_level_id / stream_id now traverse the M2M
    # (education_levels / streams) instead of a single FK column — see
    # models.py. This is the actual fix for exams "disappearing" when
    # filtered: previously only the exam's FIRST tag was stored, so
    # filtering by any other valid tag matched nothing.
    INT_FILTER_MAP = {
        'exam_type_id':        'exam_type_id',
        'category_id':         'category_id',
        'education_level_id':  'education_levels__education_level_id',
        'stream_id':           'streams__stream_id',
        'field_id':            'field_id',
        'sub_field_id':        'sub_field_id',
        'board_id':            'board_id',
        'state_id':            'state_id',
        'level_id':            'level_id',
    }
 
    def _parse_int(self, value, param_name):
        """
        Returns (int_value, None) on success.
        Returns (None, Response) on failure — caller must return the Response.
        """
        if not value.isdigit() or int(value) <= 0:
            return None, Response(
                {'error': f'"{param_name}" must be a positive integer, got "{value}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return int(value), None
 
    def _validate_job_category_filter(self, job_category_id, exam_type_id):
        """
        job_category_id is only meaningful when exam_type is Job.
        Returns a warning string if misused, None otherwise.
        """
        if not job_category_id or not exam_type_id:
            return None
        try:
            et = ExamType.objects.get(pk=exam_type_id)
            if et.type_name.strip().lower() != 'job':
                return (
                    f'job_category_id is ignored because exam_type '
                    f'"{et.type_name}" is not "Job".'
                )
        except ExamType.DoesNotExist:
            pass
        return None
 
    def get(self, request):
        params = request.query_params
        errors = []
        int_values = {}
 
        # ── 1. Parse and validate all integer params ──────────────────────
        for param in list(self.INT_FILTER_MAP.keys()) + ['page', 'page_size']:
            raw = params.get(param, '').strip()
            if raw:
                val, err_response = self._parse_int(raw, param)
                if err_response:
                    errors.append(f'{param}: must be a positive integer, got "{raw}"')
                else:
                    int_values[param] = val
 
        # ── Special: job_category_id (separate from INT_FILTER_MAP) ───────
        raw_jc = params.get('job_category_id', '').strip()
        job_category_id = None
        if raw_jc:
            val, err_response = self._parse_int(raw_jc, 'job_category_id')
            if err_response:
                errors.append(f'job_category_id: must be a positive integer, got "{raw_jc}"')
            else:
                job_category_id = val
 
        if errors:
            return Response(
                {'error': 'Invalid parameter(s).', 'details': errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # ── 2. Warn if job_category_id is used with a non-Job exam type ───
        warnings = []
        warn = self._validate_job_category_filter(
            job_category_id, int_values.get('exam_type_id')
        )
        if warn:
            warnings.append(warn)
            job_category_id = None  # ignore it to avoid wrong results
 
        # ── 3. Base queryset ───────────────────────────────────────────────
        qs = (
            Exam.objects
            .filter(is_active=True)
            .select_related(
                'exam_type', 'field', 'sub_field', 'board', 'state', 'level',
            )
            .prefetch_related('education_levels', 'streams')
            # distinct=True guards against join fan-out introduced by the
            # M2M filters below (without it, question_count gets multiplied
            # once per matching education_level/stream row).
            .annotate(question_count=Count('question', distinct=True))
            .order_by('-is_trending', '-trending_score', '-question_count', 'exam_name')
        )
 
        # ── 4. Apply all standard integer FK filters ───────────────────────
        for param, orm_field in self.INT_FILTER_MAP.items():
            if param in int_values:
                qs = qs.filter(**{orm_field: int_values[param]})

        # M2M joins (education_levels__, streams__) can duplicate a row in
        # the result set; collapse duplicates back to one row per exam.
        if 'education_level_id' in int_values or 'stream_id' in int_values:
            qs = qs.distinct()
 
        # ── 5. Job-category sub-filter (category_id inside job scope) ─────
        #   When exam_type is Job and job_category_id is given, we resolve
        #   which category_ids belong to that job_category and filter exams.
        if job_category_id:
            exam_type_id = int_values.get('exam_type_id')
            if exam_type_id:
                # We know it's Job type (validated above), so resolve
                # the JobExamCategory PKs for that job_category and use
                # them to narrow the generic category_id column on Exam.
                job_exam_cat_ids = list(
                    JobExamCategory.objects
                    .filter(job_category_id=job_category_id, exam_type_id=exam_type_id)
                    .values_list('category_id', flat=True)
                )
                if job_exam_cat_ids:
                    qs = qs.filter(category_id__in=job_exam_cat_ids)
                else:
                    # No exam categories exist for this job_category — return empty
                    qs = qs.none()
            else:
                # No exam_type_id given but job_category_id given:
                # still try to narrow — find all Job-type exam_type ids first
                job_exam_cat_ids = list(
                    JobExamCategory.objects
                    .filter(job_category_id=job_category_id)
                    .values_list('category_id', flat=True)
                )
                job_exam_type_ids = list(
                    ExamType.objects
                    .filter(type_name__iexact='Job')
                    .values_list('exam_type_id', flat=True)
                )
                if job_exam_cat_ids and job_exam_type_ids:
                    qs = qs.filter(
                        exam_type_id__in=job_exam_type_ids,
                        category_id__in=job_exam_cat_ids,
                    )
                else:
                    qs = qs.none()
 
        # ── 6. Text search ─────────────────────────────────────────────────
        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(exam_name__icontains=search) |
                Q(exam_code__icontains=search) |
                Q(conducting_body__icontains=search) |
                Q(description__icontains=search)
            )
 
        # ── 7. Validate related objects exist (helpful 404s) ───────────────
        #   Only check if a filter was actually applied and returned nothing
        #   due to a genuinely missing object, to give a better error message.
        existence_checks = {
            'exam_type_id':       (ExamType,        'ExamType'),
            'education_level_id': (EducationLevel,  'EducationLevel'),
            'stream_id':          (Stream,           'Stream'),
            'field_id':           (Field,            'Field'),
            'sub_field_id':       (SubField,         'SubField'),
            'board_id':           (Board,            'Board'),
            'state_id':           (State,            'State'),
            'level_id':           (ExamLevel,        'ExamLevel'),
        }
        not_found = []
        for param, (model, label) in existence_checks.items():
            if param in int_values:
                if not model.objects.filter(pk=int_values[param]).exists():
                    not_found.append(f'{label} with id={int_values[param]} does not exist.')
 
        if job_category_id:
            if not JobCategory.objects.filter(pk=job_category_id).exists():
                not_found.append(f'JobCategory with id={job_category_id} does not exist.')
 
        if not_found:
            return Response(
                {'error': 'One or more filter values were not found.', 'details': not_found},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        # ── 8. Pagination ──────────────────────────────────────────────────
        page_number = int_values.get('page', 1)
        page_size = min(
            int_values.get('page_size', self.PAGE_SIZE_DEFAULT),
            self.PAGE_SIZE_MAX,
        )
 
        total_count = qs.count()
        paginator = Paginator(qs, page_size)
 
        # Clamp page number to valid range
        if page_number > paginator.num_pages and paginator.num_pages > 0:
            page_number = paginator.num_pages
 
        page_obj = paginator.get_page(page_number)
        serializer = ExamSerializer(page_obj.object_list, many=True)
 
        # ── 9. Build response ──────────────────────────────────────────────
        response_data = {
            'meta': {
                'total_count':  total_count,
                'page':         page_number,
                'page_size':    page_size,
                'total_pages':  paginator.num_pages,
                'has_next':     page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'filters_applied': {
                k: v for k, v in {
                    **{p: int_values[p] for p in self.INT_FILTER_MAP if p in int_values},
                    'job_category_id': job_category_id,
                    'search': search or None,
                }.items() if v is not None
            },
            'results': serializer.data,
        }
 
        if warnings:
            response_data['warnings'] = warnings
 
        return Response(response_data, status=status.HTTP_200_OK)

# ─────────────────────────────────────────────────────────────
# EXAMS  (Process Flow steps 10-11)
# ─────────────────────────────────────────────────────────────

class ExamListView(APIView):
    """
    GET /api/exams/
    Params (all optional, combine with AND):
        page            – page number, default 1
        exam_id         – exact PK
        exam_type       – ExamType PK
        category_id     – category PK from whichever table matches exam_type
        education_level – EducationLevel PK
        stream          – Stream PK
        field           – Field PK
        sub_field       – SubField PK
        board           – Board PK
        state           – State PK
        level           – ExamLevel PK
        search          – text match on exam_name / exam_code / conducting_body

    CHANGED: `exam_category` (free text) and `exam_year` are gone —
    Exam has no such columns anymore. Use `exam_type` + `category_id`
    (+ `education_level`) instead, which map onto the real
    School/Entrance/Job category tables from the ERD.
    """
    PAGE_SIZE = 517

    FILTER_MAP = {
        'exam_type': 'exam_type_id',
        'category_id': 'category_id',
        # CHANGED: education_level/stream are now M2M — see models.py.
        'education_level': 'education_levels__education_level_id',
        'stream': 'streams__stream_id',
        'field': 'field_id',
        'sub_field': 'sub_field_id',
        'board': 'board_id',
        'state': 'state_id',
        'level': 'level_id',
    }

    def get(self, request):
        qs = Exam.objects.filter(is_active=True) \
            .select_related('exam_type', 'field', 'sub_field', 'board', 'state', 'level') \
            .prefetch_related('education_levels', 'streams') \
            .annotate(question_count=Count('question', distinct=True)) \
            .order_by('exam_name')

        exam_id = request.query_params.get('exam_id', '').strip()
        if exam_id:
            if not exam_id.isdigit():
                return Response(
                    {'error': f'exam_id must be a valid integer, got "{exam_id}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(exam_id=int(exam_id))

        for param, field_lookup in self.FILTER_MAP.items():
            value = request.query_params.get(param, '').strip()
            if value:
                if not value.isdigit():
                    return Response(
                        {'error': f'{param} must be a valid integer, got "{value}".'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = qs.filter(**{field_lookup: int(value)})

        # M2M joins (education_levels__, streams__) can duplicate a row in
        # the result set; collapse duplicates back to one row per exam.
        if request.query_params.get('education_level', '').strip() or \
           request.query_params.get('stream', '').strip():
            qs = qs.distinct()

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(exam_name__icontains=search) |
                Q(exam_code__icontains=search) |
                Q(conducting_body__icontains=search)
            )

        page_param = request.query_params.get('page', '1').strip()
        page_number = int(page_param) if page_param.isdigit() else 1

        paginator = Paginator(qs, self.PAGE_SIZE)
        page = paginator.get_page(page_number)

        serializer = ExamSerializer(page.object_list, many=True)
        return Response({'results': serializer.data, 'count': paginator.count})

    def post(self, request):
        """
        POST /api/exams/
        Body: the CreateExamView.vue `form` object, mapped through
        ExamCreateUpdateSerializer (see serializers.py for the exact
        field-name mapping — e.g. camelCase `examLogo` isn't auto-mapped,
        the frontend api layer flattens `form` into snake_case first).

        `status` in the body controls draft vs publish:
          status: 'draft'     -> Save as Draft button
          status: 'published' -> Publish Exam button
        Defaults to 'draft' if omitted.
        """
        serializer = ExamCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        response_data = ExamFullDetailSerializer(exam).data
        response_data['syllabus'] = SubjectSerializer(exam.subject_set.all(), many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class ExamDetailView(APIView):
    """
    GET    /api/exams/<exam_id>/   — full exam incl. nested detail/pattern/
                                      boards/important_dates/eligibility,
                                      for re-opening the wizard on an
                                      existing draft/published exam.
    PUT    /api/exams/<exam_id>/   — full update (same payload shape as POST).
    PATCH  /api/exams/<exam_id>/   — partial update, e.g. just {"status": "published"}
                                      for a lightweight publish action.
    """
    def get_object(self, exam_id):
        try:
            return Exam.objects.get(exam_id=exam_id)
        except Exam.DoesNotExist:
            return None

    def get(self, request, exam_id):
        exam = self.get_object(exam_id)
        if exam is None:
            return Response({'error': f'No exam found with exam_id "{exam_id}".'}, status=status.HTTP_404_NOT_FOUND)
        # FIX: ExamFullDetailSerializer was never defined/imported anywhere
        # in serializers.py, so this endpoint raised a NameError -> 500 on
        # every call. That silently broke the mock-test edit flow: the
        # frontend's fetchExamDetail() call failed, was swallowed by a
        # try/catch, and left examTypeId/categoryId empty on
        # CreateMockTestView.vue's edit-mode hydration. ExamSerializer
        # already exposes everything this GET needs (exam_type, category_id,
        # exam_type_name, category_name, question_count, etc.) so it's used
        # here instead. If a richer payload (nested pattern/boards/dates/
        # eligibility) is genuinely needed for another consumer of this
        # endpoint, that should be a dedicated serializer, not this fix.
        data = ExamSerializer(exam).data
        data['syllabus'] = SubjectSerializer(exam.subject_set.all(), many=True).data
        return Response(data)

    def put(self, request, exam_id):
        exam = self.get_object(exam_id)
        if exam is None:
            return Response({'error': f'No exam found with exam_id "{exam_id}".'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExamCreateUpdateSerializer(exam, data=request.data)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        response_data = ExamFullDetailSerializer(exam).data
        response_data['syllabus'] = SubjectSerializer(exam.subject_set.all(), many=True).data
        return Response(response_data)

    def patch(self, request, exam_id):
        exam = self.get_object(exam_id)
        if exam is None:
            return Response({'error': f'No exam found with exam_id "{exam_id}".'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExamCreateUpdateSerializer(exam, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        response_data = ExamFullDetailSerializer(exam).data
        response_data['syllabus'] = SubjectSerializer(exam.subject_set.all(), many=True).data
        return Response(response_data)




class MockExamListView(APIView):
    """
    GET  /api/mockexams/?exam_code=&exam_id=&exam_type=&category_id=&status=&page=&page_size=&search=
    POST /api/mockexams/

    GET returns MockExam rows ("JEE Main 2024 Shift 1", etc).

    Two call shapes are supported:

    1. SCOPED TO ONE EXAM PROGRAM (student "Select Mock Test" screen,
       step 3 of Practice/Mock flow) — pass exam_code or exam_id and you
       get back only that program's mock tests, exactly as before.

    2. UNSCOPED / ADMIN TABLE (Exam Admin -> Mock Tests page) — omit
       both exam_code and exam_id and you get back mock tests across
       ALL exam programs, optionally narrowed by exam_type, category_id,
       and status. This is what MockTestsView.vue's listMockExams() call
       hits; it has no single exam in scope, it's browsing everything.

    exam_code takes priority over exam_id if both are passed.

    GET params:
        exam_code   – Exam.exam_code, e.g. "JEE-MAIN". Optional — when
                      omitted (along with exam_id), results are not
                      scoped to a single exam program.
        exam_id     – PK of the parent Exam. Optional alternative to
                      exam_code. Also optional for the same reason.
        exam_type   – PK of ExamType. Only applies when NOT scoped to a
                      single exam via exam_code/exam_id (admin table use).
        category_id – PK of ExamCategory. Same scoping note as exam_type.
        status      – 'Published' | 'Draft' | 'Archived'. Filters on
                      is_active / is_archived (see mapping below). When
                      omitted, both active and inactive mock exams are
                      returned (the old hardcoded is_active=True is gone —
                      that was hiding drafts from the admin table).
        page        – page number, default 1.
        page_size   – results per page, default 20 (was hardcoded PAGE_SIZE).
        search      – optional icontains match on mockexam_name.

    NEW: POST creates a MockExam. This is what the admin "Create Mock
    Test" wizard's final "Confirm & Create" button (ReviewConfirmStep)
    calls, after collecting data across BasicDetailsStep + SelectExamStep
    + SetPatternStep. Body (flattened by the frontend api layer —
    see mockTestApi.ts):
        exam                (required) – PK of the parent Exam, chosen
                              in SelectExamStep (form.examId, resolved
                              from the exam search box)
        mockexam_name       (required) – BasicDetailsStep form.name
        year                (optional) – BasicDetailsStep form.year
        description         (optional) – BasicDetailsStep form.description
        total_marks         (optional) – BasicDetailsStep form.totalMarks,
                              or SetPatternStep's computed subject total
                              if the frontend prefers that value instead
        duration_minutes    (optional) – BasicDetailsStep form.duration
        is_active           (optional, default True) – BasicDetailsStep
                              form.active toggle
        pattern             (optional) – the entire SetPatternStep.form
                              object as-is: { totalQuestions,
                              marksPerQuestion, negativeMarking,
                              sectionalTime, sectionalMinutes, subjects }
    Returns the created MockExam shaped like the GET list response
    (via MockExamSerializer) so the frontend can redirect straight into
    a "mock test created" confirmation without a second round-trip.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    DEFAULT_PAGE_SIZE = 20

    def get(self, request):
        exam_code = request.query_params.get('exam_code', '').strip()
        exam_id   = request.query_params.get('exam_id', '').strip()
        scoped_to_one_exam = bool(exam_code or exam_id)

        qs = MockExam.objects.annotate(
            question_count=Count('question', filter=Q(question__is_active=True), distinct=True)
        )

        if exam_code:
            qs = qs.filter(exam__exam_code=exam_code)
        elif exam_id:
            if not exam_id.isdigit():
                return Response(
                    {'error': f'exam_id must be a valid integer, got "{exam_id}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(exam_id=int(exam_id))

        if not scoped_to_one_exam and not qs.exists() and exam_code:
            # exam_code didn't match any Exam row at all — distinguish
            # "wrong/unknown code" from "valid exam, just no mock tests yet"
            if not Exam.objects.filter(exam_code=exam_code).exists():
                return Response(
                    {'error': f'No exam found with exam_code "{exam_code}".'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # These two only make sense when browsing across exams (admin
        # table). If a specific exam is already selected via exam_code/
        # exam_id, exam_type/category_id are redundant, so they're
        # ignored in that case rather than silently narrowing results
        # to zero on a mismatch.
        if not scoped_to_one_exam:
            exam_type = request.query_params.get('exam_type', '').strip()
            category_id = request.query_params.get('category_id', '').strip()
            if exam_type:
                qs = qs.filter(exam__exam_type_id=exam_type)
            if category_id:
                qs = qs.filter(exam__category_id=category_id)

        # status: 'Active' -> is_active True, 'Inactive' -> is_active
        # False. No status param -> return everything, so "All Status"
        # on the admin table actually shows all mock tests.
        status_param = request.query_params.get('status', '').strip()
        if status_param == 'Active':
            qs = qs.filter(is_active=True)
        elif status_param == 'Inactive':
            qs = qs.filter(is_active=False)

        qs = qs.select_related('exam').order_by('-year', 'mockexam_name')

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(mockexam_name__icontains=search)

        page_param = request.query_params.get('page', '1').strip()
        page_number = int(page_param) if page_param.isdigit() else 1

        page_size_param = request.query_params.get('page_size', '').strip()
        page_size = int(page_size_param) if page_size_param.isdigit() else self.DEFAULT_PAGE_SIZE

        paginator = Paginator(qs, page_size)
        page = paginator.get_page(page_number)

        serializer = MockExamSerializer(page.object_list, many=True)
        return Response({'results': serializer.data, 'count': paginator.count})

    def post(self, request):
        serializer = MockExamCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mockexam = serializer.save()

        # Re-annotate a fresh queryset for this one row so question_count
        # (an annotation, not a real column — see GET above) is present
        # in the response the same way it is in the list endpoint.
        mockexam = (
            MockExam.objects
            .filter(pk=mockexam.pk)
            .annotate(question_count=Count(
                'question', filter=Q(question__is_active=True), distinct=True
            ))
            .select_related('exam')
            .first()
        )
        return Response(
            MockExamSerializer(mockexam).data,
            status=status.HTTP_201_CREATED,
        )

def _annotated_mockexam(mockexam_id: int):
    """
    Return a single MockExam with question_count annotation and
    all related objects pre-fetched, exactly as MockExamListView does.
    Returns None if not found.
    """
    return (
        MockExam.objects
        .filter(pk=mockexam_id)
        .select_related(
            'exam',
            'exam__exam_type',
            'exam__category',
        )
        .annotate(
            question_count=Count(
                'question',
                filter=Q(question__is_active=True),
                distinct=True,
            )
        )
        .first()
    )

# ─────────────────────────────────────────────────────────────
# MockExamStatsView
# GET /api/mockexams/stats/
# ─────────────────────────────────────────────────────────────

class MockExamStatsView(APIView):
    """
    GET /api/mockexams/stats/

    Powers the 3 stat cards at the top of the Mock Tests admin table
    (Total Mock Tests / Active / Inactive). Matches the MockExamStats
    interface in mockTestApi.ts: { total, published, draft, archived }.

    NOTE: this was entirely missing before — fetchMockExamStats() on the
    frontend had nothing to call, hence the 404. There's no is_archived
    field on MockExam yet, so `archived` is always 0 for now; add a real
    field/query here if that status gets introduced later.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        total = MockExam.objects.count()
        published = MockExam.objects.filter(is_active=True).count()
        draft = MockExam.objects.filter(is_active=False).count()
        archived = 0

        return Response({
            'total': total,
            'published': published,
            'draft': draft,
            'archived': archived,
        })


def _annotated_mockexam(mockexam_id: int):
    """
    Return a single MockExam with question_count annotation and
    all related objects pre-fetched, exactly as MockExamListView does.
    Returns None if not found.

    CHANGED: select_related('exam__category') was removed — Exam has no
    real `category` relation. `Exam.category_id` is a plain IntegerField
    (a manual polymorphic pointer into one of SchoolExamCategory /
    EntranceExamCategory / JobExamCategory, resolved by exam_type — see
    ExamCategoryListView). select_related() validates its paths against
    real FK/O2O relations at query time, so 'exam__category' raised a
    FieldError the moment this queryset was evaluated — that FieldError
    was the actual cause of the 500 on GET /mockexams/<id>/. The list
    endpoint (MockExamListView) never hit this because it only calls
    .select_related('exam') and lets MockExamSerializer.category_name's
    dotted `source` silently fall back to its `default=None` instead of
    raising, which is a serialization-time safety net that doesn't apply
    to invalid select_related() query paths.
    """
    return (
        MockExam.objects
        .filter(pk=mockexam_id)
        .select_related(
            'exam',
            'exam__exam_type',
        )
        .annotate(
            question_count=Count(
                'question',
                filter=Q(question__is_active=True),
                distinct=True,
            )
        )
        .first()
    )
 

# ─────────────────────────────────────────────────────────────
# MockExamDetailView  (replaces / extends the existing one)
# GET / PUT / PATCH / DELETE  →  /api/mockexams/<mockexam_id>/
# ─────────────────────────────────────────────────────────────
 
class MockExamDetailView(APIView):
    """
    GET    → Full mock test detail (used by the 👁 View action button).
             Returns the same shape as the list endpoint so the frontend
             can render a read-only detail modal/page without extra mapping.
 
    PUT    → Full update (used by the ✏ Edit action — "Save" on the
             wizard's Review & Confirm step after editing all fields).
             Body: same payload as POST /api/mockexams/.
 
    PATCH  → Partial update. Used two ways:
               a) Individual field update (e.g. { "is_active": true })
               b) Inline cell edit on the list table (e.g. change name)
 
    DELETE → Soft-delete or hard-delete based on whether the mock exam
             has questions linked to it:
               • No questions → hard delete (gone from DB).
               • Has questions → returns 409 Conflict with counts so
                 the frontend can show a confirmation modal ("This mock
                 test has N questions. Delete anyway?") and re-call with
                 ?force=true to confirm the hard delete including children.
 
    All responses include the standard MockExamSerializer shape so the
    Vue list component can update its local row immediately from the
    response without a full re-fetch.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
 
    def _get_or_404(self, mockexam_id: int):
        obj = _annotated_mockexam(mockexam_id)
        if obj is None:
            return None
        return obj
 
    # ── GET ───────────────────────────────────────────────────
    def get(self, request, mockexam_id: int):
        """
        GET /api/mockexams/<mockexam_id>/
 
        Returns full mock test detail.
        Used by the 👁 View button to open a detail modal/page.
 
        Response shape: MockExamSerializer (same as list rows) + extra
        fields useful on the detail page:
          subjects      — list of subject dicts from pattern JSON
          total_questions — question_count annotation
        """
        obj = self._get_or_404(mockexam_id)
        if obj is None:
            return Response(
                {'error': f'No mock test found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        data = MockExamSerializer(obj).data
 
        # Enrich with subject breakdown from the stored pattern JSON
        # and the live question count per subject for the detail panel.
        pattern = getattr(obj, 'pattern', None) or {}
        subjects_pattern = pattern.get('subjects', []) if isinstance(pattern, dict) else []
 
        # Live question count per subject (for the detail view table)
        subject_question_counts = (
            Question.objects
            .filter(_mock_question_q(mockexam_id), is_active=True)
            .values('chapter__subject__subject_name')
            .annotate(count=Count('question_id'))
        )
        counts_map = {
            r['chapter__subject__subject_name']: r['count']
            for r in subject_question_counts
        }
 
        data['subjects_detail'] = [
            {
                'name':              s.get('name', ''),
                'planned_questions': s.get('questions', 0),
                'planned_marks':     s.get('marks', 0),
                'uploaded_questions': counts_map.get(s.get('name', ''), 0),
            }
            for s in subjects_pattern
        ]
 
        return Response(data, status=status.HTTP_200_OK)
 
    # ── PUT ───────────────────────────────────────────────────
    def put(self, request, mockexam_id: int):
        """
        PUT /api/mockexams/<mockexam_id>/
 
        Full update — replaces all fields.
        The ✏ Edit wizard calls this on its "Save Changes" button.
 
        Body: same as POST /api/mockexams/
            exam, mockexam_name, year, description,
            total_marks, duration_minutes, pattern, is_active
        """
        obj = _annotated_mockexam(mockexam_id)
        if obj is None:
            return Response(
                {'error': f'No mock test found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        serializer = MockExamCreateUpdateSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
 
        return Response(
            MockExamSerializer(_annotated_mockexam(updated.pk)).data,
            status=status.HTTP_200_OK,
        )
 
    # ── PATCH ─────────────────────────────────────────────────
    def patch(self, request, mockexam_id: int):
        """
        PATCH /api/mockexams/<mockexam_id>/
 
        Partial update — only the fields present in the body are changed.
 
        Common uses from the frontend:
          { "is_active": true }               → publish / activate
          { "is_active": false }              → deactivate
          { "mockexam_name": "New Name" }     → inline name edit
          { "duration_minutes": 180 }         → inline duration edit
        """
        obj = _annotated_mockexam(mockexam_id)
        if obj is None:
            return Response(
                {'error': f'No mock test found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        serializer = MockExamCreateUpdateSerializer(
            obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
 
        return Response(
            MockExamSerializer(_annotated_mockexam(updated.pk)).data,
            status=status.HTTP_200_OK,
        )
 
    # ── DELETE ────────────────────────────────────────────────
    def delete(self, request, mockexam_id: int):
        """
        DELETE /api/mockexams/<mockexam_id>/
 
        Query params:
            force=true  — required to delete a mock exam that has
                          questions. Without it, returns 409 Conflict
                          with question counts so the UI can show a
                          confirmation dialog.
 
        Behaviour:
        1. If no questions exist → hard delete immediately (204).
        2. If questions exist and force != 'true' → 409 Conflict with
           counts, the frontend shows a "Are you sure?" modal.
        3. If questions exist and force=true → delete all child
           questions (+ their options / correct answers via CASCADE)
           then delete the mock exam. Returns 200 with a summary.
 
        Why not soft-delete?
        MockExam has no `is_deleted` / `deleted_at` column (per the
        model file — is_active is for publish/unpublish, not deletion).
        If you add a soft-delete column later, swap the `.delete()` call
        for a `.save()` with `is_deleted=True` and filter it out of the
        list endpoint.
        """
        try:
            obj = MockExam.objects.get(pk=mockexam_id)
        except MockExam.DoesNotExist:
            return Response(
                {'error': f'No mock test found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        force = request.query_params.get('force', '').lower() == 'true'
 
        # Count linked questions (active + inactive)
        question_count = Question.objects.filter(mock_exam_id=mockexam_id).count()
 
        if question_count > 0 and not force:
            # Return conflict so the frontend can confirm
            return Response(
                {
                    'error': 'This mock test has linked questions.',
                    'detail': (
                        f'Deleting "{obj.mockexam_name}" will also permanently '
                        f'delete {question_count} question(s) and all their '
                        f'options and answers. '
                        f'Re-send with ?force=true to confirm.'
                    ),
                    'mockexam_id':    mockexam_id,
                    'mockexam_name':  obj.mockexam_name,
                    'question_count': question_count,
                },
                status=status.HTTP_409_CONFLICT,
            )
 
        # Snapshot name before deletion for the response
        name = obj.mockexam_name
 
        try:
            obj.delete()  # Django CASCADE handles Question/Option/Answer rows
        except ProtectedError as exc:
            # Handles FK relations that use PROTECT instead of CASCADE
            return Response(
                {
                    'error': 'Cannot delete: other records depend on this mock test.',
                    'detail': str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )
 
        return Response(
            {
                'message':        f'Mock test "{name}" deleted successfully.',
                'mockexam_id':    mockexam_id,
                'questions_deleted': question_count,
            },
            status=status.HTTP_200_OK,
        )
 
 
# ─────────────────────────────────────────────────────────────
# MockExamToggleStatusView
# PATCH  →  /api/mockexams/<mockexam_id>/toggle-status/
# ─────────────────────────────────────────────────────────────
 
class MockExamToggleStatusView(APIView):
    """
    PATCH /api/mockexams/<mockexam_id>/toggle-status/
 
    One-click active ↔ inactive toggle for the status pill in the
    actions column. No request body needed — flips is_active and
    returns the updated row.
 
    Why a separate endpoint instead of PATCH with { is_active }?
    The list table's status pill/badge is a toggle button, not a form.
    A dedicated URL makes the Vue component's onClick handler a single
    api call with no payload construction:
        await toggleMockExamStatus(row.mockexam_id)
    and the caller can immediately update its local row from the
    response without re-fetching the whole list.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
 
    def patch(self, request, mockexam_id: int):
        try:
            obj = MockExam.objects.get(pk=mockexam_id)
        except MockExam.DoesNotExist:
            return Response(
                {'error': f'No mock test found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
 
        annotated = _annotated_mockexam(mockexam_id)
        return Response(
            {
                'mockexam_id': mockexam_id,
                'is_active':   obj.is_active,
                'status_label': 'Active' if obj.is_active else 'Inactive',
                'row': MockExamSerializer(annotated).data,
            },
            status=status.HTTP_200_OK,
        )


class SubjectListView(APIView):
    """
    GET /api/subjects/
    Params (priority order — first match wins):
        exam_id   (integer) – numeric PK of Exam       [highest priority]
        exam_code (integer or string) – numeric treated as PK,
                   otherwise matched against Exam.exam_code

    CHANGED: `exam_category` (free text, e.g. 'JEE') has been dropped —
    Exam has no such column. Resolve the exam_id first via
    /api/exams/?exam_type=&category_id=... if you only have a category.

    ADDED: when NEITHER exam_id nor exam_code is given, return every
    subject across every exam in a single query instead of 400ing.
    This is what the admin "All Subjects" list page needs — it used to
    call /api/exams/ then fire one /api/subjects/?exam_id=X request per
    exam (N+1), which never finishes once there are hundreds of exams.
    One query with select_related('exam') avoids that entirely, and the
    exam's name/code/streams/education levels are included directly so
    the frontend doesn't need a second round-trip per row either.
    ADDED: POST /api/subjects/ creates a new subject. Body:
        exam_id       (required) – integer PK of Exam
        subject_name  (required) – string
    Previously this class only had get() — the Add Subject page's
    "Save Subject" / "Save & Add Another" buttons had nothing to call,
    so they silently did nothing.

    NOTE: the frontend form also collects "Subject Code" and "Active"
    values, but Subject has no subject_code/is_active columns (kept
    as-is per instruction not to touch the model), so those two values
    are accepted here but NOT persisted — see the response comment
    below.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        exam_id = request.data.get('exam_id')
        subject_name = (request.data.get('subject_name') or '').strip()

        if not exam_id:
            return Response({'error': 'exam_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not subject_name:
            return Response({'error': 'subject_name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': f'No exam found with id {exam_id}.'}, status=status.HTTP_404_NOT_FOUND)
        except (TypeError, ValueError):
            return Response({'error': f'exam_id must be a valid integer, got "{exam_id}".'}, status=status.HTTP_400_BAD_REQUEST)

        subject = Subject.objects.create(
            exam=exam,
            subject_name=subject_name,
        )

        return Response({
            'subject_id': subject.subject_id,
            'subject_name': subject.subject_name,
            # subject_code / is_active are NOT real columns on Subject
            # right now, so nothing was actually saved for them — this
            # just echoes back the exam's own is_active for display
            # consistency, matching what the GET list already does.
            'exam_id': exam.pk,
            'exam_name': exam.exam_name,
            'exam_code': exam.exam_code,
            'is_active': exam.is_active,
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        exam_id = request.query_params.get('exam_id', '').strip()
        exam_code = request.query_params.get('exam_code', '').strip()

        if not exam_id and not exam_code:
            subjects = (
                Subject.objects
                .select_related('exam', 'exam__exam_type')
                .prefetch_related('exam__education_levels', 'exam__streams')
                .annotate(chapter_count=Count('chapter', filter=~Q(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)))
                .order_by('exam__exam_name', 'subject_name')
            )
            data = [{
                'subject_id': s.subject_id,
                'subject_name': s.subject_name,
                'chapter_count': s.chapter_count,
                'exam_id': s.exam_id,
                'exam_name': s.exam.exam_name if s.exam else '',
                'exam_code': s.exam.exam_code if s.exam else '',
                'stream_names': [st.stream_name for st in s.exam.streams.all()] if s.exam else [],
                'education_level_names': [
                    el.education_level for el in s.exam.education_levels.all()
                ] if s.exam else [],
                'is_active': s.exam.is_active if s.exam else True,
            } for s in subjects]

            return Response({
                'exam_id': None,
                'count': len(data),
                'subjects': data,
            })

        resolved_exam_id = None

        if exam_id:
            if not exam_id.isdigit():
                return Response(
                    {'error': f'exam_id must be a valid integer, got "{exam_id}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            resolved_exam_id = int(exam_id)
            subjects = (
                Subject.objects
                .filter(exam_id=resolved_exam_id)
                .annotate(chapter_count=Count('chapter', filter=~Q(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)))
                .order_by('subject_name')
            )

        else:
            if exam_code.isdigit():
                resolved_exam_id = int(exam_code)
                subjects = (
                    Subject.objects
                    .filter(exam_id=resolved_exam_id)
                    .annotate(chapter_count=Count('chapter', filter=~Q(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)))
                    .order_by('subject_name')
                )
            else:
                subjects = (
                    Subject.objects
                    .filter(exam__exam_code__iexact=exam_code)
                    .annotate(chapter_count=Count('chapter', filter=~Q(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)))
                    .order_by('subject_name')
                )

        serializer = SubjectSerializer(subjects, many=True)
        return Response({
            'exam_id': resolved_exam_id,
            'count': len(serializer.data),
            'subjects': serializer.data,
        })


class ChapterListView(APIView):
    """
    GET /api/chapters/
    Params:
        subject_id (required) – PK of Subject

    CHANGED: Question has no `status` field — filtering now uses the
    real `is_active` boolean instead of the old string-variant matching.
    """

    def get(self, request):
        subject_id = request.query_params.get('subject_id', '').strip()

        if not subject_id:
            return Response({'error': 'subject_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not subject_id.isdigit():
            return Response(
                {'error': f'subject_id must be a valid integer, got "{subject_id}".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        chapters = (
            Chapter.objects
            .filter(subject_id=int(subject_id))
            .exclude(chapter_name__iexact=IMPORTED_CHAPTER_NAME)   # never list the ungrouped bucket
            .annotate(question_count=Count('question', filter=Q(question__is_active=True)))
            .order_by('chapter_name')
        )

        serializer = ChapterSerializer(chapters, many=True)
        return Response({
            'subject_id': int(subject_id),
            'count': len(serializer.data),
            'chapters': serializer.data,
        })


class CustomQuestionListView(APIView):
    """
    GET /api/questions/custom/
    Params:
        subject_ids  (required unless mock_exam_id is given) – comma-separated
                     Subject PKs, OR "all" combined with exam_id
        exam_id      (required only when subject_ids="all")
        mock_exam_id (optional) – PK of a MockExam. When given, returns
                     ONLY that mock test's own questions (Question.mock_exam_id),
                     ignoring subject_ids/exam_id entirely. This is what a
                     mock-test attempt screen should call — using exam_id
                     alone would return every question under the parent
                     Exam, including OTHER mock tests' questions if more
                     than one exists for the same exam.
        difficulty   (optional) – "easy" | "medium" | "hard" | "mixed" (default: mixed)
        count        (optional) – number of questions to return, default 50

    CHANGED: `exam_category` support is gone (pass exam_id instead).
    Question has no `subject` FK — subject filtering now goes through
    `chapter__subject_id`, since Question only links to Chapter directly.
    `status` string-matching replaced with the real `is_active` boolean.
    ADDED: mock_exam_id branch (see above) — previously there was no way
    to fetch a specific mock test's questions at all; a mock-attempt
    screen calling this with exam_id would get every question tagged to
    the parent Exam, not just the ones belonging to that one mock paper.
    """

    def get(self, request):
        subject_ids_param = request.query_params.get('subject_ids', '').strip()
        exam_id_param = request.query_params.get('exam_id', '').strip()
        mock_exam_id_param = request.query_params.get('mock_exam_id', '').strip()
        difficulty = request.query_params.get('difficulty', 'mixed').strip().lower()
        count_param = request.query_params.get('count', '50').strip()

        if not subject_ids_param and not mock_exam_id_param:
            return Response(
                {'error': 'subject_ids (or mock_exam_id) is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not count_param.isdigit() or int(count_param) <= 0:
            return Response(
                {'error': f'count must be a positive integer, got "{count_param}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        count = int(count_param)

        qs = Question.objects.filter(is_active=True)

        if mock_exam_id_param:
            if not mock_exam_id_param.isdigit():
                return Response(
                    {'error': f'mock_exam_id must be a valid integer, got "{mock_exam_id_param}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(_mock_question_q(int(mock_exam_id_param)))   # own + merged (appearances) questions
        elif subject_ids_param.lower() == 'all':
            if not exam_id_param:
                return Response(
                    {'error': 'exam_id is required when subject_ids="all".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not exam_id_param.isdigit():
                return Response(
                    {'error': f'exam_id must be a valid integer, got "{exam_id_param}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(
                Q(exam_id=int(exam_id_param)) | Q(chapter__subject__exam_id=int(exam_id_param))
            )
            # imported PYQs without a real chapter are mock-test-only
            qs = qs.exclude(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME) \
                   .exclude(chapter__isnull=True, is_previousyear=True)
        else:
            ids = [s.strip() for s in subject_ids_param.split(',') if s.strip()]
            if not all(s.isdigit() for s in ids):
                return Response(
                    {'error': f'subject_ids must all be valid integers, got "{subject_ids_param}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(chapter__subject_id__in=[int(s) for s in ids]) \
                   .exclude(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)

        if difficulty != 'mixed':
            qs = qs.filter(difficulty_level__iexact=difficulty)

        qs = (
            qs.select_related('chapter__subject')
              .prefetch_related('questionoption_set', 'solution_set', 'correctanswer_set')
              .order_by('question_id')[:count]
        )

        serializer = QuestionSerializer(qs, many=True, context={'mode': 'test'})

        return Response({
            'difficulty': difficulty,
            'count': len(serializer.data),
            'questions': serializer.data,
        })

@method_decorator(csrf_exempt, name='dispatch')
class CheckDuplicateQuestionView(APIView):
    """
    POST /api/questions/check-duplicate/

    Called from Step 2 (Question Details) of the "Add New Question" wizard —
    on blur of the question-text field, and again as a guard before "Next
    Step" — to warn the admin the exact same question text already exists,
    and (if that existing question is a PYQ) offer to map the new PYQ
    exam/year/session onto a fresh Question row instead of creating an
    unrelated duplicate.

    Request body:
        question_text  (required) str
        chapter_id     (optional) int – narrows the match to the same
                        chapter, since the same question text could
                        legitimately exist under different chapters/exams.

    Response:
        { "duplicate": false }
        or
        {
          "duplicate": true,
          "question_id": 123,
          "existing": {
            "exam_name": "JEE_MAIN",
            "pyq_exam_name": "NEET-UG",
            "year": 2023,
            "session": "Shift 1"
          }
        }

    Matching is on a normalized (trimmed, whitespace-collapsed,
    case-insensitive) comparison of question_text — good enough to catch
    copy-pasted PYQs without needing fuzzy/similarity matching.

    IMPORTANT — intentionally NOT scoped to chapter_id: Subject belongs to
    a single Exam and Chapter belongs to Subject, so every exam has its
    own separate Chapter rows even for a subject with the same name (e.g.
    JEE Main's "Circuits" chapter and NEET's "Circuits" chapter are
    different rows with different ids). The whole purpose of this check
    is to catch the *same* question text being re-added under a
    *different* exam, which by definition means a different chapter_id.
    Filtering on chapter_id would make that case unmatchable and silently
    defeat the duplicate check. chapter_id is accepted for logging/future
    use but is never used to narrow the match.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        question_text = (data.get('question_text') or '').strip()

        if not question_text:
            return Response({'error': 'question_text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        normalized = ' '.join(question_text.split())

        qs = Question.objects.filter(question_text__iexact=normalized)

        existing_question = qs.select_related('pyq_exam', 'exam').order_by('-question_id').first()

        if not existing_question:
            return Response({'duplicate': False})

        # `exam` is the source of truth for which exam this question is
        # actually filed under (it's derived strictly from the question's
        # chapter, which belongs to exactly one exam). `pyq_exam` is
        # separate metadata about which exam's *paper* the question
        # originally came from, and can legitimately differ or be stale —
        # it must never be preferred over `exam` here, or the modal ends
        # up showing the wrong "already added in" exam (as happened with
        # Q2269: exam was corrected to JEE_MAIN but pyq_exam was still
        # pointing at NEET-UG from the original bad save).
        # Expose the current exam (source of truth, chapter-derived) and
        # the pyq_exam (separate "which paper did this PYQ come from"
        # metadata) as distinct fields, rather than collapsing them into
        # one — so the frontend can show both and admins can immediately
        # spot a mismatch like Q2269's (exam=JEE_MAIN, pyq_exam=NEET-UG
        # left over from the earlier bad save).
        existing_payload = {
            'exam_name': existing_question.exam.exam_name if existing_question.exam else None,
            'pyq_exam_name': existing_question.pyq_exam.exam_name if existing_question.pyq_exam else None,
            'year': existing_question.pyq_year,
            'session': existing_question.pyq_session,
        }

        return Response({
            'duplicate': True,
            'question_id': existing_question.question_id,
            'existing': existing_payload,
        })

@method_decorator(csrf_exempt, name='dispatch')
class AddQuestionView(APIView):
    """
    POST /api/questions/add/

    Backs the 4-step "Add New Question" admin wizard
    (QuestionClassification -> QuestionEditor -> OptionsAnswer ->
    MarksEvaluation) with a single call on the final "Save" step.

    Accepts multipart/form-data (so the optional question image can ride
    alongside the JSON fields) OR a plain JSON body if there's no image.

    Body fields:
        exam_id          (optional) int  – falls back to chapter's exam if omitted
        chapter_id       (required) int
        question_type    (required) str  – single_correct | multiple_correct | integer | subjective
        difficulty       (required) str  – easy | medium | hard
        question_text    (required) str  – plain text of the question stem
        options          (required) JSON string or list –
                          [{"id": 1, "text": "..."}, ...] (2-6 entries, at
                          least 2 with non-empty text)
        correct_answer   (required)      – the `id` (from `options`) of the
                          correct option
        correct_marks    (required) number
        negative_marks   (optional) number, default 0
        enable_negative  (optional) bool, default true — when false,
                          negative_marks is stored as 0 regardless of what
                          was sent
        explanation      (optional) str  – creates a Solution row if present
        image            (optional) file – question stem image
        is_pyq           (optional) bool, default false – marks the question
                          as a Previous Year Question (stored as
                          Question.is_previousyear)
        pyq_exam_id      (required if is_pyq) int – exam this PYQ appeared in
        pyq_year         (required if is_pyq) int – year it appeared
        pyq_session      (optional) str – e.g. "Shift 1", "Shift 2"

    NOTE — Topic: the wizard's "Topic" dropdown has no backing table yet
    (no Topic model exists in models.py, and Question has no topic FK).
    Any `topic_id` sent is accepted but silently ignored so the request
    doesn't fail — nothing is persisted for it. Add a Topic model +
    FK/M2M on Question first if this needs to be stored and filtered on.

    Returns the created question serialized via QuestionSerializer
    (mode='practice', so options/correct answer/explanation are included).
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    VALID_TYPES = ('single_correct', 'multiple_correct', 'integer', 'subjective')
    VALID_DIFFICULTIES = ('easy', 'medium', 'hard')
    OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

    def post(self, request):
        data = request.data

        exam_id = data.get('exam_id')
        chapter_id = data.get('chapter_id')
        question_type = (data.get('question_type') or '').strip()
        difficulty = (data.get('difficulty') or '').strip()
        question_text = (data.get('question_text') or '').strip()
        correct_answer_id = data.get('correct_answer')
        explanation = (data.get('explanation') or '').strip()

        # Set on Step 2 of the wizard when the admin confirmed the
        # "Question Already Added" modal and chose to map this new PYQ
        # onto another exam/year rather than cancel. Purely for audit —
        # does not change how the new Question row is created below.
        mapped_from_question_id = data.get('mapped_from_question_id')

        # ---- PYQ (Previous Year Question) fields ----
        is_pyq = str(data.get('is_pyq', 'false')).lower() in ('true', '1', 'yes')
        pyq_exam_id = data.get('pyq_exam_id')
        pyq_year = data.get('pyq_year')
        pyq_session = (data.get('pyq_session') or '').strip()

        enable_negative = str(data.get('enable_negative', 'true')).lower() in ('true', '1', 'yes')

        raw_options = data.get('options')
        if isinstance(raw_options, str):
            try:
                raw_options = json.loads(raw_options)
            except (TypeError, ValueError):
                return Response({'errors': {'options': 'options must be valid JSON.'}}, status=status.HTTP_400_BAD_REQUEST)

        # ---- field-level validation ----
        errors = {}

        if not chapter_id:
            errors['chapter_id'] = 'This field is required.'

        if question_type not in self.VALID_TYPES:
            errors['question_type'] = f'Must be one of {", ".join(self.VALID_TYPES)}.'

        if difficulty not in self.VALID_DIFFICULTIES:
            errors['difficulty'] = f'Must be one of {", ".join(self.VALID_DIFFICULTIES)}.'

        if not question_text:
            errors['question_text'] = 'This field is required.'

        if not raw_options or not isinstance(raw_options, list):
            errors['options'] = 'A list of at least 2 options is required.'

        if correct_answer_id in (None, ''):
            errors['correct_answer'] = 'This field is required.'

        # PYQ Exam / PYQ Year are required only when is_pyq is true.
        pyq_year_int = None
        if is_pyq:
            if not pyq_exam_id:
                errors['pyq_exam_id'] = 'This field is required when the question is marked as PYQ.'
            if not pyq_year:
                errors['pyq_year'] = 'This field is required when the question is marked as PYQ.'
            else:
                try:
                    pyq_year_int = int(pyq_year)
                except (TypeError, ValueError):
                    errors['pyq_year'] = 'Must be a valid year.'

        try:
            correct_marks = float(data.get('correct_marks'))
        except (TypeError, ValueError):
            errors['correct_marks'] = 'Must be a number.'
            correct_marks = None

        negative_marks = 0
        if enable_negative:
            try:
                negative_marks = float(data.get('negative_marks', 0) or 0)
            except (TypeError, ValueError):
                errors['negative_marks'] = 'Must be a number.'

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # ---- resolve chapter / exam ----
        try:
            chapter = Chapter.objects.select_related('subject__exam').get(pk=chapter_id)
        except (Chapter.DoesNotExist, ValueError, TypeError):
            return Response({'error': f'No chapter found with id {chapter_id}.'}, status=status.HTTP_404_NOT_FOUND)

        exam = chapter.subject.exam if chapter.subject_id else None

        # NOTE: exam_id is intentionally NOT used to override the exam
        # derived from the chosen chapter. Chapter -> Subject -> Exam is a
        # strict one-to-one chain (every exam has its own Chapter rows,
        # even for identically-named subjects/chapters), so the chapter
        # already fully determines the exam. Previously a separately
        # submitted exam_id would silently override this and could save
        # the question under the wrong exam if the frontend's exam_id
        # field was stale (e.g. left over from a previous dropdown
        # selection). Now we just validate exam_id agrees, if supplied,
        # instead of trusting it blindly.
        if exam_id and exam and str(exam_id) != str(exam.exam_id):
            return Response(
                {'errors': {'exam_id': (
                    f"exam_id {exam_id} does not match the exam for the selected chapter "
                    f"(chapter {chapter_id} belongs to exam {exam.exam_id} - {exam.exam_name})."
                )}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pyq_exam = None
        if is_pyq and pyq_exam_id:
            try:
                pyq_exam = Exam.objects.get(pk=pyq_exam_id)
            except (Exam.DoesNotExist, ValueError, TypeError):
                return Response({'error': f'No exam found with id {pyq_exam_id} for pyq_exam_id.'}, status=status.HTTP_404_NOT_FOUND)

        # ---- options ----
        filled_options = [o for o in raw_options if isinstance(o, dict) and (o.get('text') or '').strip()]
        if len(filled_options) < 2:
            return Response({'errors': {'options': 'At least 2 options need text.'}}, status=status.HTTP_400_BAD_REQUEST)
        if len(filled_options) > len(self.OPTION_LETTERS):
            return Response(
                {'errors': {'options': f'A maximum of {len(self.OPTION_LETTERS)} options is allowed.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Map each option's frontend id -> a letter (A, B, C...) in stable
        # order, since QuestionOption stores plain option_a..option_f
        # columns and CorrectAnswer stores the *letter*, not the frontend id.
        id_to_letter = {}
        letter_to_text = {}
        for index, option in enumerate(filled_options):
            letter = self.OPTION_LETTERS[index]
            id_to_letter[str(option.get('id'))] = letter
            letter_to_text[letter] = (option.get('text') or '').strip()

        correct_letter = id_to_letter.get(str(correct_answer_id))
        if not correct_letter:
            return Response(
                {'errors': {'correct_answer': 'correct_answer must reference one of the submitted options.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- optional question image ----
        image_data = {}
        image_file = request.FILES.get('image')
        if image_file:
            saved_path = default_storage.save(f'questions/{image_file.name}', image_file)
            image_data = {'images': [default_storage.url(saved_path)]}

        question = Question.objects.create(
            exam=exam,
            chapter=chapter,
            question_text=question_text,
            question_type=question_type,
            marks=correct_marks,
            negative_marks=negative_marks,
            image_url=image_data,
            difficulty_level=difficulty,
            is_previousyear=is_pyq,
            pyq_exam=pyq_exam,
            pyq_year=pyq_year_int,
            pyq_session=pyq_session or None,
            is_active=True,
        )

        QuestionOption.objects.create(
            question=question,
            option_a=letter_to_text.get('A', ''),
            option_b=letter_to_text.get('B', ''),
            option_c=letter_to_text.get('C', ''),
            option_d=letter_to_text.get('D', ''),
            option_e=letter_to_text.get('E'),
        )

        CorrectAnswer.objects.create(
            question=question,
            option_id=correct_letter,
        )

        if explanation:
            Solution.objects.create(
                question=question,
                user=request.user if request.user.is_authenticated else None,
                explaination_text=explanation,
                hints='',
            )

        # Audit log only — Question has no `mapped_from` FK today. If this
        # lineage needs to be queryable later, add a nullable
        # `mapped_from = models.ForeignKey('self', null=True, blank=True,
        # on_delete=models.SET_NULL, related_name='mapped_children')`
        # field on Question and set it here instead of just logging.
        if mapped_from_question_id:
            logger.info(
                "Question %s created as a mapped duplicate of question %s "
                "(admin confirmed 'Map for Another Exam').",
                question.question_id, mapped_from_question_id,
            )

        serializer = QuestionSerializer(question, context={'mode': 'practice'})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class QuestionListView(APIView):
    """
    GET /api/questions/
    Params:
        chapter_id    — fetch by chapter (chapter-wise)
        subject_id    — fetch by subject (complete syllabus)
        mode          — 'test' | 'practice' (affects whether answers/explanations are hidden)
        scope         — 'full' signals complete syllabus (used with subject_id)
        count_only    — if 'true', return only { count } without questions

        # Admin Question Bank mode (no chapter_id/subject_id required):
        admin         — 'true' enables admin listing mode
        search        — icontains on question_text
        difficulty    — easy | medium | hard
        question_type — single_correct | multiple_correct | integer | etc.
        exam_id       — filter by exam
        page          — page number (default 1)
        page_size     — results per page (default 20, max 100)

    CHANGED: subject_id filtering now goes through `chapter__subject_id`
    since Question has no direct `subject` FK. Both branches now also
    require `is_active=True`.
    """

    def get(self, request):
        chapter_id = request.query_params.get('chapter_id', '').strip()
        subject_id = request.query_params.get('subject_id', '').strip()
        mode       = request.query_params.get('mode', 'test').strip().lower()
        scope      = request.query_params.get('scope', '').strip().lower()
        count_only = request.query_params.get('count_only', 'false').strip().lower() == 'true'
        is_admin   = request.query_params.get('admin', 'false').strip().lower() == 'true'

        # ── Admin Question Bank branch ─────────────────────────────────────
        # Activated by passing ?admin=true. No chapter_id/subject_id needed.
        # Returns paginated list with lightweight per-row data (no options/
        # solutions loaded) suitable for the admin table.
        #
        # GROUPING: the same question text is legitimately re-added under
        # multiple exams (see AddQuestionView's duplicate-mapping flow), so
        # naive per-row listing shows the same question several times. This
        # branch groups rows by normalized question_text and returns one
        # entry per group, with a `mapped_exams` list describing every exam
        # it's filed under. Grouping happens in Python (not SQL) because it
        # needs to run before pagination — the DB can't paginate "distinct
        # normalized text" cheaply without a generated/indexed column, and
        # question-bank sizes here are small enough for this to be fine.
        if is_admin:
            qs = (
                Question.objects
                .filter(is_active=True)
                .select_related('chapter__subject', 'exam', 'pyq_exam')
                .order_by('-created_at')
            )

            # Optional filters
            search = request.query_params.get('search', '').strip()
            if search:
                qs = qs.filter(question_text__icontains=search)

            if subject_id:
                qs = qs.filter(
                    Q(chapter__subject_id=subject_id) |
                    Q(chapter_mappings__chapter__subject_id=subject_id)
                ).distinct()

            if chapter_id:
                qs = qs.filter(
                    Q(chapter_id=chapter_id) |
                    Q(chapter_mappings__chapter_id=chapter_id)
                ).distinct()

            difficulty = request.query_params.get('difficulty', '').strip()
            if difficulty:
                qs = qs.filter(difficulty_level__iexact=difficulty)

            question_type = request.query_params.get('question_type', '').strip()
            if question_type:
                qs = qs.filter(question_type__iexact=question_type)

            exam_id = request.query_params.get('exam_id', '').strip()
            if exam_id:
                qs = qs.filter(exam_id=exam_id)

            # ---- group by normalized question_text ----
            groups = {}   # normalized_text -> list[Question], insertion-ordered
            for q in qs:
                key = ' '.join((q.question_text or '').split()).lower()
                groups.setdefault(key, []).append(q)

            def exam_label(q):
                exam = q.exam or q.pyq_exam
                return exam.exam_name if exam else None

            grouped_rows = []
            for rows in groups.values():
                # Representative row = the earliest-created (original) one,
                # since that's the "canonical" version for edit/delete
                # actions — later ones are just the same question mapped
                # onto other exams.
                rows_sorted = sorted(rows, key=lambda r: r.question_id)
                primary = rows_sorted[0]

                subject_name = None
                chapter_name = None
                if primary.chapter_id:
                    chapter_name = primary.chapter.chapter_name if primary.chapter else None
                    if primary.chapter and primary.chapter.subject_id:
                        subject_name = primary.chapter.subject.subject_name if primary.chapter.subject else None

                mapped_exams = [
                    {
                        'question_id': r.question_id,
                        'exam_name': exam_label(r),
                        'year': r.pyq_year,
                        'session': r.pyq_session,
                    }
                    for r in rows_sorted
                ]

                grouped_rows.append({
                    'question_id':      primary.question_id,
                    'question_text':    primary.question_text,
                    'question_type':    primary.question_type,
                    'difficulty_level': primary.difficulty_level,
                    'subject_name':     subject_name,
                    'chapter_name':     chapter_name,
                    'marks':            primary.marks,
                    'created_at':       primary.created_at,
                    'mapped_exams':     mapped_exams,
                    'mapped_count':     len(mapped_exams),
                    # every question_id in this group — the frontend needs
                    # this so "delete" / bulk-select can act on the whole
                    # group rather than silently leaving orphaned mappings.
                    'all_question_ids': [r.question_id for r in rows_sorted],
                    '_max_created_at':  max(r.created_at for r in rows_sorted),
                })

            # Newest group first, keyed off the most-recently-created row
            # in each group (not just the primary), so a fresh mapping
            # bumps its group back to the top like a normal "recently
            # added" list would.
            grouped_rows.sort(key=lambda g: g.pop('_max_created_at'), reverse=True)

            # Pagination (over groups, not raw rows)
            try:
                page = max(1, int(request.query_params.get('page', 1)))
            except (ValueError, TypeError):
                page = 1
            try:
                page_size = min(int(request.query_params.get('page_size', 20)), 100)
            except (ValueError, TypeError):
                page_size = 20

            paginator = Paginator(grouped_rows, page_size)
            page_obj  = paginator.get_page(page)

            return Response({
                'count':       paginator.count,
                'total_pages': paginator.num_pages,
                'page':        page,
                'page_size':   page_size,
                'results':     list(page_obj.object_list),
            })


        # ── Student / test-taking branch (existing behaviour unchanged) ────
        if not chapter_id and not subject_id:
            return Response(
                {'error': 'chapter_id or subject_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if subject_id and scope == 'full':
            qs = (
                Question.objects
                .filter(
                    Q(chapter__subject_id=subject_id) |
                    Q(chapter_mappings__chapter__subject_id=subject_id),
                    is_active=True
                )
                .exclude(chapter__chapter_name__iexact=IMPORTED_CHAPTER_NAME)   # mock-test-only bucket
                .distinct()
                .select_related('chapter__subject')
                .prefetch_related('questionoption_set', 'solution_set', 'correctanswer_set')
                .order_by('?')
            )
        elif chapter_id:
            qs = (
                Question.objects
                .filter(
                    Q(chapter_id=chapter_id) |
                    Q(chapter_mappings__chapter_id=chapter_id),
                    is_active=True
                )
                .distinct()
                .select_related('chapter__subject')
                .prefetch_related('questionoption_set', 'solution_set', 'correctanswer_set')
                .order_by('?')
            )
        else:
            return Response(
                {'error': 'Provide chapter_id for chapter-wise or subject_id + scope=full for complete syllabus.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if count_only:
            return Response({'count': qs.count()})

        serializer = QuestionSerializer(qs, many=True, context={'mode': mode})
        return Response({
            'mode':  mode,
            'scope': scope or 'chapter',
            'count': len(serializer.data),
            'questions': serializer.data,
        })

    def delete(self, request):
        """
        DELETE /api/questions/?admin=true&id=<question_id>
        Soft-deletes a question (sets is_active=False).
        """
        if request.query_params.get('admin', '').lower() != 'true':
            return Response({'error': 'admin=true is required.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = request.query_params.get('id', '').strip()
        if not question_id:
            return Response({'error': 'id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            q = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

        q.is_active = False
        q.save(update_fields=['is_active'])
        return Response({'deleted': question_id}, status=status.HTTP_200_OK)



@method_decorator(csrf_exempt, name='dispatch')
class SubmitAnswersView(APIView):
    """
    POST /api/questions/submit/
    Body: {
        "answers":          { "<question_id>": "A"|"B"|"C"|"D" },
        "all_question_ids": ["<id>", ...]   # every question in the test
    }
 
    KEY FIXES vs old version:
    - Queries ALL questions (answered + unattempted) using all_question_ids,
      not just answered ones, so the result screen shows correct_answer and
      solution for EVERY question including skipped ones.
    - Uses +4 / -1 marking scheme (JEE standard); was incorrectly +1/0.
    - Handles empty answers dict gracefully (no longer returns 400).
    - Returns subject_name per question for frontend grouping.
    - csrf_exempt + AllowAny: this is a same-origin JSON POST from a plain
      fetch() with no CSRF token attached. With Django's default
      SessionAuthentication that POST was being rejected with 403 before
      ever reaching this method — the frontend's catch block then silently
      fell back to its zeroed-out/empty result state, which is what
      rendered every question as "Unattempted" with no correct answer or
      solution even though the scoring logic below was already correct.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            answers       = request.data.get('answers', {}) or {}           # may be {}
            all_ids_param = request.data.get('all_question_ids', []) or []  # every qid
        except Exception:
            return Response(
                {'error': 'Malformed request body — expected JSON with "answers" and "all_question_ids".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(answers, dict):
            return Response(
                {'error': '"answers" must be an object of { question_id: option_key }.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use all_question_ids when provided; fall back to answered ids only
        all_ids = [str(i) for i in all_ids_param] if all_ids_param else list(answers.keys())
 
        if not all_ids:
            return Response(
                {'error': 'No question IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        questions = (
            Question.objects
            .filter(question_id__in=all_ids)
            .select_related('chapter__subject')
            .prefetch_related('correctanswer_set', 'solution_set')
        )
 
        results       = []
        raw_score     = 0
        correct_count = 0
        wrong_count   = 0
 
        for q in questions:
            user_answer = answers.get(str(q.question_id), '').strip().upper()
            ca          = q.correctanswer_set.first()
            correct     = ca.option_id.strip().upper() if ca else ''
            is_correct  = bool(user_answer and user_answer == correct)
 
            # +4 for correct, -1 for wrong, 0 for unattempted (JEE standard)
            if is_correct:
                raw_score     += 4
                correct_count += 1
            elif user_answer:
                raw_score  -= 1
                wrong_count += 1
 
            sol = q.solution_set.first()
 
            # Resolve subject_name through chapter->subject chain safely
            subject_name = ''
            try:
                if q.chapter_id and q.chapter and q.chapter.subject_id:
                    subject_name = q.chapter.subject.subject_name or ''
            except Exception:
                subject_name = ''
 
            results.append({
                'question_id':    q.question_id,
                'question_text':  q.question_text,
                'subject_name':   subject_name,
                'your_answer':    user_answer,       # '' means unattempted
                'correct_answer': correct,
                'is_correct':     is_correct,
                'explanation':    (sol.explaination_text or '') if sol else '',
                'hints':          (sol.hints or '') if sol else '',
            })
 
        total     = len(questions)
        attempted = correct_count + wrong_count
        score     = max(0, raw_score)
 
        return Response({
            'score':      score,
            'max_score':  total * 4,
            'total':      total,
            'correct':    correct_count,
            'wrong':      wrong_count,
            'skipped':    total - attempted,
            'attempted':  attempted,
            'percentage': round((correct_count / total) * 100, 1) if total else 0,
            'results':    results,
        })

# ─────────────────────────────────────────────────────────────
# ADMIN DASHBOARD — mirrors src/data/adminDummyData.ts exactly so the
# Vue components (StatsCard, RecentExamsTable, ExamDistributionChart,
# ExamTrendChart, TestActivityTable) need zero shape changes when
# switching from the dummy import to these live endpoints.
# ─────────────────────────────────────────────────────────────
 
class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/
    Mirrors `statsData` — a fixed-order list of 6 stat cards.
    """
    permission_classes = [IsAdminUser]
 
    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        exams = Exam.objects.all()
        tests = TestDefinition.objects.all()
        questions = Question.objects.all()
 
        def stat(label, qs, icon, color):
            return {
                'label': label,
                'value': qs.count(),
                'trend': f"+{qs.filter(created_at__gte=week_ago).count()} this week",
                'icon': icon,
                'color': color,
            }
 
        data = [
            stat('Total Exams',     exams,                          'graduation', '#7C3AED'),
            stat('Published Exams', exams.filter(is_active=True),   'file-check', '#2563EB'),
            stat('Draft Exams',     exams.filter(is_active=False),  'pencil',     '#D97706'),
            stat('Trending Exams',  exams.filter(is_trending=True), 'clock',      '#7C3AED'),
            stat('Total Tests',     tests,                          'book',       '#059669'),
            stat('Total Questions', questions,                       'question',   '#DC2626'),
        ]
        return Response(data)
 
 
class RecentExamsView(APIView):
    """
    GET /api/dashboard/recent-exams/?limit=5
    Mirrors `recentExams` — { name, type, category, status, updatedOn }.
    """
    permission_classes = [IsAdminUser]
 
    def get(self, request):
        limit_param = request.query_params.get('limit', '5').strip()
        limit = int(limit_param) if limit_param.isdigit() else 5
 
        exams = (
            Exam.objects
            .select_related('exam_type')
            .order_by('-updated_at')[:limit]
        )
        from .serializers import resolve_category_name
        data = [{
            'name':      e.exam_name,
            'type':      e.exam_type.type_name if e.exam_type else '',
            'category':  resolve_category_name(e) or '',
            'status':    'Published' if e.is_active else 'Draft',
            'updatedOn': e.updated_at.strftime('%d %b %Y') if e.updated_at else '',
        } for e in exams]
        return Response(data)
 
 
class ExamDistributionView(APIView):
    """
    GET /api/dashboard/exam-distribution/
    Mirrors `examDistribution` — { label, count, percent, color }.
    """
    permission_classes = [IsAdminUser]
 
    COLORS = {
        'entrance': '#7C3AED',
        'job': '#3B82F6',
        'school': '#10B981',
    }
 
    def get(self, request):
        total = Exam.objects.count() or 1
        rows = (
            Exam.objects
            .values('exam_type__type_name')
            .annotate(count=Count('exam_id'))
            .order_by('-count')
        )
        data = []
        for r in rows:
            type_name = r['exam_type__type_name'] or 'Unknown'
            data.append({
                'label': f"{type_name} Exams",
                'count': r['count'],
                'percent': round(r['count'] / total * 100, 1),
                'color': self.COLORS.get(type_name.strip().lower(), '#999999'),
            })
        return Response(data)
 
 
class ExamTrendView(APIView):
    """
    GET /api/dashboard/exam-trend/?days=7
    Mirrors `examTrend` — { date, count }, one entry per day (including
    zero-count days) over the requested window.
    """
    permission_classes = [IsAdminUser]
 
    def get(self, request):
        days_param = request.query_params.get('days', '7').strip()
        days = int(days_param) if days_param.isdigit() else 7
 
        since = (timezone.now() - timedelta(days=days - 1)).date()
        rows = (
            Exam.objects
            .filter(created_at__date__gte=since)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('exam_id'))
            .order_by('day')
        )
        counts_by_day = {r['day']: r['count'] for r in rows}
 
        data = []
        for i in range(days):
            day = since + timedelta(days=i)
            data.append({
                'date': day.strftime('%b %d'),
                'count': counts_by_day.get(day, 0),
            })
        return Response(data)
 
 
class RecentTestActivityView(generics.ListAPIView):
    """
    GET /api/dashboard/recent-tests/?limit=5
    Mirrors `recentTestActivity` — { name, exam, type, questions,
    duration, status, updatedOn }.
    """
    permission_classes = [IsAdminUser]
    serializer_class = TestDefinitionSerializer
    pagination_class = None
 
    def get_queryset(self):
        limit_param = self.request.query_params.get('limit', '5').strip()
        limit = int(limit_param) if limit_param.isdigit() else 5
        return (
            TestDefinition.objects
            .select_related('exam')
            .annotate(questions=Count('exam__question', distinct=True))
            .order_by('-created_at')[:limit]
        )


"""
bulk_upload_views.py
────────────────────
Drop-in additions for views.py.

Endpoints
─────────
POST /api/mockexams/<mockexam_id>/bulk-upload/validate/
    Upload an .xlsx / .xls / .csv file.
    Returns a validation report with valid / invalid / duplicate rows
    and an upload_id to pass to the import step.

POST /api/mockexams/<mockexam_id>/bulk-upload/import/
    Body: { "upload_id": "<uuid>" }
    Imports only the valid rows from the earlier validation into the DB
    as Question / QuestionOption / CorrectAnswer rows tied to the
    given MockExam.

GET  /api/bulk-upload/template/
    Returns the Excel template the user is asked to fill.

Paste this entire file's contents into views.py (anywhere after the
existing imports block), then add the three paths to urls.py:
    path('mockexams/<int:mockexam_id>/bulk-upload/validate/', BulkUploadValidateView.as_view()),
    path('mockexams/<int:mockexam_id>/bulk-upload/import/',   BulkUploadImportView.as_view()),
    path('bulk-upload/template/', BulkUploadTemplateView.as_view()),
"""

import io
import uuid
import re
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import MockExam, Question, QuestionOption, CorrectAnswer, Chapter, Subject

# NOTE: openpyxl and pandas are imported lazily inside the functions that
# need them (not at module level). This means a missing package will NOT
# crash the entire Django process at startup — every other endpoint keeps
# working and only the bulk-upload endpoints return a clear error.
#
# Make sure these are in your requirements.txt / Dockerfile:
#   openpyxl>=3.1
#   pandas>=2.0
#   xlrd>=2.0     ← only needed for legacy .xls files

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

# Cache key prefix and TTL (10 minutes — enough to cover the
# validate → preview → import round-trip in normal usage).
UPLOAD_CACHE_PREFIX = "bulk_upload_"
UPLOAD_CACHE_TTL = 600  # seconds

# Required columns (case-insensitive, stripped).
REQUIRED_COLUMNS = {
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",  # A / B / C / D (or A,C for MSQ)
}

# Optional columns and their defaults.
OPTIONAL_COLUMNS = {
    "subject":       "",
    "chapter":       "",
    "question_type": "MCQ",
    "difficulty":    "Medium",
    "marks":         4,
    "negative_marks": 1,
    "option_e":      "",
    "explanation":   "",
    "hint":          "",
}

ALLOWED_CORRECT = {"A", "B", "C", "D", "E", "A,B", "A,C", "A,D", "B,C", "B,D", "C,D",
                   "A,B,C", "A,B,D", "A,C,D", "B,C,D", "A,B,C,D"}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _read_file(file_obj):
    """
    Parse an uploaded file (.xlsx / .xls / .csv) into a pandas DataFrame.
    Raises ValueError with a user-friendly message on failure.
    Imports pandas lazily so a missing package only breaks this function,
    not the whole Django startup.
    """
    try:
        import pandas as pd  # lazy import
    except ImportError:
        raise ValueError(
            "pandas is not installed. Add 'pandas>=2.0' to requirements.txt "
            "and rebuild the Docker image."
        )

    name = getattr(file_obj, 'name', '').lower()

    try:
        if name.endswith('.csv'):
            df = pd.read_csv(file_obj, dtype=str, keep_default_na=False)
        elif name.endswith('.xls'):
            df = pd.read_excel(file_obj, engine='xlrd', dtype=str, keep_default_na=False)
        else:  # .xlsx (default)
            df = pd.read_excel(file_obj, engine='openpyxl', dtype=str, keep_default_na=False)
    except ImportError as exc:
        # openpyxl / xlrd missing
        raise ValueError(
            f"A required library is not installed: {exc}. "
            "Add 'openpyxl>=3.1' (and 'xlrd>=2.0' for .xls) to requirements.txt."
        ) from exc
    except Exception as exc:
        raise ValueError(f"Could not read the file: {exc}") from exc

    # Normalise column names: lower-case, strip spaces, replace spaces with _.
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    return df


def _validate_row(row: dict, row_num: int, seen_texts: set) -> tuple[dict | None, str | None]:
    """
    Validate a single row dict (column → value, already normalised).

    Returns (cleaned_row, None) on success.
    Returns (None, reason_string) on failure.
    """
    # ── Check required fields ──────────────────────────────────
    for col in REQUIRED_COLUMNS:
        val = str(row.get(col, '')).strip()
        if not val:
            return None, f"Row {row_num}: missing required field '{col}'"

    question_text = str(row['question_text']).strip()
    correct_raw   = str(row['correct_answer']).strip().upper().replace(' ', '')

    # ── Correct answer must be one of the allowed patterns ─────
    if correct_raw not in ALLOWED_CORRECT:
        return None, (
            f"Row {row_num}: invalid correct_answer '{correct_raw}'. "
            f"Must be one of A / B / C / D or a comma-separated combo."
        )

    # ── Duplicate detection (within this upload) ───────────────
    text_key = question_text.lower()
    if text_key in seen_texts:
        return None, f"Row {row_num}: duplicate question text (already seen in this file)"
    seen_texts.add(text_key)

    # ── Build cleaned row ─────────────────────────────────────
    cleaned = {
        'text':          question_text,
        'option_a':      str(row.get('option_a', '')).strip(),
        'option_b':      str(row.get('option_b', '')).strip(),
        'option_c':      str(row.get('option_c', '')).strip(),
        'option_d':      str(row.get('option_d', '')).strip(),
        'option_e':      str(row.get('option_e', '')).strip(),
        'correct_answer': correct_raw,
        'subject':       str(row.get('subject', '')).strip(),
        'chapter':       str(row.get('chapter', '')).strip(),
        'question_type': str(row.get('question_type', 'MCQ')).strip() or 'MCQ',
        'difficulty':    str(row.get('difficulty', 'Medium')).strip() or 'Medium',
        'marks':         _safe_decimal(row.get('marks', 4), 4),
        'negative_marks': _safe_decimal(row.get('negative_marks', 1), 1),
        'explanation':   str(row.get('explanation', '')).strip(),
        'hint':          str(row.get('hint', '')).strip(),
    }
    return cleaned, None


def _safe_decimal(value, default):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return float(default)


def _row_to_preview(cleaned: dict, idx: int) -> dict:
    """Shape a cleaned row for the frontend preview table."""
    return {
        'id':         idx,
        'text':       cleaned['text'],
        'subject':    cleaned['subject'] or '—',
        'chapter':    cleaned['chapter'] or '—',
        'type':       cleaned['question_type'],
        'difficulty': cleaned['difficulty'],
        'marks':      cleaned['marks'],
    }


def _invalid_row_to_preview(raw: dict, reason: str, idx: int) -> dict:
    return {
        'id':         idx,
        'text':       str(raw.get('question_text', '')).strip() or '(empty)',
        'subject':    str(raw.get('subject', '')).strip() or '—',
        'chapter':    str(raw.get('chapter', '')).strip() or '—',
        'type':       str(raw.get('question_type', 'MCQ')).strip() or 'MCQ',
        'difficulty': str(raw.get('difficulty', '')).strip() or '—',
        'marks':      _safe_decimal(raw.get('marks', 4), 4),
        'reason':     reason,
    }


# ─────────────────────────────────────────────────────────────
# View 1 — Validate
# ─────────────────────────────────────────────────────────────

class BulkUploadValidateView(APIView):
    """
    POST /api/mockexams/<mockexam_id>/bulk-upload/validate/

    Multipart body:
        file   (required) – the .xlsx / .xls / .csv upload

    Response (200):
    {
        "upload_id":      "<uuid>",
        "totalRows":      42,
        "validRows":      [...],      ← preview-shaped rows
        "invalidRows":    [...],
        "duplicateRows":  [...],
    }

    The upload_id is a short-lived cache key (10 min) that references
    the cleaned valid rows so the import step doesn't have to re-parse
    the file.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, mockexam_id):
        # ── 1. Verify mock exam exists ────────────────────────
        try:
            MockExam.objects.get(pk=mockexam_id)
        except MockExam.DoesNotExist:
            return Response(
                {'error': f'No mock exam found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── 2. Get uploaded file ──────────────────────────────
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file provided. Send the file under the key "file".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file_obj.size > MAX_FILE_SIZE_BYTES:
            return Response(
                {'error': 'File exceeds the 10 MB limit.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = file_obj.name.lower()
        if not any(filename.endswith(ext) for ext in ('.xlsx', '.xls', '.csv')):
            return Response(
                {'error': 'Unsupported file type. Please upload .xlsx, .xls, or .csv.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 3. Parse the file ─────────────────────────────────
        try:
            df = _read_file(file_obj)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if df.empty:
            return Response(
                {'error': 'The uploaded file is empty.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 4. Check required columns are present ─────────────
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            return Response(
                {
                    'error': 'Missing required column(s).',
                    'missing_columns': sorted(missing),
                    'hint': (
                        'Download the template from the Guidelines panel to '
                        'see the exact header names required.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 5. Validate each row ──────────────────────────────
        seen_texts: set[str] = set()
        valid_rows_cleaned = []
        invalid_preview    = []
        duplicate_preview  = []

        for i, (_, row) in enumerate(df.iterrows(), start=2):  # row 1 = header
            raw = row.to_dict()
            cleaned, reason = _validate_row(raw, i, seen_texts)

            if cleaned is None:
                if 'duplicate' in (reason or '').lower():
                    duplicate_preview.append(_invalid_row_to_preview(raw, reason, i))
                else:
                    invalid_preview.append(_invalid_row_to_preview(raw, reason, i))
            else:
                valid_rows_cleaned.append(cleaned)

        # ── 6. Cross-check DB duplicates ──────────────────────
        # A question whose text already exists in the DB for this mock
        # exam is treated as a duplicate (not invalid).
        existing_texts = set(
            Question.objects
            .filter(mock_exam_id=mockexam_id)
            .values_list('question_text', flat=True)
        )
        final_valid = []
        for cleaned in valid_rows_cleaned:
            if cleaned['text'].lower() in {t.lower() for t in existing_texts}:
                # Move from valid to duplicate
                duplicate_preview.append({
                    'id':         len(duplicate_preview),
                    'text':       cleaned['text'],
                    'subject':    cleaned['subject'] or '—',
                    'chapter':    cleaned['chapter'] or '—',
                    'type':       cleaned['question_type'],
                    'difficulty': cleaned['difficulty'],
                    'marks':      cleaned['marks'],
                    'reason':     'Question already exists in this mock test.',
                })
            else:
                final_valid.append(cleaned)

        # ── 7. Store valid rows in cache ──────────────────────
        upload_id = str(uuid.uuid4())
        cache.set(
            f"{UPLOAD_CACHE_PREFIX}{upload_id}",
            {
                'mockexam_id': mockexam_id,
                'valid_rows':  final_valid,
            },
            timeout=UPLOAD_CACHE_TTL,
        )

        return Response({
            'upload_id':      upload_id,
            'totalRows':      len(df),
            'validRows':      [_row_to_preview(r, i) for i, r in enumerate(final_valid)],
            'invalidRows':    invalid_preview,
            'duplicateRows':  duplicate_preview,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# View 2 — Import
# ─────────────────────────────────────────────────────────────

class BulkUploadImportView(APIView):
    """
    POST /api/mockexams/<mockexam_id>/bulk-upload/import/

    JSON body:
        { "upload_id": "<uuid-from-validate-step>" }

    Response (200):
        { "imported": 38, "skipped": 0 }

    Creates one Question + QuestionOption + CorrectAnswer per valid row.
    Subject / Chapter resolution:
        - If the row includes a subject name, we look for (or create)
          a Subject under the mock exam's parent Exam with that name.
        - If it also includes a chapter name, we look for (or create)
          a Chapter under that Subject.
        - If neither is given, question.chapter is left null.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, mockexam_id):
        # ── 1. Verify mock exam ───────────────────────────────
        try:
            mock_exam = MockExam.objects.select_related('exam').get(pk=mockexam_id)
        except MockExam.DoesNotExist:
            return Response(
                {'error': f'No mock exam found with id {mockexam_id}.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── 2. Retrieve cached upload ─────────────────────────
        upload_id = (request.data.get('upload_id') or '').strip()
        if not upload_id:
            return Response(
                {'error': '"upload_id" is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f"{UPLOAD_CACHE_PREFIX}{upload_id}"
        cached = cache.get(cache_key)
        if not cached:
            return Response(
                {
                    'error': (
                        'Upload session has expired or was not found. '
                        'Please re-upload and validate your file.'
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if cached['mockexam_id'] != mockexam_id:
            return Response(
                {'error': 'upload_id does not belong to this mock exam.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        valid_rows = cached['valid_rows']
        if not valid_rows:
            return Response({'imported': 0, 'skipped': 0})

        # ── 3. Import rows ────────────────────────────────────
        exam = mock_exam.exam

        # Local caches to avoid repeated DB hits for the same
        # subject/chapter names within a single import batch.
        subject_cache: dict[str, Subject]  = {}
        chapter_cache: dict[tuple, Chapter] = {}

        questions_to_create = []
        options_to_create   = []
        answers_to_create   = []

        # We bulk-create Questions first (no pk yet), then Options/Answers.
        # Django's bulk_create returns the objects with pks on most DBs
        # (PostgreSQL/MySQL ≥ 8 / SQLite ≥ 3.35), so we use that.

        for row in valid_rows:
            subject_name = row['subject']
            chapter_name = row['chapter']

            chapter = None

            if subject_name:
                if subject_name not in subject_cache:
                    subj, _ = Subject.objects.get_or_create(
                        exam=exam,
                        subject_name=subject_name,
                    )
                    subject_cache[subject_name] = subj

                subject = subject_cache[subject_name]

                if chapter_name:
                    key = (subject.pk, chapter_name)
                    if key not in chapter_cache:
                        ch, _ = Chapter.objects.get_or_create(
                            subject=subject,
                            chapter_name=chapter_name,
                            defaults={'is_active': True},
                        )
                        chapter_cache[key] = ch
                    chapter = chapter_cache[key]

            questions_to_create.append(
                Question(
                    exam=exam,
                    mock_exam=mock_exam,
                    chapter=chapter,
                    question_text=row['text'],
                    question_type=row['question_type'],
                    marks=row['marks'],
                    negative_marks=row['negative_marks'],
                    difficulty_level=row['difficulty'],
                    hint=row['hint'] or None,
                    is_active=True,
                )
            )

        created_questions = Question.objects.bulk_create(questions_to_create)

        for q, row in zip(created_questions, valid_rows):
            options_to_create.append(
                QuestionOption(
                    question=q,
                    option_a=row['option_a'],
                    option_b=row['option_b'],
                    option_c=row['option_c'],
                    option_d=row['option_d'],
                    option_e=row['option_e'] or '',
                )
            )
            answers_to_create.append(
                CorrectAnswer(
                    question=q,
                    option_id=row['correct_answer'],
                )
            )

        QuestionOption.objects.bulk_create(options_to_create)
        CorrectAnswer.objects.bulk_create(answers_to_create)

        # ── 4. Invalidate cache entry ─────────────────────────
        cache.delete(cache_key)

        return Response({
            'imported': len(created_questions),
            'skipped':  0,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# View 3 — Download Template
# ─────────────────────────────────────────────────────────────

class BulkUploadTemplateView(APIView):
    """
    GET /api/bulk-upload/template/

    Returns a pre-filled .xlsx template the admin can fill and upload.
    The first row is column headers; the second row is a sample question
    so the user can see the expected format immediately.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            import openpyxl  # lazy import
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            return Response(
                {
                    'error': (
                        "openpyxl is not installed on the server. "
                        "Add 'openpyxl>=3.1' to requirements.txt and rebuild the Docker image."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Questions"

        headers = [
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "option_e",
            "correct_answer",
            "subject",
            "chapter",
            "question_type",
            "difficulty",
            "marks",
            "negative_marks",
            "explanation",
            "hint",
        ]

        # Style the header row
        header_font  = Font(bold=True, color="FFFFFF")
        header_fill  = PatternFill("solid", fgColor="6C4BF4")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.append(headers)
        for cell in ws[1]:
            cell.font      = header_font
            cell.fill      = header_fill
            cell.alignment = header_align

        # Sample row
        sample = [
            "If a = 2 + √3 and b = 2 − √3, then a² + b² equals:",
            "12",
            "14",
            "16",
            "18",
            "",           # option_e (optional)
            "B",          # correct_answer
            "Mathematics",
            "Quadratic Equations",
            "MCQ",
            "Medium",
            "4",
            "1",
            "Using (a+b)²=a²+2ab+b², we get a²+b²=14.",
            "Try expanding (a+b)² first.",
        ]
        ws.append(sample)

        # Auto-size columns (rough heuristic: max char length + padding)
        for col_cells in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 50)

        # Freeze the header row
        ws.freeze_panes = "A2"

        # Add a "Required columns" note in a separate sheet
        info_ws = wb.create_sheet("README")
        info_ws.append(["Column", "Required?", "Allowed Values / Notes"])
        notes = [
            ("question_text",  "YES", "The full question text. No duplicates allowed."),
            ("option_a",       "YES", "Text for option A."),
            ("option_b",       "YES", "Text for option B."),
            ("option_c",       "YES", "Text for option C."),
            ("option_d",       "YES", "Text for option D."),
            ("option_e",       "no",  "Optional fifth option."),
            ("correct_answer", "YES", "A / B / C / D / E or comma-separated like A,C"),
            ("subject",        "no",  "Subject name. Created automatically if new."),
            ("chapter",        "no",  "Chapter name. Created automatically if new."),
            ("question_type",  "no",  "MCQ (default) / MSQ / Numeric"),
            ("difficulty",     "no",  "Easy / Medium (default) / Hard"),
            ("marks",          "no",  "Numeric. Default: 4"),
            ("negative_marks", "no",  "Numeric. Default: 1"),
            ("explanation",    "no",  "Solution explanation text."),
            ("hint",           "no",  "Hint text shown during practice."),
        ]
        for row in notes:
            info_ws.append(row)
        for col_cells in info_ws.columns:
            max_len = max(len(str(c.value or '')) for c in col_cells)
            info_ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 60)

        # Serialize and return
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        resp = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        resp['Content-Disposition'] = 'attachment; filename="bulk_upload_template.xlsx"'
        return resp


# ─────────────────────────────────────────────────────────────────
# QUESTION BANK bulk upload — completely separate from the mock-exam
# bulk upload above (BulkUploadValidateView / BulkUploadImportView).
#
# Why separate:
#   - Mock exam import requires a mockexam_id and always sets
#     Question.mock_exam to that exam. Question Bank questions have
#     mock_exam = None and are keyed by exam_id instead.
#   - Question Bank uses a different question_type / difficulty
#     vocabulary than the mock-exam file format
#     (single_correct/multiple_correct/integer/subjective, lowercase
#     difficulty) — see AddQuestionView above for the canonical values.
#   - Duplicate-detection must exclude mock-exam questions: a question
#     bank question should only be flagged as a duplicate against other
#     question-bank questions for the same exam, not against every
#     question ever imported into a mock test for that exam.
#
# Reuses _read_file / _safe_decimal from the mock-exam section above
# (file parsing is format-agnostic) but does NOT reuse
# _validate_row/_row_to_preview, since those assume mock-exam's
# MCQ/Medium vocabulary.
# ─────────────────────────────────────────────────────────────────

QB_UPLOAD_CACHE_PREFIX = "qb_bulk_upload_"
QB_UPLOAD_CACHE_TTL = 600  # seconds

QB_REQUIRED_COLUMNS = {
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",
    "chapter",  # required here: Question Bank questions must belong to a chapter
}

QB_ALLOWED_CORRECT = ALLOWED_CORRECT  # same A/B/C/D(+combo) grammar

QB_TYPE_MAP = {
    "MCQ": "single_correct",
    "MSQ": "multiple_correct",
    "NUMERIC": "integer",
    "SUBJECTIVE": "subjective",
}
QB_DIFFICULTY_MAP = {"EASY": "easy", "MEDIUM": "medium", "HARD": "hard"}


def _qb_validate_row(row: dict, row_num: int, seen_texts: set) -> tuple[dict | None, str | None]:
    for col in QB_REQUIRED_COLUMNS:
        val = str(row.get(col, '')).strip()
        if not val:
            return None, f"Row {row_num}: missing required field '{col}'"

    question_text = str(row['question_text']).strip()
    correct_raw = str(row['correct_answer']).strip().upper().replace(' ', '')
    if correct_raw not in QB_ALLOWED_CORRECT:
        return None, (
            f"Row {row_num}: invalid correct_answer '{correct_raw}'. "
            f"Must be one of A / B / C / D or a comma-separated combo."
        )

    text_key = question_text.lower()
    if text_key in seen_texts:
        return None, f"Row {row_num}: duplicate question text (already seen in this file)"
    seen_texts.add(text_key)

    raw_type = str(row.get('question_type', 'MCQ')).strip().upper() or 'MCQ'
    question_type = QB_TYPE_MAP.get(raw_type)
    if question_type is None:
        return None, f"Row {row_num}: invalid question_type '{raw_type}'. Must be one of MCQ / MSQ / Numeric / Subjective."

    raw_difficulty = str(row.get('difficulty', 'Medium')).strip().upper() or 'MEDIUM'
    difficulty = QB_DIFFICULTY_MAP.get(raw_difficulty)
    if difficulty is None:
        return None, f"Row {row_num}: invalid difficulty '{raw_difficulty}'. Must be one of Easy / Medium / Hard."

    chapter_name = str(row.get('chapter', '')).strip()  # optional now; subject is what's validated
    subject_name = str(row.get('subject', '')).strip()

    cleaned = {
        'text':           question_text,
        'option_a':       str(row.get('option_a', '')).strip(),
        'option_b':       str(row.get('option_b', '')).strip(),
        'option_c':       str(row.get('option_c', '')).strip(),
        'option_d':       str(row.get('option_d', '')).strip(),
        'option_e':       str(row.get('option_e', '')).strip(),
        'correct_answer': correct_raw,
        'subject':        subject_name,
        'chapter':        chapter_name,
        'question_type':  question_type,
        'difficulty':     difficulty,
        'marks':          _safe_decimal(row.get('marks', 4), 4),
        'negative_marks': _safe_decimal(row.get('negative_marks', 1), 1),
        'explanation':    str(row.get('explanation', '')).strip(),
        'hint':           str(row.get('hint', '')).strip(),
    }
    return cleaned, None


def _qb_row_to_preview(cleaned: dict, idx: int) -> dict:
    return {
        'id':         idx,
        'text':       cleaned['text'],
        'subject':    cleaned['subject'] or '—',
        'chapter':    cleaned['chapter'] or '—',
        'type':       cleaned['question_type'],
        'difficulty': cleaned['difficulty'],
        'marks':      cleaned['marks'],
    }


def _qb_invalid_row_to_preview(raw: dict, reason: str, idx: int) -> dict:
    return {
        'id':         idx,
        'text':       str(raw.get('question_text', '')).strip() or '(empty)',
        'subject':    str(raw.get('subject', '')).strip() or '—',
        'chapter':    str(raw.get('chapter', '')).strip() or '—',
        'type':       str(raw.get('question_type', 'MCQ')).strip() or 'MCQ',
        'difficulty': str(raw.get('difficulty', '')).strip() or '—',
        'marks':      _safe_decimal(raw.get('marks', 4), 4),
        'reason':     reason,
    }


class QuestionBankBulkUploadValidateView(APIView):
    """
    POST /api/exams/<exam_id>/question-bank/bulk-upload/validate/

    Separate from the mock-exam bulk upload: keyed by exam_id (not
    mockexam_id), requires a 'subject' column per row (Question Bank
    questions are validated against Subject, not Chapter — there's no
    mock exam to fall back on), and created questions get mock_exam=None.
    An optional 'chapter' column may also be supplied; if present it is
    resolved/created under the matched subject but is never itself
    validated against existing chapters.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, exam_id):
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': f'No exam found with id {exam_id}.'}, status=status.HTTP_404_NOT_FOUND)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided. Send the file under the key "file".'}, status=status.HTTP_400_BAD_REQUEST)
        if file_obj.size > MAX_FILE_SIZE_BYTES:
            return Response({'error': 'File exceeds the 10 MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

        filename = file_obj.name.lower()
        if not any(filename.endswith(ext) for ext in ('.xlsx', '.xls', '.csv')):
            return Response({'error': 'Unsupported file type. Please upload .xlsx, .xls, or .csv.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = _read_file(file_obj)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if df.empty:
            return Response({'error': 'The uploaded file is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        missing = QB_REQUIRED_COLUMNS - set(df.columns)
        if missing:
            return Response({
                'error': 'Missing required column(s).',
                'missing_columns': sorted(missing),
                'hint': 'Download the Question Bank template — it requires a "subject" column, unlike the mock-test template.',
            }, status=status.HTTP_400_BAD_REQUEST)

        seen_texts: set[str] = set()
        valid_rows_cleaned = []
        invalid_preview = []
        duplicate_preview = []

        # Resolve subject names -> Subject rows under this exam up front.
        subject_lookup = {
            s.subject_name.strip().lower(): s
            for s in Subject.objects.filter(exam=exam)
        }
        # Local cache for optional chapter get_or_create, scoped per subject.
        chapter_cache: dict[tuple, Chapter] = {}

        for i, (_, row) in enumerate(df.iterrows(), start=2):
            raw = row.to_dict()
            cleaned, reason = _qb_validate_row(raw, i, seen_texts)

            if cleaned is None:
                target = duplicate_preview if 'duplicate' in (reason or '').lower() else invalid_preview
                target.append(_qb_invalid_row_to_preview(raw, reason, i))
                continue

            subject = subject_lookup.get(cleaned['subject'].strip().lower())
            if subject is None:
                invalid_preview.append(_qb_invalid_row_to_preview(
                    raw, f"Row {i}: subject '{cleaned['subject']}' does not exist under this exam.", i,
                ))
                continue

            chapter = None
            chapter_name = cleaned['chapter']
            if chapter_name:
                key = (subject.pk, chapter_name.strip().lower())
                if key not in chapter_cache:
                    ch, _ = Chapter.objects.get_or_create(
                        subject=subject,
                        chapter_name=chapter_name,
                        defaults={'is_active': True},
                    )
                    chapter_cache[key] = ch
                chapter = chapter_cache[key]

            cleaned['subject_id'] = subject.pk
            cleaned['chapter_id'] = chapter.pk if chapter else None
            valid_rows_cleaned.append(cleaned)

        # Cross-check against existing Question Bank questions for this exam
        # (mock_exam is null — mock-test-only questions don't count as dupes here).
        existing_texts = {
            t.lower() for t in Question.objects
            .filter(exam=exam, mock_exam__isnull=True)
            .values_list('question_text', flat=True)
        }
        final_valid = []
        duplicate_rows_cleaned = []  # full cleaned dicts, kept so "map them" can still import these
        for cleaned in valid_rows_cleaned:
            if cleaned['text'].lower() in existing_texts:
                duplicate_preview.append({
                    'id':         len(duplicate_preview),
                    'text':       cleaned['text'],
                    'subject':    cleaned['subject'] or '—',
                    'chapter':    cleaned['chapter'] or '—',
                    'type':       cleaned['question_type'],
                    'difficulty': cleaned['difficulty'],
                    'marks':      cleaned['marks'],
                    'reason':     f"Question already exists in the Question Bank for {exam.exam_name}.",
                    'existing_exam_name': exam.exam_name,
                })
                duplicate_rows_cleaned.append(cleaned)
            else:
                final_valid.append(cleaned)

        upload_id = str(uuid.uuid4())
        cache.set(
            f"{QB_UPLOAD_CACHE_PREFIX}{upload_id}",
            {
                'exam_id':          exam_id,
                'valid_rows':       final_valid,
                'duplicate_rows':   duplicate_rows_cleaned,  # only imported if mapDuplicates=true
            },
            timeout=QB_UPLOAD_CACHE_TTL,
        )

        return Response({
            'upload_id':          upload_id,
            'totalRows':          len(df),
            'validRows':          [_qb_row_to_preview(r, i) for i, r in enumerate(final_valid)],
            'invalidRows':        invalid_preview,
            'duplicateRows':      duplicate_preview,
            'duplicateExamName':  exam.exam_name,
        }, status=status.HTTP_200_OK)


class QuestionBankBulkUploadImportView(APIView):
    """
    POST /api/exams/<exam_id>/question-bank/bulk-upload/import/

    JSON body: { "upload_id": "<uuid-from-validate-step>", "mapDuplicates": false }
    Creates Question rows with mock_exam=None (Question Bank, not tied
    to any mock test). Rows are validated by subject; chapter (if the
    file supplied one) was resolved/auto-created under that subject at
    validate time and may be null here if no chapter was given.

    mapDuplicates: if true, the rows that were flagged as duplicates at
    validate time (already existing in the Question Bank) are imported
    too, in addition to the always-valid rows. Defaults to false, which
    preserves the original skip-duplicates behavior.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, exam_id):
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({'error': f'No exam found with id {exam_id}.'}, status=status.HTTP_404_NOT_FOUND)

        upload_id = (request.data.get('upload_id') or '').strip()
        if not upload_id:
            return Response({'error': '"upload_id" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        map_duplicates = bool(request.data.get('mapDuplicates', False))

        cache_key = f"{QB_UPLOAD_CACHE_PREFIX}{upload_id}"
        cached = cache.get(cache_key)
        if not cached:
            return Response({'error': 'Upload session has expired or was not found. Please re-upload and validate your file.'}, status=status.HTTP_404_NOT_FOUND)
        if cached['exam_id'] != exam_id:
            return Response({'error': 'upload_id does not belong to this exam.'}, status=status.HTTP_403_FORBIDDEN)

        valid_rows = list(cached['valid_rows'])
        mapped_count = 0
        if map_duplicates:
            duplicate_rows = cached.get('duplicate_rows') or []
            valid_rows.extend(duplicate_rows)
            mapped_count = len(duplicate_rows)

        if not valid_rows:
            return Response({'imported': 0, 'skipped': 0, 'mapped': 0})

        chapters_by_id = {
            c.pk: c for c in Chapter.objects.filter(
                pk__in=[r['chapter_id'] for r in valid_rows if r.get('chapter_id')]
            )
        }

        questions_to_create = []
        for row in valid_rows:
            questions_to_create.append(Question(
                exam=exam,
                mock_exam=None,  # Question Bank question — not tied to a mock test
                chapter=chapters_by_id.get(row['chapter_id']) if row.get('chapter_id') else None,
                question_text=row['text'],
                question_type=row['question_type'],
                marks=row['marks'],
                negative_marks=row['negative_marks'],
                difficulty_level=row['difficulty'],
                hint=row['hint'] or None,
                is_active=True,
            ))

        created_questions = Question.objects.bulk_create(questions_to_create)

        options_to_create = []
        answers_to_create = []
        for q, row in zip(created_questions, valid_rows):
            options_to_create.append(QuestionOption(
                question=q,
                option_a=row['option_a'],
                option_b=row['option_b'],
                option_c=row['option_c'],
                option_d=row['option_d'],
                option_e=row['option_e'] or '',
            ))
            answers_to_create.append(CorrectAnswer(question=q, option_id=row['correct_answer']))

        QuestionOption.objects.bulk_create(options_to_create)
        CorrectAnswer.objects.bulk_create(answers_to_create)

        cache.delete(cache_key)

        return Response({
            'imported': len(created_questions),
            'skipped':  0,
            'mapped':   mapped_count,
        }, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from .permissions import IsAdminUser


class AdminSessionUserView(APIView):
    """
    GET /api/admin/session-user/

    Deliberately isolated from the app's global TokenAuthentication.
    This is the ONLY endpoint that authenticates via Django's native
    session cookie (set by /admin/login/), so the rest of the API
    (including /api/auth/login/) is unaffected and never triggers
    session-based CSRF enforcement.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        })


# # ═════════════════════════════════════════════════════════════
# PYQ / MOCK TEST PDF IMPORT WIZARD — v10
#
# views.py - Enhanced PDF extraction with complete mathematical preservation
# and multi-layout support for NEET, JEE Main, JEE Advanced style PDFs.
#
# v10 CHANGES (bugfix + feature on top of v9):
# - FIXED CRITICAL BUG: _find_fraction_bars() scanned page.lines/page.rects
#   across the WHOLE PAGE, so vector lines belonging to a diagram (axes,
#   graph box edges, dashed reference lines — e.g. a P-V diagram sitting
#   right above the next question) were misdetected as fraction bars.
#   _extract_fraction_tokens() then stole nearby, unrelated question-stem
#   text as a bogus numerator/denominator, corrupting the stem (symptom:
#   "\frac{a}{q}" spliced into the middle of an ordinary sentence) and,
#   because a corrupted page can throw off the (1)(2)(3)(4) option-boundary
#   regex too, cascading into spurious "needs review" flags across that
#   whole page. Fixed by excluding each page's diagram bounding boxes
#   (found cheaply via new _find_diagram_bboxes(), a render-free sibling of
#   _find_diagram_regions()) from fraction-bar detection, plus a length cap
#   in _extract_fraction_tokens() as a second line of defense: a fraction
#   token is only kept if both its numerator and denominator are short
#   (a real fraction's numerator/denominator is never a run of prose).
# - Added _dedupe_duplicate_question_numbers(), called at the end of the
#   _extract_question_with_options() dispatcher: defensively merges/drops
#   duplicate question_number entries (keeping the richer one) and
#   re-indexes survivors' "index" 0..N-1 contiguously, guarding against
#   phantom extra questions from any stray digit sequence a corrupted
#   stretch of text might produce.
# - Added subject-wise block fallback: DEFAULT_SUBJECT_BLOCK_ORDER and
#   _assign_subjects_by_block(), used in PyqPdfUploadView.post() when a
#   paper has NO in-text subject headers at all (common in older JEE Main
#   PDFs — 2002, 2011, etc. — that just print Q1...Q90 back-to-back with no
#   "Physics (Section A)" markers). Splits the extracted question list into
#   len(subject_names) equal contiguous blocks in order, e.g. for 90
#   questions: Q1-30 -> Physics, Q31-60 -> Chemistry, Q61-90 -> Mathematics.
#   paper_details is now computed earlier in the view (before this
#   fallback runs, since it needs the exam's subject order) rather than
#   right before _persist().
#
# v9 CHANGES (bugfix on top of v8):
# - FIXED CRITICAL BUG: diagram-to-question matching in PyqPdfUploadView.post()
#   fell back to comparing diagrams_by_question keys (keyed by question_number)
#   against q["index"] (0-based list position). Since index == question_number - 1
#   for normal papers, this silently attached the PREVIOUS question's diagrams
#   to any question that had none of its own — causing images to "leak" forward
#   from one question/option set to the next. The broken fallback has been
#   removed entirely; diagrams_by_question is already correctly keyed by the
#   real question_number, so no fallback is needed or safe.
# - Added a defensive max-vertical-gap guard in _extract_pdf_images_by_question's
#   region-to-marker scoring so a diagram region can no longer be claimed by a
#   marker that is implausibly far above it on the page, even if that marker is
#   technically the closest "ceiling"-satisfying candidate found so far.
#
# v8 CHANGES:
# - Completely rewritten _detect_layout() with weighted multi-signal scoring
# - New "lettered_inline" layout for (A)(B)(C)(D) style papers (JEE Advanced)
# - Robust _extract_options_lettered() with 3-tier fallback
# - Improved _extract_answer_key_map() supporting grid tables + letter keys
# - _find_option_start_lettered() helper to fix stem/option boundary detection
# - _is_graphical_question() to flag image-only option questions gracefully
# - Added _extract_question_with_options_lettered_inline() for (A)(B)(C)(D) layout
# - Fixed critical bug: MCQ correct_answer was saving numerical_answer (empty string)
# - Subject/section detection now works for numeric_key layout too
# - _split_body_and_tail() handles both "Solutions" and "ANSWER KEY/KEYS" patterns
# ═════════════════════════════════════════════════════════════

import uuid
import re
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Max, Sum
import hashlib
from .models import (
    Exam, Subject, Chapter, Question, QuestionOption, CorrectAnswer, MockExam,
    TestDefinition, QuestionChapterMapping,
)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

PYQ_CACHE_PREFIX = "pyq_pdf_import_"
PYQ_CACHE_TTL = 1800
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

STATUS_VALID = "valid"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_FAILED = "failed"

ALLOWED_CORRECT = {"A", "B", "C", "D", "E"}
_OPTION_LETTERS = ("A", "B", "C", "D", "E")

QUESTION_TYPE_MCQ = "MCQ"
QUESTION_TYPE_NUMERICAL = "Numerical"

PYQ_STORAGE_DIR = Path("/tmp/pyq_imports")
PYQ_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Greek letters mapping
# ─────────────────────────────────────────────────────────────

GREEK_TO_LATEX = {
    'α': '\\alpha', 'β': '\\beta', 'γ': '\\gamma', 'δ': '\\delta',
    'ε': '\\epsilon', 'ζ': '\\zeta', 'η': '\\eta', 'θ': '\\theta',
    'ι': '\\iota', 'κ': '\\kappa', 'λ': '\\lambda', 'μ': '\\mu',
    'ν': '\\nu', 'ξ': '\\xi', 'ο': '\\omicron', 'π': '\\pi',
    'ρ': '\\rho', 'σ': '\\sigma', 'τ': '\\tau', 'υ': '\\upsilon',
    'φ': '\\phi', 'χ': '\\chi', 'ψ': '\\psi', 'ω': '\\omega',
    'Α': '\\Alpha', 'Β': '\\Beta', 'Γ': '\\Gamma', 'Δ': '\\Delta',
    'Ε': '\\Epsilon', 'Ζ': '\\Zeta', 'Η': '\\Eta', 'Θ': '\\Theta',
    'Ι': '\\Iota', 'Κ': '\\Kappa', 'Λ': '\\Lambda', 'Μ': '\\Mu',
    'Ν': '\\Nu', 'Ξ': '\\Xi', 'Ο': '\\Omicron', 'Π': '\\Pi',
    'Ρ': '\\Rho', 'Σ': '\\Sigma', 'Τ': '\\Tau', 'Υ': '\\Upsilon',
    'Φ': '\\Phi', 'Χ': '\\Chi', 'Ψ': '\\Psi', 'Ω': '\\Omega',
}

# ─────────────────────────────────────────────────────────────
# Mathematical symbols mapping
# ─────────────────────────────────────────────────────────────

MATH_SYMBOLS = {
    '∫': '\\int', '∑': '\\sum', '∏': '\\prod', '∂': '\\partial',
    '∇': '\\nabla', '×': '\\times', '÷': '\\div', '±': '\\pm',
    '∓': '\\mp', '≤': '\\leq', '≥': '\\geq', '≠': '\\neq',
    '≈': '\\approx', '≡': '\\equiv', '≅': '\\cong', '∼': '\\sim',
    '∝': '\\propto', '∞': '\\infty', '°': '^{\\circ}',
    '→': '\\rightarrow', '←': '\\leftarrow', '⇒': '\\Rightarrow',
    '⇐': '\\Leftarrow', '⇔': '\\Leftrightarrow', '↔': '\\leftrightarrow',
    '⟶': '\\longrightarrow', '⟵': '\\longleftarrow', '⇌': '\\rightleftharpoons',
}

# ─────────────────────────────────────────────────────────────
# Physics vector notation
# ─────────────────────────────────────────────────────────────

VECTOR_PATTERNS = [
    (re.compile(r'vec\s*\{([^}]*)\}'), r'\\vec{\1}'),
    (re.compile(r'bar\s*\{([^}]*)\}'), r'\\bar{\1}'),
    (re.compile(r'hat\s*\{([^}]*)\}'), r'\\hat{\1}'),
    (re.compile(r'overrightarrow\s*\{([^}]*)\}'), r'\\overrightarrow{\1}'),
    (re.compile(r'dot\s*\{([^}]*)\}'), r'\\dot{\1}'),
    (re.compile(r'ddot\s*\{([^}]*)\}'), r'\\ddot{\1}'),
    (re.compile(r'\^\s*([ijk])\b'), r'\\hat{\1}'),
    (re.compile(r'\b([ijk])\s*\^(?![a-zA-Z0-9{])'), r'\\hat{\1}'),
    (re.compile(r'\b([ijk])\^(?=[a-zA-Z])'), r'\\hat{\1} ')
]

# ─────────────────────────────────────────────────────────────
# Unit patterns
# ─────────────────────────────────────────────────────────────

UNIT_PATTERNS = [
    (re.compile(r'm\s*/\s*s(?![^a-zA-Z])'), r'm/s'),
    (re.compile(r'cm\s*/\s*s(?![^a-zA-Z])'), r'cm/s'),
    (re.compile(r'km\s*/\s*s(?![^a-zA-Z])'), r'km/s'),
    (re.compile(r'm\s*/\s*min'), r'm/min'),
    (re.compile(r'm\s*/\s*s\^2'), r'm/s^2'),
    (re.compile(r'cm\s*/\s*s\^2'), r'cm/s^2'),
    (re.compile(r'N\s*/\s*m'), r'N/m'),
    (re.compile(r'N\s*/\s*s'), r'N/s'),
    (re.compile(r'J\s*/\s*K'), r'J/K'),
    (re.compile(r'eV\s*/\s*nm'), r'eV/nm'),
    (re.compile(r'kg\s*\*?\s*m\s*/\s*s'), r'kg·m/s'),
    (re.compile(r'g\s*/\s*cm\^3'), r'g/cm^3'),
]

# ─────────────────────────────────────────────────────────────
# Chemical formula patterns
# ─────────────────────────────────────────────────────────────

CHEM_PATTERNS = [
    (re.compile(r'([A-Z][a-z]?)\s*_\{(\d+)\}'), r'\1_{\2}'),
    (re.compile(r'([A-Z][a-z]?)\s*_(\d+)'), r'\1_{\2}'),
    (re.compile(r'([A-Z][a-z]?)\s*\^\{([+-]\d*)\}'), r'\1^{\2}'),
    (re.compile(r'([A-Z][a-z]?)\s*\^([+-]\d*)'), r'\1^{\2}'),
    (re.compile(r'([A-Z][a-z]?)\s*\^\{([+-])\}'), r'\1^{\2}'),
    (re.compile(r'([A-Z][a-z]?)\s*\^([+-])'), r'\1^{\2}'),
    (re.compile(r'([A-Z][a-z]?)\s*_\{([^}]*)\}\s*\^\{([^}]*)\}'), r'\1_{\2}^{\3}'),
    (re.compile(r'K\s*_\{sp\}'), r'K_{sp}'),
    (re.compile(r'K\s*_\{c\}'), r'K_c'),
    (re.compile(r'K\s*_\{p\}'), r'K_p'),
    (re.compile(r'K\s*_\{eq\}'), r'K_{eq}'),
    (re.compile(r'pK\s*_\{a\}'), r'pK_a'),
    (re.compile(r'pK\s*_\{b\}'), r'pK_b'),
    (re.compile(r'p\s*H(?![a-zA-Z])'), r'pH'),
]

# ─────────────────────────────────────────────────────────────
# Math expression patterns
# ─────────────────────────────────────────────────────────────

MATH_PATTERNS = [
    (re.compile(r'\\frac\s*\{([^}]*)\}\s*\{([^}]*)\}'), r'\\frac{\1}{\2}'),
    (re.compile(r'(\d+)\s*/\s*(\d+)(?![^a-zA-Z])'), r'\\frac{\1}{\2}'),
    (re.compile(r'\\sqrt\s*\{([^}]*)\}'), r'\\sqrt{\1}'),
    (re.compile(r'([a-zA-Z])\s*_\{([^}]*)\}'), r'\1_{\2}'),
    (re.compile(r'([a-zA-Z])\s*_\s*([a-zA-Z0-9])'), r'\1_{\2}'),
    (re.compile(r'([a-zA-Z])\s*\^\{([^}]{1,3})\}(?![a-zA-Z])'), r'\1^{\2}'),
    (re.compile(r'([a-zA-Z])\s*\^\s*([a-zA-Z0-9])(?![a-zA-Z])'), r'\1^{\2}'),
    (re.compile(r'\b(sin|cos|tan|cot|sec|cosec|csc)\s*\^\{?([-]?\d+)\}?\s*([a-zA-Z0-9θφψωαβγδπ]+)'), r'\1^{\2} \3'),
    (re.compile(r'\b(sin|cos|tan|cot|sec|cosec|csc)\s*([a-zA-Z0-9θφψωαβγδπ]+)'), r'\1 \2'),
    (re.compile(r'\b(sin|cos|tan|cot|sec|cosec|csc)\s*\^{-1}\s*([a-zA-Z0-9θφψωαβγδπ]+)'), r'\1^{-1} \2'),
    (re.compile(r'\b(log|ln|lg)\s*_\{([^}]*)\}\s*([a-zA-Z0-9θφψωαβγδπ]+)'), r'\1_{\2} \3'),
    (re.compile(r'\b(log|ln|lg)\s*([a-zA-Z0-9θφψωαβγδπ]+)'), r'\1 \2'),
    (re.compile(r'\\lim\s*_\{([^}]*)\}'), r'\\lim_{\1}'),
    (re.compile(r'\\lim\s*([a-zA-Z0-9θφψωαβγδπ]+)'), r'\\lim \1'),
]

# ─────────────────────────────────────────────────────────────
# v6: Python-style power / root notation
# ─────────────────────────────────────────────────────────────

_SUPERSCRIPT_DIGIT_MAP = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
}
_SUPERSCRIPT_LETTER_MAP = {
    'ⁿ': 'n', 'ˣ': 'x', 'ʸ': 'y', 'ᵃ': 'a', 'ᵇ': 'b',
    'ᶜ': 'c', 'ᵈ': 'd', 'ᵉ': 'e', 'ᶠ': 'f', 'ᵍ': 'g',
    'ʰ': 'h', 'ⁱ': 'i', 'ʲ': 'j', 'ᵏ': 'k', 'ˡ': 'l',
    'ᵐ': 'm', 'ᵒ': 'o', 'ᵖ': 'p', 'ʳ': 'r', 'ˢ': 's',
    'ᵗ': 't', 'ᵘ': 'u', 'ᵛ': 'v', 'ʷ': 'w', 'ᶻ': 'z',
}
_SUPERSCRIPT_ALL_MAP = {**_SUPERSCRIPT_DIGIT_MAP, **_SUPERSCRIPT_LETTER_MAP}
_SUPERSCRIPT_RE = re.compile(
    '[' + re.escape(''.join(_SUPERSCRIPT_ALL_MAP.keys())) + ']+'
)
_SQRT_BRACED_RE = re.compile(r'√\s*\{([^}]+)\}')
_SQRT_PAREN_RE  = re.compile(r'√\s*\(([^)]+)\)')
_SQRT_BARE_RE   = re.compile(r'√\s*([A-Za-z0-9]+)')


def _convert_to_python_math(text: str) -> str:
    """Convert Unicode superscripts and √ into Python-style ** notation."""
    def _replace_superscript(m: re.Match) -> str:
        plain = ''.join(_SUPERSCRIPT_ALL_MAP[ch] for ch in m.group(0))
        return f' ** {plain}'
    text = _SUPERSCRIPT_RE.sub(_replace_superscript, text)
    text = _SQRT_BRACED_RE.sub(lambda m: f'({m.group(1)}) ** 0.5', text)
    text = _SQRT_PAREN_RE.sub(lambda m: f'({m.group(1)}) ** 0.5', text)
    text = _SQRT_BARE_RE.sub(lambda m: f'{m.group(1)} ** 0.5', text)
    return text


# ─────────────────────────────────────────────────────────────
# Complete Mathematical Expression Preservation
# ─────────────────────────────────────────────────────────────

def _preserve_physics_math(text: str) -> str:
    """Preserve all physics, chemistry, and mathematics expressions."""
    text = _convert_to_python_math(text)
    text = _protect_latex_delimiters(text)

    for greek_unicode, greek_latex in GREEK_TO_LATEX.items():
        text = text.replace(greek_unicode, greek_latex)

    _greek_names = "|".join(sorted(
        {v.lstrip("\\") for v in GREEK_TO_LATEX.values()}, key=len, reverse=True
    ))
    text = re.sub(rf'(\\(?:{_greek_names}))(?=[a-zA-Z])', r'\1 ', text)

    for symbol_unicode, symbol_latex in MATH_SYMBOLS.items():
        text = text.replace(symbol_unicode, symbol_latex)

    for pattern, replacement in VECTOR_PATTERNS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in UNIT_PATTERNS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in CHEM_PATTERNS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in MATH_PATTERNS:
        text = pattern.sub(replacement, text)

    text = _restore_latex_delimiters(text)

    text = re.sub(r'\\\s*\(', r'\\(', text)
    text = re.sub(r'\\\s*\)', r'\\)', text)
    text = re.sub(r'\\\s*\[', r'\\[', text)
    text = re.sub(r'\\\s*\]', r'\\]', text)

    return text


def _protect_latex_delimiters(text: str) -> str:
    text = text.replace('\\(', '<<LATEX_OPEN>>')
    text = text.replace('\\)', '<<LATEX_CLOSE>>')
    text = text.replace('\\[', '<<LATEX_OPEN_BRACKET>>')
    text = text.replace('\\]', '<<LATEX_CLOSE_BRACKET>>')
    return text


def _restore_latex_delimiters(text: str) -> str:
    text = text.replace('<<LATEX_OPEN>>', '\\(')
    text = text.replace('<<LATEX_CLOSE>>', '\\)')
    text = text.replace('<<LATEX_OPEN_BRACKET>>', '\\[')
    text = text.replace('<<LATEX_CLOSE_BRACKET>>', '\\]')
    return text


# ─────────────────────────────────────────────────────────────
# Diagram / Image Extraction Helpers
# ─────────────────────────────────────────────────────────────

def _get_clean_page_graphics(page, watermark_repeat_threshold=3):
    def _strip_watermarks(objs, threshold, left_key="x0", right_key="x1"):
        groups = defaultdict(list)
        for o in objs:
            w = round(o.get(right_key, 0) - o.get(left_key, 0))
            h = round(o.get("bottom", 0) - o.get("top", 0))
            groups[(w, h)].append(o)
        keep = []
        for key, members in groups.items():
            if len(members) > threshold:
                continue
            keep.extend(members)
        return keep

    images = _strip_watermarks(page.images, watermark_repeat_threshold)
    rects  = _strip_watermarks(page.rects,  watermark_repeat_threshold)
    lines  = _strip_watermarks(page.lines,  max(watermark_repeat_threshold, 5))
    curves = _strip_watermarks(page.curves, max(watermark_repeat_threshold, 5))
    return images, lines, curves, rects


# ─────────────────────────────────────────────────────────────
# PATCHED: _find_diagram_regions — v12
# Raises min_weight for non-image (curve/line/rect only) clusters
# to filter out MathonGo watermark curves that escape _strip_watermarks.
# ─────────────────────────────────────────────────────────────
 
def _find_diagram_regions(page, min_weight=3, min_height=20, min_width=20, cluster_gap=10):
    """
    v12: same as v10/v11 but with an additional filter:
    clusters that contain NO raster image member must reach weight >= 8
    (i.e. at least 4 distinct non-watermark shapes) before being treated as
    a real diagram region. This suppresses the MathonGo watermark glyph clusters
    (each ~20×20 pt Bézier pair, weight=2 each) that survive _strip_watermarks
    when their sizes differ slightly between PDF instances.
    """
    graphical_objs = []
    clean_images, clean_lines, clean_curves, clean_rects = _get_clean_page_graphics(page)
 
    for img in clean_images:
        graphical_objs.append({
            "top": img["top"], "bottom": img["bottom"],
            "left": img["x0"], "right": img["x1"],
            "weight": 10, "type": "image"
        })
    for shape_list in (clean_lines, clean_curves, clean_rects):
        for obj in shape_list:
            width  = obj.get("x1", 0) - obj.get("x0", 0)
            height = obj.get("bottom", 0) - obj.get("top", 0)
            if width > 10 or height > 10:
                graphical_objs.append({
                    "top": obj["top"], "bottom": obj["bottom"],
                    "left": obj["x0"], "right": obj["x1"],
                    "weight": 2, "type": "shape"
                })
 
    if not graphical_objs:
        return []
 
    n = len(graphical_objs)
    parent = list(range(n))
 
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
 
    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
 
    def boxes_close(a, b):
        vertical_gap   = max(a["top"],  b["top"])  - min(a["bottom"], b["bottom"])
        horizontal_gap = max(a["left"], b["left"]) - min(a["right"],  b["right"])
        return vertical_gap <= cluster_gap and horizontal_gap <= cluster_gap
 
    for i in range(n):
        for j in range(i + 1, n):
            if boxes_close(graphical_objs[i], graphical_objs[j]):
                union(i, j)
 
    clusters = {}
    for i, obj in enumerate(graphical_objs):
        clusters.setdefault(find(i), []).append(obj)
 
    results = []
    for members in clusters.values():
        has_raster_image = any(m["type"] == "image" for m in members)
        weight = sum(m["weight"] for m in members)
 
        # v12: curve/line/rect-only clusters need higher weight to be real diagrams
        effective_min_weight = min_weight if has_raster_image else max(min_weight, 8)
        if weight < effective_min_weight:
            continue
 
        tops   = [m["top"]    for m in members]
        bots   = [m["bottom"] for m in members]
        lefts  = [m["left"]   for m in members]
        rights = [m["right"]  for m in members]
 
        top, bottom = min(tops), max(bots)
        left, right = min(lefts), max(rights)
        width  = right - left
        height = bottom - top
 
        if height < min_height or width < min_width:
            continue
 
        words = page.extract_words()
        text_in_region = [
            w for w in words
            if (w["top"] <= bottom + 5 and w["bottom"] >= top - 5 and
                w["x0"] <= right + 5  and w["x1"] >= left - 5)
        ]
        if text_in_region and weight < 5:
            continue
 
        pad = 5
        try:
            cropped = page.crop((
                max(0.0, left - pad),
                max(0.0, top  - pad),
                min(float(page.width),  right  + pad),
                min(float(page.height), bottom + pad),
            ))
            im = cropped.to_image(resolution=200)
            if _is_blank_crop(im.original):
                continue
            buf = _io.BytesIO()
            im.save(buf, format="PNG")
            results.append({
                "top": top, "bottom": bottom, "left": left, "right": right,
                "png_bytes": _clean_diagram_image(buf.getvalue()),
                "weight": weight,
            })
        except Exception as e:
            print(f"Error cropping region: {e}")
            continue
 
    results.sort(key=lambda r: (r["top"], r["left"]))
    return results
 


def _find_diagram_bboxes(page, min_weight=3, min_height=20, min_width=20, cluster_gap=10):
    """
    v10: lightweight sibling of _find_diagram_regions() — same clustering
    logic (union-find over images/lines/rects), but returns only bounding
    boxes with no PNG cropping/cleaning. Used to exclude diagram geometry
    from fraction-bar detection cheaply during the text-extraction pass
    (well before the separate, PNG-rendering diagram-extraction pass that
    still uses _find_diagram_regions()).
    """
    graphical_objs = []
    clean_images, clean_lines, clean_curves, clean_rects = _get_clean_page_graphics(page)

    for img in clean_images:
        graphical_objs.append({
            "top": img["top"], "bottom": img["bottom"],
            "left": img["x0"], "right": img["x1"], "weight": 10,
        })
    for shape_list in (clean_lines, clean_curves, clean_rects):
        for obj in shape_list:
            width  = obj.get("x1", 0) - obj.get("x0", 0)
            height = obj.get("bottom", 0) - obj.get("top", 0)
            if width > 10 or height > 10:
                graphical_objs.append({
                    "top": obj["top"], "bottom": obj["bottom"],
                    "left": obj["x0"], "right": obj["x1"], "weight": 2,
                })

    if not graphical_objs:
        return []

    n = len(graphical_objs)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    def boxes_close(a, b):
        vertical_gap   = max(a["top"],  b["top"])  - min(a["bottom"], b["bottom"])
        horizontal_gap = max(a["left"], b["left"]) - min(a["right"],  b["right"])
        return vertical_gap <= cluster_gap and horizontal_gap <= cluster_gap

    for i in range(n):
        for j in range(i + 1, n):
            if boxes_close(graphical_objs[i], graphical_objs[j]):
                union(i, j)

    clusters = {}
    for i, obj in enumerate(graphical_objs):
        clusters.setdefault(find(i), []).append(obj)

    bboxes = []
    for members in clusters.values():
        weight = sum(m["weight"] for m in members)
        top, bottom = min(m["top"] for m in members), max(m["bottom"] for m in members)
        left, right = min(m["left"] for m in members), max(m["right"] for m in members)
        if weight < min_weight or (bottom - top) < min_height or (right - left) < min_width:
            continue
        bboxes.append((top, bottom, left, right))
    return bboxes


def _clean_diagram_image(png_bytes: bytes, white_thresh: int = 238, noise_thresh: int = 215) -> bytes:
    try:
        from PIL import Image as PILImage
        import numpy as np

        img  = PILImage.open(io.BytesIO(png_bytes)).convert("RGBA")
        data = np.array(img, dtype=np.uint16)
        r, g, b = data[..., 0], data[..., 1], data[..., 2]
        near_white = (r >= white_thresh) & (g >= white_thresh) & (b >= white_thresh)
        data[near_white] = [255, 255, 255, 255]
        clean = PILImage.fromarray(data.astype(np.uint8), "RGBA")

        rgb_arr = np.array(clean.convert("RGB"), dtype=np.int16)
        diff    = np.abs(rgb_arr - 255).max(axis=2)
        mask    = diff > (255 - noise_thresh)
        rows    = np.any(mask, axis=1)
        cols    = np.any(mask, axis=0)
        if rows.any() and cols.any():
            pad  = 8
            rmin = max(0, int(np.where(rows)[0][0])  - pad)
            rmax = min(clean.height - 1, int(np.where(rows)[0][-1]) + pad)
            cmin = max(0, int(np.where(cols)[0][0])  - pad)
            cmax = min(clean.width  - 1, int(np.where(cols)[0][-1]) + pad)
            clean = clean.crop((cmin, rmin, cmax + 1, rmax + 1))

        final = PILImage.new("RGB", clean.size, (255, 255, 255))
        final.paste(clean, mask=clean.split()[3])
        buf = io.BytesIO()
        final.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as e:
        print(f"[_clean_diagram_image] fallback – {e}")
        return png_bytes


def _is_blank_crop(pil_image, white_threshold=245, min_ink_fraction=0.00015):
    try:
        gray = pil_image.convert("L")
        hist  = gray.histogram()
        total = sum(hist)
        if total == 0:
            return True
        non_white = sum(hist[:white_threshold])
        return (non_white / total) < min_ink_fraction
    except Exception:
        return False


def _crop_band_diagram(page, band_top, band_bottom, band_left=None, band_right=None,
                        min_weight=3, min_height=15, min_width=15, min_shapes=2, pad=4):
    if band_left  is None: band_left  = 0.0
    if band_right is None: band_right = float(page.width)

    objs = []
    clean_images, clean_lines, clean_curves, clean_rects = _get_clean_page_graphics(page)

    def _in_band(o):
        return (o["top"]  >= band_top  - 1 and o["bottom"] <= band_bottom + 1 and
                o["left"] >= band_left - 1 and o["right"]  <= band_right  + 1)

    for img in clean_images:
        cand = {"top": img["top"], "bottom": img["bottom"],
                "left": img["x0"], "right": img["x1"], "weight": 10}
        if _in_band(cand): objs.append(cand)

    for shape_list in (clean_lines, clean_curves, clean_rects):
        for obj in shape_list:
            cand = {"top": obj["top"], "bottom": obj["bottom"],
                    "left": obj.get("x0", 0), "right": obj.get("x1", 0), "weight": 2}
            w = cand["right"] - cand["left"]
            h = cand["bottom"] - cand["top"]
            if (w > 8 or h > 8) and _in_band(cand):
                objs.append(cand)

    if not objs or sum(o["weight"] for o in objs) < min_weight:
        return None

    has_real_image = any(o["weight"] == 10 for o in objs)
    if not has_real_image and len(objs) < min_shapes:
        return None

    top    = min(o["top"]    for o in objs)
    bottom = max(o["bottom"] for o in objs)
    left   = min(o["left"]   for o in objs)
    right  = max(o["right"]  for o in objs)

    if (bottom - top) < min_height or (right - left) < min_width:
        return None

    try:
        cropped = page.crop((
            max(band_left,   left   - pad),
            max(band_top,    top    - pad),
            min(band_right,  right  + pad),
            min(band_bottom, bottom + pad),
        ))
        im = cropped.to_image(resolution=200)
        if _is_blank_crop(im.original):
            return None
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return _clean_diagram_image(buf.getvalue())
    except Exception as e:
        print(f"Error cropping band: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Region → question/option marker matching
# ─────────────────────────────────────────────────────────────
#
# NOTE (v9): MAX_MARKER_REGION_GAP bounds how far ABOVE a diagram region a
# candidate marker (Q number or option letter) may sit and still be treated
# as that region's owner. Without this bound, a region on a page with sparse
# markers could be claimed by a marker many questions earlier merely because
# it was the closest one satisfying the "ceiling" (next-question-top) check —
# this is what allowed diagrams to visually "belong" to the wrong question in
# edge cases. This is a defensive guard, independent of the index/qnum bug
# fixed in PyqPdfUploadView.post() below.
MAX_MARKER_REGION_GAP = 260  # points; ~ a generous multi-line question stem

import re as _re
import io as _io

def _extract_pdf_images_by_question(file_obj, row_tolerance=8) -> dict:
    """
    Content-first diagram extraction, matching detected blobs to nearest Q/option marker.

    v12 FIXES:
    - Cross-page image assignment: track last_q_number across pages so diagrams
      at the top of a page (continuation of previous-page question) are correctly
      attributed instead of being silently dropped.
    - Raise effective min_weight for curve-only clusters (no raster image) to
      filter out watermark-curve noise that passes _strip_watermarks when glyph
      sizes vary slightly between PDF instances.

    v13 FIX (marker false-positives corrupting question ownership):
    - The Q-marker regex previously matched ANY "<digits><.|)>" text anywhere on
      the page, including decimal numbers inside option values (e.g. "256.2",
      "240.2" in Q1's data table) and numbers embedded in prose next to a stray
      punctuation token (e.g. "140" + ")" from "atomic weight 140 )" in Q10,
      or "16" + "1." from an unrelated fraction). These produced bogus 'Q'
      markers with huge fake values (140, 161, 236, 256...) that corrupted
      last_q_number (used by the cross-page/no-candidate fallback) and the
      per-page ownership scoring - causing diagrams belonging to later
      questions (e.g. Q6's pulley diagram, Q23's meter-bridge diagram) to be
      wrongly attached to an earlier question (e.g. Q2) instead.
      Fixed with two guards:
        1. (?!\\d) after the marker punctuation, so "256.2" no longer matches
           (mirrors the same guard already used in _QUESTION_PATTERN elsewhere
           in this file).
        2. A left-margin check: real question-number markers are always
           flush-left on the page; numbers embedded mid-sentence are not. A
           candidate marker is only accepted if its x0 is within
           Q_MARKER_X_TOLERANCE points of the page's leftmost word.
    """
    import pdfplumber

    file_obj.seek(0)
    result = {}
    option_re      = _re.compile(r'(?:\(([A-D1-4])\)|([A-D])[\.)\s])', _re.IGNORECASE)
    digit_to_letter = {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}
    DIAGRAM_CLUSTER_GAP = 4
    Q_MARKER_X_TOLERANCE = 40  # points; real Q-markers are flush-left on the page

    # Track the last Q number seen as we walk pages in order, so cross-page
    # images at the top of a page can be assigned to the correct question.
    last_q_number = None

    with pdfplumber.open(file_obj) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                words = page.extract_words(use_text_flow=False)
                if not words:
                    continue

                # v13 FIX: real question-number markers are always flush-left
                # on the page. Numbers that happen to look like "N." or "N)"
                # but sit mid-sentence (option values, physical quantities,
                # decimal fragments) are not markers and must be rejected.
                left_margin = min((w['x0'] for w in words), default=0)

                def _near_left_margin(x0):
                    return x0 <= left_margin + Q_MARKER_X_TOLERANCE

                markers = []
                for i, word in enumerate(words):
                    text = word['text'].strip()
                    # v13 FIX: (?!\d) rejects decimal numbers like "256.2" —
                    # mirrors the guard already used in _QUESTION_PATTERN.
                    m = _re.match(r'^(?:Q\.?\s*)?(\d{1,3})[\.\)](?!\d)', text, _re.IGNORECASE)
                    if m and _near_left_margin(word['x0']):
                        markers.append({
                            'top': word['top'], 'left': word['x0'],
                            'kind': 'Q', 'value': int(m.group(1)),
                        })
                        continue
                    if i + 1 < len(words) and _near_left_margin(word['x0']):
                        combined = text + words[i + 1]['text'].strip()
                        m = _re.match(r'^(?:Q\.?\s*)?(\d{1,3})[\.\)](?!\d)', combined, _re.IGNORECASE)
                        if m:
                            markers.append({
                                'top': word['top'], 'left': word['x0'],
                                'kind': 'Q', 'value': int(m.group(1)),
                            })
                            continue

                    mm     = option_re.match(text)
                    letter = None
                    if mm:
                        raw    = (mm.group(1) or mm.group(2) or '').upper()
                        letter = digit_to_letter.get(raw, raw)
                    else:
                        m2 = _re.match(r'\(([1-4])\)', text)
                        if m2:
                            letter = digit_to_letter.get(m2.group(1))
                    if letter in ('A', 'B', 'C', 'D'):
                        markers.append({'top': word['top'], 'left': word['x0'], 'kind': letter})

                # Update last_q_number with any Q markers found on this page
                # (we do this BEFORE image matching so that if a page has both
                #  a cross-page image at the top AND new Q markers, the image
                #  at the top still gets last_q_number from the previous page).
                page_q_numbers = sorted(
                    [m['value'] for m in markers if m['kind'] == 'Q']
                )

                if not markers:
                    # Still update last_q_number if we found Q values above
                    if page_q_numbers:
                        last_q_number = page_q_numbers[-1]
                    # No markers at all → process images with last_q_number fallback
                    regions = _find_diagram_regions(page, cluster_gap=DIAGRAM_CLUSTER_GAP)
                    if last_q_number is not None:
                        for region in regions:
                            bucket = result.setdefault(last_q_number, {'question': [], 'options': {}})
                            bucket['question'].append(region['png_bytes'])
                    continue

                markers.sort(key=lambda m: (m['top'], m['left']))

                q_markers_sorted = sorted(
                    [m for m in markers if m['kind'] == 'Q'],
                    key=lambda m: m['top']
                )

                def owning_question(marker_top):
                    owner = None
                    for m in q_markers_sorted:
                        if m['top'] <= marker_top + 1: owner = m['value']
                        else: break
                    return owner

                def next_q_top_after(marker_top):
                    for m in q_markers_sorted:
                        if m['top'] > marker_top + 1: return m['top']
                    return float('inf')

                regions          = _find_diagram_regions(page, cluster_gap=DIAGRAM_CLUSTER_GAP)
                pending_options  = {}
                pending_questions = {}

                for region in regions:
                    r_top, r_bottom, r_left = region['top'], region['bottom'], region['left']

                    # Candidates: markers strictly ABOVE this region
                    candidates = [m for m in markers if m['top'] <= r_top + 6]

                    if not candidates:
                        # ── v12 FIX: cross-page fallback ──────────────────
                        # No marker above this image on this page → it belongs
                        # to the last question seen (which started on a prior page).
                        if last_q_number is not None:
                            bucket = result.setdefault(last_q_number, {'question': [], 'options': {}})
                            bucket['question'].append(region['png_bytes'])
                        continue

                    def _score(m, _r_top=r_top, _r_bottom=r_bottom, _r_left=r_left):
                        if m['kind'] == 'Q':
                            ceiling = next_q_top_after(m['top'])
                        else:
                            owner_q_top = None
                            for qm in q_markers_sorted:
                                if qm['top'] <= m['top'] + 1: owner_q_top = qm['top']
                                else: break
                            ceiling = (next_q_top_after(owner_q_top)
                                       if owner_q_top is not None else float('inf'))
                        if _r_bottom > ceiling + 4:
                            return float('inf')
                        if (_r_top - m['top']) > MAX_MARKER_REGION_GAP:
                            return float('inf')
                        return (_r_top - m['top']) + 0.5 * abs(m['left'] - _r_left)

                    scores   = {i: _score(m) for i, m in enumerate(candidates)}
                    best_idx = min(scores, key=scores.__getitem__)

                    if scores[best_idx] == float('inf'):
                        # All candidates scored infinite (ceiling violations).
                        # Fall back to last_q_number rather than dropping the image.
                        if last_q_number is not None:
                            bucket = result.setdefault(last_q_number, {'question': [], 'options': {}})
                            bucket['question'].append(region['png_bytes'])
                        continue

                    owner_marker = candidates[best_idx]
                    qnum = (owner_marker['value'] if owner_marker['kind'] == 'Q'
                            else owning_question(owner_marker['top']))
                    if qnum is None:
                        if last_q_number is not None:
                            bucket = result.setdefault(last_q_number, {'question': [], 'options': {}})
                            bucket['question'].append(region['png_bytes'])
                        continue

                    if owner_marker['kind'] == 'Q':
                        pending_questions.setdefault(qnum, []).append(region)
                    else:
                        pending_options.setdefault((qnum, owner_marker['kind']), []).append(region)

                for qnum, regs in pending_questions.items():
                    bucket = result.setdefault(qnum, {'question': [], 'options': {}})
                    for r in regs:
                        bucket['question'].append(r['png_bytes'])

                for (qnum, letter), regs in pending_options.items():
                    bucket = result.setdefault(qnum, {'question': [], 'options': {}})
                    best   = max(regs, key=lambda r: (r['right'] - r['left']) * (r['bottom'] - r['top']))
                    bucket['options'][letter] = [best['png_bytes']]

                # Update last_q_number to the highest Q seen on this page
                if page_q_numbers:
                    last_q_number = page_q_numbers[-1]

            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                continue

    file_obj.seek(0)
    return result



# ─────────────────────────────────────────────────────────────
# Superscript / fraction reconstruction (v7)
# ─────────────────────────────────────────────────────────────

_SLASH_LOOKALIKES = {'⁄': '/', '∕': '/'}


def _normalize_slashes(text: str) -> str:
    for bad, good in _SLASH_LOOKALIKES.items():
        text = text.replace(bad, good)
    return text


def _find_fraction_bars(page, bbox, min_bar_width=3.0, max_bar_width=140.0,
                         max_bar_height=1.8, exclude_regions=None):
    """
    v10 FIX: exclude_regions (a list of (top, bottom, left, right) boxes —
    diagram bounding boxes on this page) lets the caller keep genuine
    fraction bars while throwing out lines/rects that are actually part of
    a diagram: axis lines, graph box edges, dashed reference lines, etc.
    Without this, a page containing e.g. a P-V diagram or a cooling-curve
    graph has every thin diagram line treated as a candidate fraction bar,
    and _extract_fraction_tokens() then steals nearby question-stem text
    as a bogus numerator/denominator — this is what produced garbled
    output like "\\frac{a}{q}" spliced into the middle of an unrelated
    sentence.
    """
    exclude_regions = exclude_regions or []
    bars = []
    for shape_list in (page.lines, page.rects):
        for obj in shape_list:
            top    = obj.get("top",    0)
            bottom = obj.get("bottom", top)
            x0     = obj.get("x0",     0)
            x1     = obj.get("x1",     x0)
            height = bottom - top
            width  = x1 - x0
            if not (bbox[0] - 2 <= x0 and x1 <= bbox[2] + 2 and bbox[1] - 2 <= top <= bbox[3] + 2):
                continue
            if not (min_bar_width <= width <= max_bar_width and height <= max_bar_height):
                continue
            if any(
                top >= r_top - 2 and bottom <= r_bottom + 2 and
                x0  >= r_left - 2 and x1    <= r_right  + 2
                for (r_top, r_bottom, r_left, r_right) in exclude_regions
            ):
                continue
            bars.append({"top": top, "bottom": bottom, "x0": x0, "x1": x1})
    return bars


def _extract_fraction_tokens(chars, bars, x_pad=2.0, vert_reach=16.0, max_component_chars=40):
    tokens   = []
    consumed = set()

    for bar in bars:
        num_chars = [
            c for c in chars
            if id(c) not in consumed
            and c.get("text", "").strip()
            and c.get("bottom", 0) <= bar["top"] + 1.0
            and c.get("bottom", 0) >= bar["top"] - vert_reach
            and c["x1"] > bar["x0"] - x_pad and c["x0"] < bar["x1"] + x_pad
        ]
        den_chars = [
            c for c in chars
            if id(c) not in consumed
            and c.get("text", "").strip()
            and c.get("top", 0) >= bar["bottom"] - 1.0
            and c.get("top", 0) <= bar["bottom"] + vert_reach
            and c["x1"] > bar["x0"] - x_pad and c["x0"] < bar["x1"] + x_pad
        ]
        if not num_chars or not den_chars:
            continue

        num_chars.sort(key=lambda c: c["x0"])
        den_chars.sort(key=lambda c: c["x0"])

        num_text = _reconstruct_line_with_superscripts(num_chars)
        den_text = _reconstruct_line_with_superscripts(den_chars)

        # v10 FIX: a real fraction's numerator/denominator is a short math
        # expression ("Mg", "2M", a digit, a variable). If either side
        # comes out implausibly long, the "bar" almost certainly wasn't a
        # real fraction rule — it grabbed a run of ordinary prose instead
        # (typically a diagram line sitting near unrelated question text
        # that slipped past the exclude_regions check, or a page with no
        # detected diagram region at all). Skip the token; leave the chars
        # as normal, unconsumed text.
        if len(num_text) > max_component_chars or len(den_text) > max_component_chars:
            continue

        for c in num_chars + den_chars:
            consumed.add(id(c))

        tokens.append({
            "text":     f"\\frac{{{num_text}}}{{{den_text}}}",
            "x0":       bar["x0"],
            "x1":       bar["x1"],
            "top":      num_chars[0]["top"],
            "bottom":   bar["bottom"],
            "size":     None,
            "_is_token": True,
        })

    return tokens, consumed


def _reconstruct_line_with_superscripts(line_chars, size_ratio_thresh=0.92,
                                         gap_ratio_thresh=0.22,
                                         raise_thresh=1.0, drop_thresh=1.0):
    if not line_chars:
        return ""

    sizes         = Counter(round(c["size"], 1) for c in line_chars if c.get("size"))
    if not sizes:
        return "".join(c.get("text", "") for c in line_chars)
    baseline_size = sizes.most_common(1)[0][0]
    gap_thresh    = baseline_size * gap_ratio_thresh

    baseline_tops = [
        c["top"] for c in line_chars
        if c.get("size") and round(c["size"], 1) == baseline_size
    ]
    baseline_top  = min(baseline_tops) if baseline_tops else None

    out      = []
    run      = []
    run_kind = None
    prev_x1  = None

    def _small(c):
        if c.get("_is_token"): return False
        size = round(c.get("size", baseline_size), 1)
        return size <= baseline_size * size_ratio_thresh

    def _is_superscript(c):
        if not _small(c): return False
        if baseline_top is not None and c.get("top", baseline_top) > baseline_top - raise_thresh:
            return False
        return True

    def _is_subscript(c):
        if not _small(c): return False
        if baseline_top is not None and c.get("top", baseline_top) < baseline_top + drop_thresh:
            return False
        return True

    def _flush_run():
        nonlocal run_kind
        if run:
            run_text = "".join(ch.get("text", "") for ch in run)
            wrapper  = "^" if run_kind == "sup" else "_"
            out.append(f"{wrapper}{{{run_text}}}")
            run.clear()
        run_kind = None

    i = 0
    n = len(line_chars)
    while i < n:
        c      = line_chars[i]
        ch_text = c.get("text", "")
        x0      = c.get("x0", 0)

        if (prev_x1 is not None and ch_text.strip()
                and (x0 - prev_x1) > gap_thresh
                and out and not out[-1].endswith(" ")):
            out.append(" ")
        prev_x1 = c.get("x1", x0)

        if not ch_text.strip():
            _flush_run()
            out.append(ch_text)
            i += 1
            continue

        if ch_text in ("-", "\u2212") and not _is_superscript(c) and i + 1 < n:
            nxt = line_chars[i + 1]
            if nxt.get("text", "").strip() and _is_superscript(nxt):
                if run_kind not in (None, "sup"):
                    _flush_run()
                run_kind = "sup"
                run.append(c)
                prev_x1 = c.get("x1", x0)
                i += 1
                continue

        if _is_superscript(c):
            if run_kind not in (None, "sup"): _flush_run()
            run_kind = "sup"
            run.append(c)
        elif _is_subscript(c):
            if run_kind not in (None, "sub"): _flush_run()
            run_kind = "sub"
            run.append(c)
        else:
            was_run = bool(run)
            _flush_run()
            if was_run and out and not out[-1].endswith(" "):
                out.append(" ")
            out.append(ch_text)

        i += 1

    _flush_run()
    return "".join(out)


def _assign_lines(stream, baseline_tol=3.0, search_window=14.0):
    if not stream:
        return []

    sizes = Counter(
        round(c["size"], 1) for c in stream
        if c.get("size") and not c.get("_is_token")
    )
    global_baseline_size = sizes.most_common(1)[0][0] if sizes else None

    normal_chars = [
        c for c in stream
        if not c.get("_is_token")
        and c.get("size")
        and global_baseline_size is not None
        and round(c["size"], 1) >= global_baseline_size * 0.97
    ]
    other_chars = [c for c in stream if c not in normal_chars]

    normal_chars.sort(key=lambda c: c["top"])
    anchors = []
    for c in normal_chars:
        placed = False
        for a in anchors:
            if abs(c["top"] - a["top"]) <= baseline_tol:
                a["members"].append(c)
                placed = True
                break
        if not placed:
            anchors.append({"top": c["top"], "members": [c]})

    if not anchors:
        stream_sorted = sorted(stream, key=lambda c: (c["top"], c["x0"]))
        lines, current_line, current_top = [], [], None
        for c in stream_sorted:
            if current_top is None or abs(c["top"] - current_top) <= baseline_tol:
                current_line.append(c)
                current_top = c["top"] if current_top is None else current_top
            else:
                lines.append(current_line)
                current_line, current_top = [c], c["top"]
        if current_line:
            lines.append(current_line)
        for line in lines:
            line.sort(key=lambda c: c["x0"])
        return lines

    for c in other_chars:
        top = c.get("top", 0)
        best_anchor, best_dist = None, None
        for a in anchors:
            dist = abs(top - a["top"])
            if dist <= search_window and (best_dist is None or dist < best_dist):
                best_anchor, best_dist = a, dist
        if best_anchor is not None:
            best_anchor["members"].append(c)
        else:
            anchors.append({"top": top, "members": [c]})

    anchors.sort(key=lambda a: a["top"])
    lines = []
    for a in anchors:
        a["members"].sort(key=lambda c: c["x0"])
        lines.append(a["members"])
    return lines


def _extract_text_preserving_superscripts(page, bbox, exclude_regions=None):
    chars = [
        c for c in page.chars
        if bbox[1] <= c["top"] <= bbox[3] and bbox[0] <= c["x0"] <= bbox[2]
    ]
    if not chars:
        return ""

    try:
        bars = _find_fraction_bars(page, bbox, exclude_regions=exclude_regions)
    except Exception:
        bars = []
    frac_tokens, consumed_ids = _extract_fraction_tokens(chars, bars) if bars else ([], set())

    remaining_chars = [c for c in chars if id(c) not in consumed_ids]
    stream          = remaining_chars + frac_tokens
    lines           = _assign_lines(stream)
    rebuilt_lines   = [_reconstruct_line_with_superscripts(line_chars) for line_chars in lines]
    return "\n".join(rebuilt_lines)


def _extract_pdf_text_preserved(file_obj, top_margin: float = 68, bottom_margin: float = 58) -> str:
    """Extract text from every page, cropping fixed header/footer margins, preserving math."""
    try:
        import pdfplumber
    except ImportError:
        raise ValueError("pdfplumber is not installed. Add 'pdfplumber>=0.11' to requirements.txt.")

    try:
        page_texts = []
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                height = page.height
                bbox   = (0, top_margin, page.width, max(height - bottom_margin, top_margin + 1))

                # v10 FIX: find this page's diagram bounding boxes first so
                # fraction-bar detection can exclude them (see
                # _find_fraction_bars / _find_diagram_bboxes above).
                try:
                    exclude_regions = _find_diagram_bboxes(page)
                except Exception:
                    exclude_regions = []

                text = _extract_text_preserving_superscripts(page, bbox, exclude_regions=exclude_regions)

                if not text.strip():
                    try:
                        cropped = page.within_bbox(bbox)
                    except Exception:
                        cropped = page
                    text = cropped.extract_text(x_tolerance=3, y_tolerance=3) or ""

                if text:
                    text = _normalize_slashes(text)
                    text = _preserve_physics_math(text)
                    page_texts.append(text)
    except Exception as exc:
        raise ValueError(f"Could not read the PDF: {exc}") from exc

    page_texts = _strip_recurring_edge_lines(page_texts)
    return "\n".join(page_texts)

# ─────────────────────────────────────────────────────────────
# PATCH FILE: views_v11 — paste these functions into views.py
# replacing their v10 equivalents
# ─────────────────────────────────────────────────────────────
 
import re
 
# ─────────────────────────────────────────────────────────────
# NEW HELPER: lowercase a./b./c./d. option extraction
# Used by JEE Main 2025 (prepp.in style) and similar PDFs
# ─────────────────────────────────────────────────────────────
 
def _extract_options_lowercase(block: str) -> dict:
    """
    Extract lowercase a./b./c./d. style options (JEE Main 2025 prepp.in format).
    Maps a→A, b→B, c→C, d→D.
    Tier 1: line-anchored  \\na. text
    Tier 2: inline run     a. text b. text ...
    """
    options = {}
    letter_map = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E'}
 
    # Tier 1: line-anchored
    line_pattern = re.compile(
        r'(?:^|\n)\s*([a-e])\.\s+(.*?)(?=(?:^|\n)\s*[a-e]\.\s+|$)',
        re.MULTILINE | re.DOTALL
    )
    for m in line_pattern.finditer(block):
        letter = letter_map.get(m.group(1).lower())
        if letter:
            value = re.sub(r'\s+', ' ', m.group(2)).strip()
            if value:
                options[letter] = _clean_option_text(value)
 
    if len(options) >= 3:
        return options
 
    # Tier 2: inline run
    inline_pattern = re.compile(r'\b([a-e])\.\s+(.*?)(?=\b[a-e]\.\s+|$)', re.DOTALL)
    options2 = {}
    for m in inline_pattern.finditer(block):
        letter = letter_map.get(m.group(1).lower())
        if letter:
            value = re.sub(r'\s+', ' ', m.group(2)).strip()
            if 0 < len(value) <= 300:
                options2[letter] = _clean_option_text(value)
    if len(options2) >= 3:
        return options2
 
    return options

# ─────────────────────────────────────────────────────────────
# PATCHED: _detect_layout — v11
# Adds: lowercase option scoring, better (A)(B) counting
# ─────────────────────────────────────────────────────────────
 
def _detect_layout(text: str) -> str:
    """
    v14: Weighted multi-signal layout detection.
    Layouts:
    - "numeric_key"        : (1)(2)(3)(4) options + ANSWER KEY/KEYS table
    - "lettered_solutions" : A./B./C./D. or a./b./c./d. options + Solutions section
    - "lettered_inline"    : (A)(B)(C)(D) options inline
    """
    tail = text[-10000:]

    # ── Signal A: option format counts ───────────────────────────────────
    numeric_opts      = len(re.findall(r'(?:^|\n)\s*\([1-5]\)\s+\S', text, re.MULTILINE))
    letter_dot_opts   = len(re.findall(r'(?:^|\n)\s*[A-D]\.\s+\S',   text, re.MULTILINE))
    letter_paren_opts = len(re.findall(r'(?:^|\n)\s*\([A-D]\)\s+\S', text, re.MULTILINE))
    lowercase_opts    = len(re.findall(r'(?:^|\n)\s*[a-d]\.\s+\S',   text, re.MULTILINE))

    # ── Signal B: answer section format ──────────────────────────────────
    has_answer_key_heading  = bool(re.search(
        r'\bANSWER\s*KEYS?\b|\bAnswer\s*Key\s*(?:&|and)\s*Explanation',
        tail, re.IGNORECASE))
    has_solutions_heading   = bool(re.search(
        r'(?:^|\n)\s*Solutions?\s*$', tail, re.IGNORECASE | re.MULTILINE))
    has_numeric_key_entries = bool(re.search(
        r'\bQ?\s*\d{1,3}[\.\)]\s*\([1-5]\)', tail, re.MULTILINE))
    has_letter_key_entries  = bool(re.search(
        r'\bQ?\s*\d{1,3}[\.\)]\s*\([A-D]\)', tail, re.MULTILINE))
    has_grid_key = bool(re.search(
        r'\d{1,3}\.\s*\([1-5]\)\s+\d{1,3}\.\s*\([1-5]\)', tail))
    has_q_letter_solutions  = bool(re.search(
        r'(?:^|\n)\s*Q\d{1,3}\.\s*\([A-D]\)', tail, re.MULTILINE))
    # prepp.in "Answer Key & Explanation" uses plain "1. (B) explanation"
    has_plain_letter_key    = bool(re.search(
        r'(?:^|\n)\s*\d{1,3}\.\s*\([A-D]\)', tail, re.MULTILINE))

    # ── Signal C: structural headers ─────────────────────────────────────
    has_section_headers = bool(re.search(
        r'\b(Physics|Chemistry|Botany|Zoology|Biology|Mathematics)\s*'
        r'(?:\(Section\s*[AB]\))?',
        text, re.IGNORECASE))
    has_q_prefix = bool(re.search(r'(?:^|\n)\s*Q\.?\s*\d+', text, re.MULTILINE))

    # ── Scoring ───────────────────────────────────────────────────────────
    score_numeric    = 0
    score_lettered   = 0
    score_ltr_inline = 0

    score_numeric    += min(numeric_opts,      120)
    score_lettered   += min(letter_dot_opts,   120)
    score_ltr_inline += min(letter_paren_opts, 120)
    score_lettered   += min(lowercase_opts,    120)

    if has_answer_key_heading and has_numeric_key_entries:
        score_numeric    += 80
    if has_answer_key_heading and has_grid_key:
        score_numeric    += 60
    if has_solutions_heading and has_letter_key_entries:
        score_lettered   += 80
    if has_solutions_heading and has_q_letter_solutions:
        score_lettered   += 80
    # Key fix: prepp.in / "Answer Key & Explanation" with "1. (B)" entries
    if has_answer_key_heading and has_plain_letter_key and not has_numeric_key_entries:
        score_lettered   += 80
    if has_answer_key_heading and has_letter_key_entries and not has_numeric_key_entries:
        score_lettered   += 50
    if not has_numeric_key_entries:
        score_ltr_inline += min(letter_paren_opts // 2, 30)

    # Section headers are weak evidence — only boost lettered if already winning
    if has_section_headers and score_lettered > score_numeric:
        score_lettered   += 15
    # Q-prefix is slightly evidence for lettered but appears in both formats
    if has_q_prefix:
        score_lettered   += 5

    best = max(score_numeric, score_lettered, score_ltr_inline)
    if best == 0:
        return "numeric_key"
    # Numeric wins ties (more format-specific answer key)
    if best == score_lettered and score_lettered > score_numeric:
        return "lettered_solutions"
    if (best == score_ltr_inline
            and score_ltr_inline > score_numeric
            and score_ltr_inline > score_lettered):
        return "lettered_inline"
    return "numeric_key"


def _split_body_and_tail(text: str, layout: str):
    """
    Cut the raw text into (question_body_text, tail_text) so the
    question-splitter regex never runs over the answer key / solutions section.

    v14: extended candidate list to cover prepp.in / MathonGo / various publisher
    heading formats. When NO heading is found at all, fall back to the last 8 000
    chars as tail (better than returning empty and finding zero answers).
    """
    candidates = [
        # Most specific first — match before broader ones
        re.compile(r'\bAnswer\s*Key\s*(?:&|and)\s*Explanations?\b',   re.IGNORECASE),
        re.compile(r'\bAnswer\s*Keys?\s*(?:&|and)\s*Explanations?\b', re.IGNORECASE),
        re.compile(r'\bANSWER\s*KEYS?\b',                              re.IGNORECASE),
        re.compile(r'\bAnswers?\s*(?:and|&)\s*Explanations?\b',       re.IGNORECASE),
        re.compile(r'(?:^|\n)[ \t]*Solutions?(?:\s+and\s+Explanations?)?\s*(?::|$)',
                   re.IGNORECASE | re.MULTILINE),
    ]

    marker = None
    for pattern in candidates:
        m = pattern.search(text)
        if m and (marker is None or m.start() < marker.start()):
            marker = m

    if not marker:
        # Last-resort: scan the last 6 000 chars for a dense cluster of
        # "N. (Letter)" entries — that signals the start of an answer block.
        dense = re.search(
            r'(?:\d{1,3}[\.\)]\s*\(?[A-E1-5]\)?[\s,;\t]{1,8}){4,}',
            text[-6000:]
        )
        if dense:
            offset = max(0, len(text) - 6000 + dense.start())
            print("[PDF Import] Tail found via dense-answer-cluster heuristic.")
            return text[:offset], text[offset:]

        print("[PDF Import] WARNING: no answer-key/solutions heading found — "
              "using last 8 000 chars as tail so answer extraction still runs.")
        cutoff = max(0, len(text) - 8000)
        return text[:cutoff], text[cutoff:]

    return text[:marker.start()], text[marker.start():]


# ─────────────────────────────────────────────────────────────
# Subject / Section tagging (shared by all layouts)
# ─────────────────────────────────────────────────────────────

def _build_subject_section_map(body_text: str):
    """
    Scan body for 'Physics (Section A)' style headers and return sorted
    list of (char_offset, subject, section).
    Also detects bare subject headings like 'Chemistry (Section A)' and
    'Botany (Section B)'.
    """
    pattern = re.compile(
        r'\b(Physics|Chemistry|Botany|Zoology|Biology|Mathematics)\s*'
        r'(?:\(Section\s*([AB])\))?',
        re.IGNORECASE
    )
    markers = []
    for m in pattern.finditer(body_text):
        subj    = m.group(1).title()
        section = f"Section {m.group(2).upper()}" if m.group(2) else ""
        markers.append((m.start(), subj, section))
    markers.sort(key=lambda t: t[0])
    return markers


def _lookup_subject_section(markers, offset: int):
    subject, section = None, None
    for pos, subj, sec in markers:
        if pos <= offset:
            subject, section = subj, sec
        else:
            break
    return subject, section

DEFAULT_SUBJECT_BLOCK_ORDER = ["Physics", "Chemistry", "Mathematics"]


def _assign_subjects_by_block(questions: list, subject_names: list) -> bool:
    """
    Fallback used when the PDF has no in-text subject headers at all (e.g.
    older JEE Main papers that just print Q1...Q90 back-to-back with no
    'Physics (Section A)' style markers, so _build_subject_section_map()
    returned nothing). Splits the already-extracted question list into
    len(subject_names) equal contiguous blocks, in the given order, e.g.
    for 90 questions and ["Physics", "Chemistry", "Mathematics"]:
        Q1-30  -> Physics
        Q31-60 -> Chemistry
        Q61-90 -> Mathematics
    Uses each question's 0-based extraction position (q["index"]), not its
    printed question_number, so it's correct even if numbering isn't a
    clean 1..N run. Only touches questions that don't already have a
    subject, so it never overrides header-based detection. Returns True
    if anything was assigned.
    """
    if not subject_names or not questions:
        return False

    n = len(subject_names)

    # FIX (chapter-mapping): position in the extracted list drifts by one as soon
    # as ONE question fails to extract (e.g. JEE Main 2012 19-May: Q23 is missing,
    # so Q31 (Chemistry) got "Physics" and Q61 (Maths) got "Chemistry").  When
    # every question carries its printed number we split on that instead, using
    # the highest printed number as the paper length (90 even if only 89 came out).
    try:
        numbers = [int(q["question_number"]) for q in questions]
    except (KeyError, TypeError, ValueError):
        numbers = []
    if numbers and len(numbers) == len(questions):
        total = max(numbers)
        position = lambda q: int(q["question_number"]) - 1
    else:
        total = len(questions)
        position = lambda q: q["index"]

    if total < n:
        return False

    block_size = total / n
    assigned = False
    for q in questions:
        if q.get("subject"):
            continue
        block = min(int(max(position(q), 0) // block_size), n - 1)
        q["subject"] = subject_names[block]
        assigned = True
    return assigned


# ─────────────────────────────────────────────────────────────
# Graphical question detector
# ─────────────────────────────────────────────────────────────

def _is_graphical_question(stem: str, options: dict) -> bool:
    """
    Return True when options are likely images (not text), e.g. graph questions.
    Signals: stem mentions visual keywords AND option text is very short/empty.
    """
    visual_words = re.search(
        r'\b(graph|figure|plot|diagram|shown|sketch|curve|waveform|figure|circuit)\b',
        stem, re.IGNORECASE
    )
    all_options_short = all(
        len((options.get(l) or "").strip()) <= 8
        for l in ['A', 'B', 'C', 'D']
    )
    return bool(visual_words) and all_options_short


# ─────────────────────────────────────────────────────────────
# Noise removal
# ─────────────────────────────────────────────────────────────

_NOISE_LINE_RES = [
    re.compile(r"^\s*join the most relevant test series.*$",      re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*question paper\s*$",                         re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*previous year paper\s*$",                    re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*mock practice test\s*-?\s*\d*\s*$",         re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*time allowed\s*:.*$",                        re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*maximum marks\s*:.*$",                       re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Page\s*\d+\s*$",                            re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Join the Most Relevant Test Series.*$",      re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*https?://[^\s]+$",                           re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*mathon?go\s*$",                              re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*www\.prepp\.in\s*$",                         re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*MathonGo\s*$",                              re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*JEE Main Previous Year Paper\s*$",           re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*Your Personal Exams Guide\s*$",              re.IGNORECASE | re.MULTILINE),
    # ── NEW: cross-page running headers that break mid-question blocks ──
    # Matches "JEE Main 2024 (06 Apr)  JEE Main Previous Year Paper"
    # Also catches the "J EE Main..." variant where the PDF has a kerning gap
    re.compile(r"^\s*J?\s*EE\s+Main\s+\d{4}.*JEE\s+Main.*Paper\s*$", re.IGNORECASE | re.MULTILINE),
    # Matches "Question Paper    MathonGo" (the two-column sub-header line)
    re.compile(r"^\s*Question\s+Paper\s+MathonGo\s*$",            re.IGNORECASE | re.MULTILINE),
    # Matches "Question Paper" alone on a line (already present above but
    # the existing one requires it to be the ONLY thing on the line — keep both)
    # Matches standalone exam-name headers from other publishers:
    re.compile(r"^\s*NEET\s+\d{4}.*?(?:Paper|Shift).*$",          re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*JEE\s+(?:Main|Advanced)\s+\d{4}.*?(?:Paper|Shift|Set).*$",
                                                                   re.IGNORECASE | re.MULTILINE),
]


def _clean_pdf_noise(text: str) -> str:
    for pattern in _NOISE_LINE_RES:
        text = pattern.sub("", text)
    text = re.sub(r"[ \t]{4,}", "  ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _clean_question_stem(text: str) -> str:
    text = re.sub(r'^Q\.?\s*\d+[\.\)]\s*',    '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Question\s*\d+[\.\)]\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _clean_option_text(text: str) -> str:
    text = re.sub(r'(?:Ans(?:wer)?|Correct\s*Answer)\s*[:\-]?\s*\(?[A-E]\)?', '', text,
                  flags=re.IGNORECASE)
    text = re.sub(r'^Option\s+[A-E]\s*[-:]\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _strip_recurring_edge_lines(page_texts: list, edge_line_count: int = 3,
                                 min_repeat_count: int = 3) -> list:
    if len(page_texts) < 3:
        return page_texts

    edge_counts     = Counter()
    page_lines_list = []
    for text in page_texts:
        lines     = text.split("\n")
        page_lines_list.append(lines)
        edge_slice = lines[:edge_line_count] + lines[-edge_line_count:]
        seen_this_page = set()
        for line in edge_slice:
            norm = re.sub(r"\s+", " ", line).strip().lower()
            if len(norm) < 6 or norm in seen_this_page:
                continue
            seen_this_page.add(norm)
            edge_counts[norm] += 1

    noisy_lines = {norm for norm, count in edge_counts.items() if count >= min_repeat_count}
    if not noisy_lines:
        return page_texts

    cleaned = []
    for lines in page_lines_list:
        kept = []
        for i, line in enumerate(lines):
            norm     = re.sub(r"\s+", " ", line).strip().lower()
            is_edge  = i < edge_line_count or i >= len(lines) - edge_line_count
            if is_edge and norm in noisy_lines:
                continue
            kept.append(line)
        cleaned.append("\n".join(kept))
    return cleaned

# ─────────────────────────────────────────────────────────────
# PATCHED: question_pattern — shared improved regex
# Handles: 1. / Q1. / Q.1 / 1) formats
# Used inside _extract_question_with_options_* functions
# ─────────────────────────────────────────────────────────────
 
_QUESTION_PATTERN = re.compile(
    r'(?:^|\n)\s*'
    r'(?:Q\.?\s*)?'                      # optional Q or Q. prefix
    r'(\d{1,3})'                          # question number
    r'[\.\)](?!\d)\s*'                    # . or ) not followed by digit
    r'([^\n]*(?:\n(?!\s*(?:Q\.?\s*)?\d{1,3}[\.\)](?!\d))[^\n]*)*)',
    re.DOTALL | re.IGNORECASE
)

# ─────────────────────────────────────────────────────────────
# PATCHED: _find_option_start_lettered — v11
# Now also detects (A) style option starts, not just A.
# ─────────────────────────────────────────────────────────────
 
def _find_option_start_lettered(content: str) -> int | None:
    """
    v11: Find where options begin, detecting both:
    - 'A. text' style (NEET Physics, NEET Botany)
    - '(A) text' style (NEET Chemistry)
    - 'a. text' style (JEE Main 2025)
    """
    # Try uppercase A. style
    for m in re.finditer(r'(?:^|\n)\s*([A-D])\.\s+\S', content, re.MULTILINE):
        if m.group(1) != 'A':
            continue
        pre = content[:m.start()].strip()
        if len(pre) < 20:
            continue
        remaining = content[m.start():]
        letters_found = set(re.findall(r'(?:^|\n)\s*([A-D])\.\s+\S', remaining, re.MULTILINE))
        if len(letters_found) >= 3:
            return m.start()
 
    # Try (A) style
    for m in re.finditer(r'(?:^|\n)?\s*\(([A-D])\)\s+\S', content, re.MULTILINE):
        if m.group(1) != 'A':
            continue
        pre = content[:m.start()].strip()
        if len(pre) < 15:
            continue
        remaining = content[m.start():]
        letters_found = set(re.findall(r'\(([A-D])\)\s+\S', remaining))
        if len(letters_found) >= 3:
            return m.start()
 
    # Try lowercase a. style
    for m in re.finditer(r'(?:^|\n)\s*([a-d])\.\s+\S', content, re.MULTILINE):
        if m.group(1) != 'a':
            continue
        pre = content[:m.start()].strip()
        if len(pre) < 15:
            continue
        remaining = content[m.start():]
        letters_found = set(re.findall(r'(?:^|\n)\s*([a-d])\.\s+\S', remaining, re.MULTILINE))
        if len(letters_found) >= 3:
            return m.start()
 
    return None


# ─────────────────────────────────────────────────────────────
# PATCHED: _extract_options_lettered — v11
# Adds: Tier 0 lowercase, better (A)(B) fallback
# ─────────────────────────────────────────────────────────────
 
def _extract_options_lettered(block: str) -> dict:
    """
    v11: Extract options with 4-tier fallback.
    Tier 0: lowercase a./b./c./d.  (JEE Main 2025 prepp.in)
    Tier 1: line-anchored A. text  (NEET Physics style)
    Tier 2: parenthesised (A) text (NEET Chemistry style)
    Tier 3: inline run A. text B. text ...
    """
    options = {}
 
    # ── Tier 0: lowercase ────────────────────────────────────────────────
    lc = _extract_options_lowercase(block)
    if len(lc) >= 4:
        return lc
 
    # ── Tier 1: line-anchored uppercase A. ──────────────────────────────
    line_pattern = re.compile(
        r'(?:^|\n)\s*([A-D])\.\s+'
        r'(.*?)(?=(?:^|\n)\s*[A-D]\.\s+|$)',
        re.MULTILINE | re.DOTALL
    )
    for m in line_pattern.finditer(block):
        letter = m.group(1).upper()
        value  = re.sub(r'\s+', ' ', m.group(2)).strip()
        if value:
            options[letter] = _clean_option_text(value)
    if len(options) >= 4:
        return options
 
    # ── Tier 2: parenthesised (A)/(B)/(C)/(D) ───────────────────────────
    # Handles NEET Chemistry style: "(A) text (B) text" or each on own line
    paren_pattern = re.compile(
        r'(?:^|\n)?\s*\(([A-D])\)\s+(.*?)(?=(?:^|\n)?\s*\([A-D]\)|$)',
        re.DOTALL
    )
    options2 = {}
    for m in paren_pattern.finditer(block):
        letter = m.group(1).upper()
        value  = re.sub(r'\s+', ' ', m.group(2)).strip()
        if value and len(value) <= 400:
            options2[letter] = _clean_option_text(value)
    if len(options2) >= 3:
        # Merge with tier 1 if we got partial
        merged = {**options2, **options}
        if len(merged) >= 3:
            return merged
        return options2
 
    # ── Tier 3: inline run ───────────────────────────────────────────────
    inline_pattern = re.compile(r'\b([A-D])\.\s+(.*?)(?=\b[A-D]\.\s+|$)', re.DOTALL)
    options3 = {}
    for m in inline_pattern.finditer(block):
        letter = m.group(1).upper()
        value  = re.sub(r'\s+', ' ', m.group(2)).strip()
        if len(value) > 250:
            continue
        if value:
            options3[letter] = _clean_option_text(value)
    if len(options3) >= 3:
        return options3
 
    # Return best we have
    return options if len(options) >= len(options2) else options2


# ─────────────────────────────────────────────────────────────
# PATCHED: _extract_answer_and_solutions_lettered — v11
# Fixes: handles "Q1. (A)" prefix in Solutions sections
# ─────────────────────────────────────────────────────────────
 
def _extract_answer_and_solutions_lettered(tail_text: str):
    """
    v14: Extract answer key for lettered-option PDFs (NEET / prepp.in / MathonGo style).

    Three progressively looser patterns are tried; the one with the most
    A–D matches wins.  If tail_text is empty (heading not found upstream)
    we return empty dicts immediately — the caller must ensure tail is non-empty
    (fixed in _split_body_and_tail v14).

    Formats handled:
      "1. (B) explanation"       strict
      "Q1. (B) explanation"      Q-prefix
      "1. (A)"                   no explanation
      "1. B explanation"         bare letter
      "1. B"                     bare letter, no explanation
    """
    answer_key_map: dict = {}
    solutions_map:  dict = {}

    if not tail_text:
        return answer_key_map, solutions_map

    # Pattern 1 (strict): "Q?N. (Letter) ..."
    # Uses (?:^|\n|\s) instead of just (?:^|\n) to survive mid-line occurrences.
    strict_pattern = re.compile(
        r'(?:^|\n|\s)Q?\s*(\d{1,3})[\.\)]\s*\(([A-D])\)\s*'
        r'([^\n]*(?:\n(?!\s*Q?\s*\d{1,3}[\.\)]\s*\([A-D]\))[^\n]*)*)',
        re.MULTILINE
    )

    # Pattern 2 (loose): tolerates colons, dashes, em-dashes between N and (Letter)
    loose_pattern = re.compile(
        r'(?:^|\n|\s)Q?\s*(\d{1,3})[\.\)]\s*[:\-—]?\s*\(([A-D])\)\s*'
        r'([^\n]*(?:\n(?!\s*Q?\s*\d{1,3}[\.\)]\s*[:\-—]?\s*\([A-D]\))[^\n]*)*)',
        re.MULTILINE
    )

    # Pattern 3 (bare): "1. B explanation" — letter without parens
    bare_pattern = re.compile(
        r'(?:^|\n|\s)Q?\s*(\d{1,3})[\.\)]\s+([A-D])(?=[\s\.\):,]|$)\s*'
        r'([^\n]*(?:\n(?!\s*Q?\s*\d{1,3}[\.\)]\s+[A-D](?:[\s\.\):,]|$))[^\n]*)*)',
        re.MULTILINE
    )

    best_map, best_solutions, best_count = {}, {}, -1
    for pattern in (strict_pattern, loose_pattern, bare_pattern):
        cmap = {}
        csol = {}
        for m in pattern.finditer(tail_text):
            q_no   = int(m.group(1))
            letter = m.group(2).upper()
            # group(3) may not exist in all pattern variants
            explanation = re.sub(r'\s+', ' ', m.group(3)).strip() if m.lastindex >= 3 else ""
            if letter in _ALLOWED_CORRECT_SET:
                cmap[q_no] = letter
            if explanation:
                csol[q_no] = explanation
        if len(cmap) > best_count:
            best_map, best_solutions, best_count = cmap, csol, len(cmap)

    answer_key_map, solutions_map = best_map, best_solutions

    # Safety net: if all three patterns found nothing, scan for ANY
    # "N. (Letter)" or "N. Letter" anywhere in tail — sacrifices solution
    # text quality but guarantees correct_answer populates.
    if not answer_key_map:
        for m in re.finditer(r'\b(\d{1,3})\s*[\.\)]\s*\(?\s*([A-D])\s*\)?', tail_text):
            q_no, letter = int(m.group(1)), m.group(2).upper()
            if letter in _ALLOWED_CORRECT_SET and q_no not in answer_key_map:
                answer_key_map[q_no] = letter

    print(f"[PDF Import] Lettered answer extraction: {len(answer_key_map)} entries "
          f"(best pattern count={best_count})")
    return answer_key_map, solutions_map



# ─────────────────────────────────────────────────────────────
# PATCHED: _extract_question_with_options_lettered — v11
# Uses improved question pattern + better option extraction
# ─────────────────────────────────────────────────────────────
 
def _extract_question_with_options_lettered(text: str) -> list:
    """v14: Layout-B with reliable tail extraction and dual answer-key pass."""
    cleaned_text = _clean_pdf_noise(text)
    body_text, tail_text = _split_body_and_tail(cleaned_text, "lettered_solutions")

    answer_key_map, solutions_map = _extract_answer_and_solutions_lettered(tail_text)

    # Second pass: if lettered extraction came up short, try the numeric extractor
    # (handles PDFs that mix answer formats, e.g. "1.(2)" grid in lettered papers)
    if len(answer_key_map) < 3 and tail_text:
        numeric_map = _extract_answer_key_map(tail_text)
        for q_no, ans in numeric_map.items():
            if q_no not in answer_key_map:
                answer_key_map[q_no] = ans

    subject_markers = _build_subject_section_map(body_text)
 
    questions = []
    for i, match in enumerate(_QUESTION_PATTERN.finditer(body_text)):
        q_num   = int(match.group(1))
        content = match.group(2).strip()
        offset  = match.start()
 
        # Try all option styles in priority order
        options = _extract_options_lettered(content)
        if not options or len(options) < 2:
            options = _extract_options_lettered_inline(content)
 
        opt_start = _find_option_start_lettered(content)
        stem      = content[:opt_start].strip() if opt_start is not None else content.strip()
        stem      = _clean_question_stem(stem)
 
        correct_answer = answer_key_map.get(q_num, "")
        solution_text  = solutions_map.get(q_num, "")
        subject, section = _lookup_subject_section(subject_markers, offset)
 
        has_min_options  = all(options.get(l) for l in ['A', 'B', 'C', 'D'])
        has_answer       = correct_answer in _ALLOWED_CORRECT_SET
        has_some_options = any(options.get(l) for l in ['A', 'B', 'C', 'D'])
 
        if has_min_options and has_answer:
            status, reason = STATUS_VALID, ""
        elif has_min_options:
            status, reason = STATUS_NEEDS_REVIEW, "All options found but no correct answer detected."
        elif has_some_options:
            status, reason = STATUS_NEEDS_REVIEW, "Some options are missing. Please fill all options."
        else:
            status, reason = STATUS_NEEDS_REVIEW, "Fewer than 4 options detected."
 
        if _is_graphical_question(stem, options):
            status = STATUS_NEEDS_REVIEW
            reason = ("Options appear to be graphs/diagrams. "
                      "Please verify images were extracted and assign correct answer manually.")
 
        questions.append({
            "index":           i,
            "question_number": q_num,
            "subject":         subject,
            "section":         section,
            "question_text":   stem,
            "question_type":   QUESTION_TYPE_MCQ,
            "option_a":        options.get("A", ""),
            "option_b":        options.get("B", ""),
            "option_c":        options.get("C", ""),
            "option_d":        options.get("D", ""),
            "option_e":        "",
            "correct_answer":  correct_answer,
            "numerical_answer": "",
            "solution_text":   solution_text,
            "difficulty":      "Medium",
            "marks":           4,
            "negative_marks":  1,
            "status":          status,
            "status_reason":   reason,
            "images":          [],
            "option_images":   {"A": None, "B": None, "C": None, "D": None},
            "_raw_content":    content[:500] if len(content) > 500 else content,
        })
 
    return questions


# ─────────────────────────────────────────────────────────────
# Layout C: lettered "(A)(B)(C)(D)" inline options
# (JEE Advanced / some older papers)
# ─────────────────────────────────────────────────────────────

def _extract_options_lettered_inline(block: str) -> dict:
    """
    Extract options from (A)/(B)/(C)/(D) inline style, e.g.:
        (A) 2x  (B) 3x  (C) x  (D) 4x
    """
    options = {}
    pattern = re.compile(
        r'\(([A-D])\)\s+(.*?)(?=\([A-D]\)|$)',
        re.DOTALL
    )
    for m in pattern.finditer(block):
        letter = m.group(1).upper()
        value  = re.sub(r'\s+', ' ', m.group(2)).strip()
        if len(value) > 300:
            continue
        if value:
            options[letter] = _clean_option_text(value)
    return options


def _extract_question_with_options_lettered_inline(text: str) -> list:
    """
    Layout-C: (A)(B)(C)(D) style inline options.
    Answer key may be present as 'ANSWER KEY' table with letter entries.
    """
    cleaned_text = _clean_pdf_noise(text)
    body_text, tail_text = _split_body_and_tail(cleaned_text, "lettered_inline")

    answer_key_map = _extract_answer_key_map(tail_text if tail_text else cleaned_text)
    # Also try letter-style key
    if not answer_key_map:
        for m in re.finditer(r'\b(\d{1,3})\.\s*\(([A-D])\)', tail_text or cleaned_text[-5000:]):
            q_no = int(m.group(1))
            ans  = m.group(2).upper()
            if ans in ALLOWED_CORRECT:
                answer_key_map[q_no] = ans

    subject_markers = _build_subject_section_map(body_text)

    question_pattern = re.compile(
        r'(?:^|\n)\s*(?:Q\.?\s*)?(\d{1,3})[\.\)](?!\d)\s*'
        r'([^\n]*(?:\n(?!\s*(?:Q\.?\s*)?\d{1,3}[\.\)](?!\d))[^\n]*)*)',
        re.DOTALL | re.IGNORECASE
    )

    questions = []
    for i, match in enumerate(question_pattern.finditer(body_text)):
        q_num   = int(match.group(1))
        content = match.group(2).strip()
        offset  = match.start()

        options = _extract_options_lettered_inline(content)
        if len(options) < 2:
            # Fallback to bare A. style
            options = _extract_options_lettered(content)

        # Find stem
        opt_start = None
        first_paren_opt = re.search(r'\([A-D]\)\s+\S', content)
        if first_paren_opt:
            pre = content[:first_paren_opt.start()].strip()
            if len(pre) >= 15:
                opt_start = first_paren_opt.start()
        if opt_start is None:
            opt_start_alt = _find_option_start_lettered(content)
            if opt_start_alt is not None:
                opt_start = opt_start_alt

        stem = content[:opt_start].strip() if opt_start is not None else content.strip()
        stem = _clean_question_stem(stem)

        correct_answer   = answer_key_map.get(q_num, "")
        subject, section = _lookup_subject_section(subject_markers, offset)

        has_min_options  = all(options.get(l) for l in ['A', 'B', 'C', 'D'])
        has_answer       = correct_answer in ALLOWED_CORRECT
        has_some_options = any(options.get(l) for l in ['A', 'B', 'C', 'D'])

        if has_min_options and has_answer:
            status, reason = STATUS_VALID, ""
        elif has_min_options:
            status, reason = STATUS_NEEDS_REVIEW, "All options found but no correct answer detected."
        elif has_some_options:
            status, reason = STATUS_NEEDS_REVIEW, "Some options are missing."
        else:
            status, reason = STATUS_NEEDS_REVIEW, "Fewer than 4 options detected."

        if _is_graphical_question(stem, options):
            status = STATUS_NEEDS_REVIEW
            reason = ("Options appear to be graphs/diagrams. "
                      "Please verify images were extracted and assign correct answer manually.")

        questions.append({
            "index":           i,
            "question_number": q_num,
            "subject":         subject,
            "section":         section,
            "question_text":   stem,
            "question_type":   QUESTION_TYPE_MCQ,
            "option_a":        options.get("A", ""),
            "option_b":        options.get("B", ""),
            "option_c":        options.get("C", ""),
            "option_d":        options.get("D", ""),
            "option_e":        options.get("E", ""),
            "correct_answer":  correct_answer,
            "numerical_answer": "",
            "solution_text":   "",
            "difficulty":      "Medium",
            "marks":           4,
            "negative_marks":  1,
            "status":          status,
            "status_reason":   reason,
            "images":          [],
            "option_images":   {"A": None, "B": None, "C": None, "D": None},
            "_raw_content":    content[:500] if len(content) > 500 else content,
        })

    return questions


# ─────────────────────────────────────────────────────────────
# Layout A: numeric "(1)(2)(3)(4)" options + ANSWER KEY table
# (JEE Main style)
# ─────────────────────────────────────────────────────────────

def _find_option_sequence_start(content: str):
    """Return the char index where the real MCQ options begin, or None."""
    for pattern, ordered_values in (
        (re.compile(r'\(([1-5])\)'), ['1', '2', '3']),
        (re.compile(r'\(([A-E])\)'), ['A', 'B', 'C']),
    ):
        matches = list(pattern.finditer(content))
        values  = [m.group(1) for m in matches]
        for i in range(len(matches) - 2):
            if values[i:i + 3] == ordered_values:
                return matches[i].start()
    return None


def _extract_options_exact(block: str) -> dict:
    """
    Extract (1)(2)(3)(4) style options. Handles three layouts common in JEE Main PDFs:
    
    Layout A - options and values on same line (easy):
        (1) 0.2 mA   (2) 0.02 mA
        (3) 0.5 mA   (4) 0.05 mA
    
    Layout B - value appears on next line(s) after the marker (fraction/math heavy):
        2g        g
        (1)      (2)
        3         2
        (3) 5g   (4) g
    
    Layout C - long text options in 2-col, (2)&(4) inline after (1)&(3) text:
        (1) Angular momentum is conserved  (2) Angular momentum changes...
        (3) Angular momentum changes...    (4) Angular momentum changes...
    """
    options = {}

    # ── Pass 1: Standard inline extraction ───────────────────────────────
    # Handles Layout A and Layout C's (1)/(3) correctly.
    # Pattern: (N) followed by text until next (N) or end
    std_pattern = re.compile(
        r'\(([1-5])\)\s*(.*?)(?=\s*\([1-5]\)\s|\s*$)',
        re.DOTALL
    )
    for m in std_pattern.finditer(block):
        num = int(m.group(1))
        if 1 <= num <= 5:
            letter = _OPTION_LETTERS[num - 1]
            value  = re.sub(r'\s+', ' ', m.group(2)).strip()
            if value:
                options[letter] = _clean_option_text(value)

    if len(options) >= 4:
        return options

    # ── Pass 2: Two-column same-line "(2)"/"(4)" inline capture ──────────
    # Handles Layout C: "(1) Some text (2) Other text" on one line.
    # Split each line on the option marker pattern first.
    options2 = {}
    line_split_re = re.compile(r'\(([1-5])\)\s*')
    for line in block.split('\n'):
        parts = line_split_re.split(line)
        # parts looks like: ['prefix', '1', 'text1', '2', 'text2', ...]
        i = 1
        while i < len(parts) - 1:
            try:
                num = int(parts[i])
                text = parts[i + 1].strip()
                if 1 <= num <= 5 and text:
                    letter = _OPTION_LETTERS[num - 1]
                    options2[letter] = _clean_option_text(text)
            except (ValueError, IndexError):
                pass
            i += 2

    if len(options2) >= 4:
        return options2

    # ── Pass 3: Layout B — value on NEXT LINE after marker ───────────────
    # Handles the math-fraction case:
    #   "2g  g\n(1)  (2)\n3    2\n(3) 5g  (4) g\n6"
    # Strategy: find all (N) marker positions, then for each collect text
    # from that position forward until the next marker or end.
    options3 = {}
    marker_re = re.compile(r'\(([1-5])\)')
    markers = [(m.start(), m.end(), int(m.group(1))) for m in marker_re.finditer(block)]
    for idx, (start, end, num) in enumerate(markers):
        if not (1 <= num <= 5):
            continue
        # Text runs from after this marker to start of next marker
        next_start = markers[idx + 1][0] if idx + 1 < len(markers) else len(block)
        raw = block[end:next_start]
        # Strip text that came BEFORE this marker on the same line
        # (those are the values for the previous column, e.g. "g" before "(2)")
        # We want text AFTER the marker, possibly on the next line(s)
        # Heuristic: if the marker is followed immediately by whitespace then newline,
        # the value is on the next line.
        value = re.sub(r'\s+', ' ', raw).strip()
        if value and len(value) < 200:
            letter = _OPTION_LETTERS[num - 1]
            options3[letter] = _clean_option_text(value)

    # But Layout B has PRECEDING text on the same line as the marker (other column's value).
    # A better approach for Layout B: look at lines containing ONLY markers (no value text),
    # then pick up the value from the next line.
    if len(options3) < 4:
        options3 = _extract_options_split_line(block)

    if len(options3) >= 2:
        # Merge with what pass 1/2 found
        merged = {**options3, **options}
        if len(merged) >= 4:
            return merged
        return options3 if len(options3) > len(options) else options

    # ── Fallback: letter-style A./B./C./D. ───────────────────────────────
    opts_letter = _extract_options_lettered(block)
    if len(opts_letter) >= 3:
        return opts_letter

    return options


def _extract_options_split_line(block: str) -> dict:
    """
    Handle Layout B: markers and values on different lines in a 2-col grid.
    
    Example text after extract_text:
        "2g g\n(1) (2)\n3 2\n(3) 5g (4) g\n6"
    
    Strategy: find lines that contain ONLY option markers (no substantive text after),
    then the VALUES are on the preceding or following lines.
    
    More robust: collect all (N) markers with their positions, then for each
    collect the non-marker, non-empty tokens that appear between this marker
    and the next in reading order (across lines).
    """
    options = {}
    
    # Tokenize: split into (marker, position) and (text, position) tokens
    marker_re = re.compile(r'\(([1-5])\)')
    all_markers = [(m.start(), int(m.group(1)), m.end()) for m in marker_re.finditer(block)]
    
    if len(all_markers) < 3:
        return {}
    
    for idx, (mstart, num, mend) in enumerate(all_markers):
        if not (1 <= num <= 5):
            continue
        next_mstart = all_markers[idx + 1][0] if idx + 1 < len(all_markers) else len(block)
        segment = block[mend:next_mstart]
        
        # Remove text that appears before a newline on the same line as the marker
        # (that text belongs to the previous column, e.g. "g" before "(2)")
        # Keep only text that is clearly the value: after a newline or if on same line
        # and there's real content (not just the other column's leftover).
        
        # Simple approach: strip everything up to the first newline if the marker
        # is followed by whitespace-only on the same line (Layout B marker-only line)
        same_line_text = re.match(r'[^\n]*', segment).group(0).strip()
        if same_line_text:
            # Marker has text on same line → that's the value (Layout A/C)
            value = re.sub(r'\s+', ' ', segment).strip()
        else:
            # Marker line is empty → value is on next line(s) (Layout B)
            rest = segment.lstrip('\n')
            value = re.sub(r'\s+', ' ', rest).strip()
        
        if value and len(value) < 200:
            letter = _OPTION_LETTERS[num - 1]
            options[letter] = _clean_option_text(value)
    
    return options


# ─────────────────────────────────────────────────────────────
# PATCHED: _extract_answer_key_map — v11
# Fixes: Q-prefix in answer key entries ("Q1. (B)")
# ─────────────────────────────────────────────────────────────

_ALLOWED_CORRECT_SET = {"A", "B", "C", "D", "E"}
 
def _extract_answer_key_map(text: str) -> dict:
    """
    v14: Extract answer key for numeric-option PDFs (JEE Main / MathonGo style).

    Supports all common formats:
      A) "1. (2)"   — number index → letter
      B) "1. (B)"   — letter in parens
      C) "1. B"     — bare letter
      D) Grid       — "1.(2)  2.(4)  3.(1)" same line
      E) Q-prefix   — "Q1. (3)"
      F) prepp.in   — "1. (B)  ΔP/P% = ..." (solution-style entry)

    Searches the whole document (not just the last N chars) so answer keys
    near the middle of the PDF are still found.
    """
    answer_key_map: dict = {}

    # ── Step 1: locate the answer section ────────────────────────────────
    key_section_match = re.search(
        r'(?:ANSWER\s*KEYS?|Answer\s*Key\s*(?:&|and)\s*Explanation'
        r'|Answers?\s*(?:&|and)\s*Explanation|ANSWERS|Solutions?)\s*[:\n]?',
        text, re.IGNORECASE
    )
    if key_section_match:
        answer_section = text[key_section_match.start():]
    else:
        # No heading found — use last 12 000 chars
        answer_section = text[-12000:]

    # ── Step 2: Pattern A — numeric index "(N)" → letter ─────────────────
    for m in re.finditer(r'\bQ?\s*(\d{1,3})[\.\)]\s*\(([1-5])\)', answer_section):
        q_no = int(m.group(1))
        opt  = int(m.group(2))
        if 1 <= opt <= 5:
            answer_key_map[q_no] = _OPTION_LETTERS[opt - 1]

    if len(answer_key_map) >= 3:
        return answer_key_map

    # ── Step 3: Pattern B — letter in parens "(A)" ────────────────────────
    for m in re.finditer(r'\bQ?\s*(\d{1,3})[\.\)]\s*\(([A-E])\)', answer_section):
        q_no = int(m.group(1))
        ans  = m.group(2).upper()
        if ans in _ALLOWED_CORRECT_SET and q_no not in answer_key_map:
            answer_key_map[q_no] = ans

    if len(answer_key_map) >= 3:
        return answer_key_map

    # ── Step 4: Pattern C — bare letter ──────────────────────────────────
    for m in re.finditer(
        r'(?:^|\s)Q?\s*(\d{1,3})[\.\)]\s+([A-E])(?=[\s\.\):,]|$)',
        answer_section, re.MULTILINE
    ):
        q_no = int(m.group(1))
        ans  = m.group(2).upper()
        if ans in _ALLOWED_CORRECT_SET and q_no not in answer_key_map:
            answer_key_map[q_no] = ans

    if len(answer_key_map) >= 3:
        return answer_key_map

    # ── Step 5: relaxed full-doc scan (last 15 000 chars) ────────────────
    for m in re.finditer(r'\b(\d{1,3})\s*[\.\)]\s*\(?\s*([A-E1-5])\s*\)?',
                         text[-15000:]):
        q_no = int(m.group(1))
        raw  = m.group(2)
        if raw.isdigit():
            idx = int(raw)
            ans = _OPTION_LETTERS[idx - 1] if 1 <= idx <= 5 else None
        else:
            ans = raw.upper() if raw.upper() in _ALLOWED_CORRECT_SET else None
        if ans and q_no not in answer_key_map:
            answer_key_map[q_no] = ans

    return answer_key_map


# ─────────────────────────────────────────────────────────────
# PATCHED: _extract_question_with_options_numeric — v11
# Uses improved question pattern
# ─────────────────────────────────────────────────────────────
 
def _extract_question_with_options_numeric(text: str) -> list:
    """v14: Layout-A with dual answer-key extraction (numeric + lettered fallback)."""
    cleaned_text = _clean_pdf_noise(text)

    # Primary: numeric index answer key
    answer_key_map = _extract_answer_key_map(cleaned_text)

    # Secondary: lettered answer key extracted from the tail section.
    # This covers prepp.in / MathonGo PDFs that print answers as "1. (B) explanation"
    # in an "Answer Key & Explanation" section — _extract_answer_key_map Pattern B
    # should already get these, but running the lettered extractor fills any gaps.
    _, tail_text = _split_body_and_tail(cleaned_text, "numeric_key")
    if tail_text:
        letter_map, _ = _extract_answer_and_solutions_lettered(tail_text)
        for q_no, ans in letter_map.items():
            if q_no not in answer_key_map:
                answer_key_map[q_no] = ans

    # Use tail boundary as the question source so Q-numbers inside the answer
    # key section don't get parsed as duplicate questions.
    if tail_text:
        questions_source_text = cleaned_text[:len(cleaned_text) - len(tail_text)]
    else:
        answer_key_heading = re.search(
            r'\bANSWER\s*KEYS?\b|\bAnswer\s*Key\b', cleaned_text, re.IGNORECASE)
        questions_source_text = (
            cleaned_text[:answer_key_heading.start()]
            if answer_key_heading else cleaned_text
        )

    subject_markers = _build_subject_section_map(questions_source_text)
 
    questions = []
    for i, match in enumerate(_QUESTION_PATTERN.finditer(questions_source_text)):
        q_num   = int(match.group(1))
        content = match.group(2).strip()
        offset  = match.start()
 
        # Try numeric first, then lowercase, then lettered
        options = _extract_options_exact(content)
        if len(options) < 2:
            options = _extract_options_lowercase(content)
        if len(options) < 2:
            options = _extract_options_lettered(content)
 
        opt_start = _find_option_sequence_start(content)
        if opt_start is None:
            opt_start = _find_option_start_lettered(content)
        if opt_start is None:
            for pattern in [r'\(\d\)', r'\([A-E]\)', r'[A-E]\)', r'[A-E]\.', r'[a-e]\.']:
                opt_match = re.search(pattern, content)
                if opt_match:
                    opt_start = opt_match.start()
                    break
 
        stem = content[:opt_start].strip() if opt_start else content.strip()
        stem = _clean_question_stem(stem)
 
        if len(stem) < 10:
            lines = content.split('\n')
            stem_lines = []
            for line in lines:
                if re.search(r'\([1-5]\)|\([A-E]\)|[A-E][\.\)]|[a-e]\.', line):
                    break
                stem_lines.append(line)
            stem = ' '.join(stem_lines).strip()
            stem = _clean_question_stem(stem)
 
        correct_answer = answer_key_map.get(q_num, "")
        if not correct_answer:
            ans_match = re.search(
                r'(?:Ans(?:wer)?|Correct\s*Answer)\s*[:\-]?\s*\(?([A-E])\)?',
                content, re.IGNORECASE
            )
            correct_answer = ans_match.group(1).upper() if ans_match else ""
 
        subject, section = _lookup_subject_section(subject_markers, offset)
 
        has_min_options  = all(options.get(l) for l in ['A', 'B', 'C', 'D'])
        has_answer       = correct_answer in _ALLOWED_CORRECT_SET
        has_some_options = any(options.get(l) for l in ['A', 'B', 'C', 'D'])
 
        if has_min_options and has_answer:
            status, reason = STATUS_VALID, ""
        elif has_min_options:
            status, reason = STATUS_NEEDS_REVIEW, "All options found but no correct answer detected."
        elif has_some_options:
            status, reason = STATUS_NEEDS_REVIEW, "Some options are missing. Please fill all options."
        else:
            status, reason = STATUS_NEEDS_REVIEW, "Fewer than 4 options detected."
 
        if _is_graphical_question(stem, options):
            status = STATUS_NEEDS_REVIEW
            reason = ("Options appear to be graphs/diagrams. "
                      "Please verify images were extracted and assign correct answer manually.")
 
        questions.append({
            "index":           i,
            "question_number": q_num,
            "subject":         subject,
            "section":         section,
            "question_text":   stem,
            "question_type":   QUESTION_TYPE_MCQ,
            "option_a":        options.get("A", ""),
            "option_b":        options.get("B", ""),
            "option_c":        options.get("C", ""),
            "option_d":        options.get("D", ""),
            "option_e":        options.get("E", ""),
            "correct_answer":  correct_answer,
            "numerical_answer": "",
            "solution_text":   "",
            "difficulty":      "Medium",
            "marks":           4,
            "negative_marks":  1,
            "status":          status,
            "status_reason":   reason,
            "images":          [],
            "option_images":   {"A": None, "B": None, "C": None, "D": None},
            "_raw_content":    content[:500] if len(content) > 500 else content,
        })
 
    return questions


# ─────────────────────────────────────────────────────────────
# Master dispatcher
# ─────────────────────────────────────────────────────────────

def _dedupe_duplicate_question_numbers(questions: list) -> list:
    """
    v10 FIX: occasionally a corrupted stretch of text (e.g. a fraction-bar
    false positive splicing garbage into a stem) makes the question regex
    fire twice for what is really one printed question, producing two
    dict entries with the same question_number — one usually a near-empty
    fragment. Keeps, per question_number, the entry with the most
    populated content (options filled + longer stem) and drops the rest,
    then re-indexes survivors' "index" field to stay contiguous 0..N-1,
    since other code (diagram matching, the v10 subject-block fallback)
    assumes "index" is a tight, ordered sequence matching list position.
    """
    def _richness(q):
        opts_filled = sum(1 for l in ("A", "B", "C", "D") if q.get(f"option_{l.lower()}"))
        return (opts_filled, len(q.get("question_text") or ""))

    best_by_number = {}
    for q in questions:
        qnum = q.get("question_number")
        if qnum is None:
            best_by_number[id(q)] = q
            continue
        current = best_by_number.get(qnum)
        if current is None or _richness(q) > _richness(current):
            best_by_number[qnum] = q

    deduped = list(best_by_number.values())
    deduped.sort(key=lambda q: q.get("question_number") or 0)
    for i, q in enumerate(deduped):
        q["index"] = i
    return deduped


def _extract_question_with_options(text: str) -> list:
    """
    Detect PDF layout and route to the correct parser.
    Layouts:
      - numeric_key        → JEE Main (1)(2)(3)(4) + ANSWER KEYS table
      - lettered_solutions → NEET A./B./C./D. + Solutions section
      - lettered_inline    → JEE Advanced (A)(B)(C)(D) inline
    """
    layout = _detect_layout(text)
    print(f"[PDF Import] Detected layout: {layout}")

    if layout == "lettered_solutions":
        questions = _extract_question_with_options_lettered(text)
    elif layout == "lettered_inline":
        questions = _extract_question_with_options_lettered_inline(text)
    else:
        questions = _extract_question_with_options_numeric(text)

    return _dedupe_duplicate_question_numbers(questions)


# ─────────────────────────────────────────────────────────────
# Helper Functions for Question Formatting
# ─────────────────────────────────────────────────────────────

def _summary_counts(questions: list) -> dict:
    total        = len(questions)
    valid        = sum(1 for q in questions if q["status"] == STATUS_VALID)
    needs_review = sum(1 for q in questions if q["status"] == STATUS_NEEDS_REVIEW)
    failed       = sum(1 for q in questions if q["status"] == STATUS_FAILED)
    return {
        "totalExtracted": total, "valid": valid, "needsReview": needs_review, "failed": failed,
        # how many questions were already pushed to a Practice / Custom test
        "addedPractice":  sum(1 for q in questions if "practice" in (q.get("added_to") or [])),
        "addedCustom":    sum(1 for q in questions if "custom"   in (q.get("added_to") or [])),
    }


def _question_full(q: dict, request=None) -> dict:
    def _absolutize(url): return url or None

    images = q.get('images', [])
    if not isinstance(images, list): images = []
    images = [_absolutize(u) for u in images]

    option_images = q.get('option_images', {})
    if not isinstance(option_images, dict): option_images = {}
    normalized_option_images = {
        "A": _absolutize(option_images.get("A") or option_images.get("a")),
        "B": _absolutize(option_images.get("B") or option_images.get("b")),
        "C": _absolutize(option_images.get("C") or option_images.get("c")),
        "D": _absolutize(option_images.get("D") or option_images.get("d")),
    }

    return {
        'index':           q.get('index'),
        'questionNumber':  q.get('question_number'),
        'subject':         q.get('subject'),
        'section':         q.get('section'),
        'question_text':   q.get('question_text', ''),
        'question_type':   q.get('question_type', 'MCQ'),
        'option_a':        q.get('option_a', ''),
        'option_b':        q.get('option_b', ''),
        'option_c':        q.get('option_c', ''),
        'option_d':        q.get('option_d', ''),
        'option_e':        q.get('option_e', ''),
        'options': {
            'A': q.get('option_a', ''),
            'B': q.get('option_b', ''),
            'C': q.get('option_c', ''),
            'D': q.get('option_d', ''),
            'E': q.get('option_e', ''),
        },
        'correct_answer':   q.get('correct_answer', ''),
        'numerical_answer': q.get('numerical_answer', ''),
        'solution_text':    q.get('solution_text', ''),
        'difficulty':       q.get('difficulty', 'Medium'),
        'marks':            q.get('marks', 4),
        'negative_marks':   q.get('negative_marks', 1),
        'status':           q.get('status', 'needs_review'),
        'status_reason':    q.get('status_reason', ''),
        'images':           images,
        'option_images':    normalized_option_images,
        '_raw':             q.get('_raw_content', ''),
        # chapter auto-mapping (see _auto_map_questions)
        'chapter_id':         q.get('chapter_id'),
        'chapter_name':       q.get('chapter_name'),
        'topic':              q.get('topic'),
        'mapping_confidence': q.get('mapping_confidence', 0),
        'mapping_status':     q.get('mapping_status', 'unmapped'),
        'mapping_source':     q.get('mapping_source'),
        'matched_keywords':   q.get('matched_keywords', []),
        'runner_up':          q.get('runner_up'),
        'added_to':           q.get('added_to', []),
        # master-question / occurrence info (see _annotate_duplicates)
        'duplicate':          q.get('duplicate'),
        'duplicate_action':   q.get('duplicate_action', 'auto'),
        'extra_chapter_ids':  q.get('extra_chapter_ids', []),
        'concepts':           q.get('concepts', []),
        'source_chapter_name': q.get('source_chapter_name', ''),
    }


def _question_preview(q: dict) -> dict:
    return {
        "index":         q["index"],
        "questionNumber": q.get("question_number"),
        "subject":       q.get("subject"),
        "section":       q.get("section"),
        "preview":       (q["question_text"][:120] + "…") if len(q["question_text"]) > 120
                         else q["question_text"],
        "question_type": q["question_type"],
        "status":        q["status"],
        "status_reason": q.get("status_reason", ""),
        "chapter_id":         q.get("chapter_id"),
        "chapter_name":       q.get("chapter_name"),
        "topic":              q.get("topic"),
        "mapping_confidence": q.get("mapping_confidence", 0),
        "mapping_status":     q.get("mapping_status", "unmapped"),
        "added_to":           q.get("added_to", []),   # ["practice", "custom"]
        "duplicate_type":     (q.get("duplicate") or {}).get("match_type"),  # exact / near_duplicate / None
    }


# ─────────────────────────────────────────────────────────────
# Storage and Cache Functions
# ─────────────────────────────────────────────────────────────

def _persist(upload_id: str, data: dict) -> None:
    cache.set(_cache_key(upload_id), data, timeout=PYQ_CACHE_TTL)
    try:
        with open(_storage_path(upload_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _get_cached_or_404(upload_id: str):
    data = cache.get(_cache_key(upload_id))
    if data:
        return data
    path = _storage_path(upload_id)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cache.set(_cache_key(upload_id), data, timeout=PYQ_CACHE_TTL)
            return data
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _delete_storage(upload_id: str) -> None:
    cache.delete(_cache_key(upload_id))
    try:
        _storage_path(upload_id).unlink(missing_ok=True)
    except OSError:
        pass


def _cache_key(upload_id: str) -> str:
    return f"{PYQ_CACHE_PREFIX}{upload_id}"


def _storage_path(upload_id: str) -> Path:
    return PYQ_STORAGE_DIR / f"{upload_id}.json"


_MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def _guess_from_filename(file_name: str) -> dict:
    """
    Pull Year / Session out of names like
        JEE_Main_2018_(15_Apr)_Previous_Year_Paper.pdf  ->  2018, "15 Apr"
        NEET_2021_Shift_2.pdf                            ->  2021, "Shift 2"
    """
    stem = Path(file_name or "").stem
    year = None
    m = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", stem)
    if m:
        year = int(m.group(1))

    session = ""
    m = re.search(r"shift[\s_\-:]*(\d)", stem, re.IGNORECASE)
    if m:
        session = f"Shift {m.group(1)}"
    else:
        m = re.search(r"(?<!\d)(\d{1,2})[\s_\-]*(" + "|".join(_MONTHS) + r")[a-z]*", stem, re.IGNORECASE)
        if m:
            session = f"{int(m.group(1))} {m.group(2).title()}"
    return {"year": year, "session": session}


def _guess_paper_details(text: str, exam: "Exam", file_name: str = "") -> dict:
    head        = text[:1500]
    from_name   = _guess_from_filename(file_name)

    # The file name is usually the most reliable source (headers often carry
    # copyright years etc.), so it wins; the PDF header is the fallback.
    year_match  = re.search(r"\b(19|20)\d{2}\b", head)
    exam_year   = from_name["year"] or (int(year_match.group(0)) if year_match else None)

    session = ""
    session_match = re.search(r"Shift\s*[-:]?\s*(\d)", head, re.IGNORECASE)
    if session_match:
        session = f"Shift {session_match.group(1)}"
    session = session or from_name["session"]

    exam_subjects   = list(Subject.objects.filter(exam=exam))
    matched_subjects = [
        subj for subj in exam_subjects
        if re.search(rf"\b{re.escape(subj.subject_name)}\b", head, re.IGNORECASE)
    ]
    subjects = matched_subjects or exam_subjects

    return {
        "exam_id":         exam.exam_id,
        "exam_name":       exam.exam_name,
        "exam_year":       exam_year,
        "pyq_session":     session,
        "subject_ids":     [s.subject_id   for s in subjects],
        "subject_names":   [s.subject_name for s in subjects],
        "difficulty":      "Medium",
        "conducting_body": exam.conducting_body or "",
    }


# ─────────────────────────────────────────────────────────────
# View Classes
# ─────────────────────────────────────────────────────────────

class PyqPdfUploadView(APIView):
    """Upload PDF and extract questions."""
    authentication_classes = []
    permission_classes     = [AllowAny]
    parser_classes         = [MultiPartParser, FormParser]

    def post(self, request, exam_id):
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({"error": f"No exam found with id {exam_id}."},
                            status=status.HTTP_404_NOT_FOUND)

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"error": 'No file provided. Send the file under the key "file".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if file_obj.size > MAX_FILE_SIZE_BYTES:
            return Response({"error": "File exceeds the 50MB limit."},
                            status=status.HTTP_400_BAD_REQUEST)
        if not file_obj.name.lower().endswith(".pdf"):
            return Response({"error": "Unsupported file type. Please upload a PDF."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            text = _extract_pdf_text_preserved(file_obj)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not text.strip():
            return Response(
                {"error": "No extractable text found in this PDF."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        questions = _extract_question_with_options(text)

        if not questions:
            return Response(
                {"error": "Could not detect any questions in this PDF."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Paper details ─────────────────────────────────────────────────
        # Moved up from the bottom of this method (was previously computed
        # right before _persist()). We need the exam's subject list *before*
        # the subject-block fallback below, so it has to run first now.
        paper_details = _guess_paper_details(text, exam, file_obj.name)

        # ── v10: subject-wise block fallback ────────────────────────────
        # Some papers (older JEE Main PDFs especially — 2002, 2011, etc.)
        # print all questions back-to-back with NO in-text subject headers
        # at all ("Physics (Section A)" style markers). In that case
        # _build_subject_section_map() inside _extract_question_with_options()
        # found nothing, so every question's "subject" is still empty here.
        # As a fallback, split the paper into len(subject_names) equal
        # contiguous blocks, in order — e.g. for 90 questions and
        # ["Physics", "Chemistry", "Mathematics"]:
        #     Q1-30  -> Physics
        #     Q31-60 -> Chemistry
        #     Q61-90 -> Mathematics
        # This only fires when NOT A SINGLE question got a subject from the
        # header-based detection, so it never overrides real header parsing
        # (including papers where only some sections have headers).
        if not any(q.get("subject") for q in questions):
            block_order = (
                request.data.getlist("subject_block_order")
                or paper_details["subject_names"]
                or DEFAULT_SUBJECT_BLOCK_ORDER
            )
            _assign_subjects_by_block(questions, block_order)

        # ── Diagram extraction ───────────────────────────────────────────
        diagrams_by_question = {}
        try:
            region_diagrams = _extract_pdf_images_by_question(file_obj)
            diagrams_by_question.update(region_diagrams)
        except Exception as e:
            print(f"Region-based extraction error: {e}")

        # ── v9 FIX ──────────────────────────────────────────────────────
        # diagrams_by_question is keyed by the REAL question_number printed
        # in the PDF (see _extract_pdf_images_by_question). Previously there
        # was a fallback here that, when a question had no bucket under its
        # own question_number, searched for a bucket keyed by q["index"]
        # (the 0-based list position) instead. Because index == question_number - 1
        # for normally-numbered papers, that fallback silently attached the
        # PREVIOUS question's diagrams to the current one whenever the current
        # question had no diagrams of its own — this is exactly the "diagram
        # leaking into the next question/option" bug. The fallback has been
        # removed: if there's no bucket for this question's real number, the
        # question simply has no diagrams, which is correct.
        for q in questions:
            qnum   = q.get("question_number")
            bucket = diagrams_by_question.get(qnum) or {'question': [], 'options': {}}

            q_images = []
            for idx, png_bytes in enumerate(bucket.get("question", [])):
                try:
                    raw = png_bytes.get('png_bytes') if isinstance(png_bytes, dict) else png_bytes
                    if raw:
                        filename   = f'pyq_diagrams/{uuid.uuid4().hex}_q{qnum}_diag_{idx}.png'
                        saved_path = default_storage.save(filename, ContentFile(raw))
                        q_images.append(default_storage.url(saved_path))
                except Exception as e:
                    print(f"Error saving question diagram {idx}: {e}")
            q["images"] = q_images

            option_images = {"A": None, "B": None, "C": None, "D": None}
            for letter, png_list in bucket.get("options", {}).items():
                if letter not in option_images or not png_list:
                    continue
                try:
                    raw = png_list[0].get('png_bytes') if isinstance(png_list[0], dict) else png_list[0]
                    if raw:
                        filename   = f'pyq_diagrams/{uuid.uuid4().hex}_q{qnum}_opt_{letter}.png'
                        saved_path = default_storage.save(filename, ContentFile(raw))
                        option_images[letter] = default_storage.url(saved_path)
                except Exception as e:
                    print(f"Error saving option {letter} diagram: {e}")
            q["option_images"] = option_images

            # If image-only options, clear brief text placeholders
            for letter in ["A", "B", "C", "D"]:
                if option_images.get(letter):
                    key           = f"option_{letter.lower()}"
                    existing_text = (q.get(key) or "").strip()
                    if existing_text and len(existing_text.split()) > 6:
                        q[key] = ""

            has_all_options = all(
                q.get(f"option_{l.lower()}") or option_images.get(l)
                for l in ["A", "B", "C", "D"]
            )
            has_answer = q.get("correct_answer") in ALLOWED_CORRECT
            if has_all_options and has_answer:
                q["status"], q["status_reason"] = STATUS_VALID, ""
            elif has_all_options and q["status"] != STATUS_VALID:
                q["status"], q["status_reason"] = (
                    STATUS_NEEDS_REVIEW,
                    "Options found but no correct answer detected.",
                )

        # Ensure images keys always exist
        for q in questions:
            if "images"       not in q: q["images"]       = []
            if "option_images" not in q: q["option_images"] = {"A": None, "B": None, "C": None, "D": None}

        # ── chapter auto-mapping (rule based, no LLM / no API cost) ───────
        # Runs once here so the "Review & Map Questions" step already has a
        # chapter, topic and confidence for every question. Wrapped in
        # try/except so a mapping problem can never break the upload itself.
        chapter_summary = {}
        try:
            chapter_summary = _auto_map_questions(exam, questions)
            print(f"[PYQ chapter auto-map debug] {chapter_summary.get('debug')}")       
        except Exception as exc:
            print(f"[PYQ chapter auto-map] skipped: {exc}")

        # ── master/occurrence duplicate detection (never blocks the upload) ──
        duplicate_summary = {}
        try:
            duplicate_summary = _annotate_duplicates(exam, questions, paper_details)
        except Exception as exc:
            print(f"[PYQ duplicate detection] skipped: {exc}")

        upload_id = str(uuid.uuid4())
        _persist(upload_id, {
            "exam_id":      exam_id,
            "file_name":    file_obj.name,
            "questions":    questions,
            "paper_details": paper_details,
            "raw_text":     text[:5000],
        })

        return Response({
            "upload_id":   upload_id,
            "fileName":    file_obj.name,
            "summary":     _summary_counts(questions),
            "paperDetails": paper_details,
            "chapterMapping": chapter_summary,
            "duplicates":  duplicate_summary,
            "questions":   [_question_full(q, request) for q in questions[:5]],
        }, status=status.HTTP_200_OK)


def _save_question_images(questions: list, file_obj) -> None:
    """Mutates each question dict in-place, adding images / option_images."""
    try:
        raw_diagrams = _extract_pdf_images_by_question(file_obj)
    except Exception:
        raw_diagrams = {}

    for q in questions:
        qnum   = q.get('question_number')
        bucket = raw_diagrams.get(qnum, {})

        q_image_urls = []
        for idx, png_bytes in enumerate(bucket.get('question', [])):
            fname = f'pyq_diagrams/{uuid.uuid4().hex}_q{qnum}_diag{idx}.png'
            try:
                saved = default_storage.save(fname, ContentFile(png_bytes))
                q_image_urls.append(default_storage.url(saved))
            except Exception:
                pass
        q['images'] = q_image_urls

        option_image_urls = {'A': None, 'B': None, 'C': None, 'D': None}
        for letter, png_list in bucket.get('options', {}).items():
            if letter not in option_image_urls or not png_list:
                continue
            fname = f'pyq_diagrams/{uuid.uuid4().hex}_q{qnum}_opt{letter}.png'
            try:
                saved = default_storage.save(fname, ContentFile(png_list[0]))
                option_image_urls[letter] = default_storage.url(saved)
            except Exception:
                pass
        q['option_images'] = option_image_urls


class PyqFullQuestionsView(APIView):
    """View to get all questions with full details for review."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        questions     = cached["questions"]
        status_filter = request.query_params.get("status", "all")
        if status_filter != "all":
            questions = [q for q in questions if q["status"] == status_filter]

        return Response({
            "total":   len(questions),
            "summary": _summary_counts(cached["questions"]),
            "questions": [_question_full(q, request) for q in questions],
        }, status=status.HTTP_200_OK)


class PyqPaperDetailsView(APIView):
    """View to get/update paper details."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(cached["paper_details"], status=status.HTTP_200_OK)

    def post(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        details = cached["paper_details"]
        body    = request.data

        if "subject_ids" in body:
            subject_ids = body["subject_ids"] or []
            subs = list(Subject.objects.filter(pk__in=subject_ids, exam_id=cached["exam_id"]))
            if len(subs) != len(set(subject_ids)):
                return Response({"error": "One or more subject_ids are invalid for this exam."},
                                status=status.HTTP_400_BAD_REQUEST)
            by_id   = {s.subject_id: s for s in subs}
            ordered = [by_id[sid] for sid in subject_ids if sid in by_id]
            details["subject_ids"]   = [s.subject_id   for s in ordered]
            details["subject_names"] = [s.subject_name for s in ordered]

        if "exam_year" in body:
            raw_year = str(body["exam_year"] if body["exam_year"] is not None else "").strip()
            if not raw_year:
                return Response({"error": "Exam Year is required."}, status=status.HTTP_400_BAD_REQUEST)
            if not raw_year.isdigit() or not (1950 <= int(raw_year) <= timezone.now().year + 1):
                return Response({"error": "Enter a valid 4-digit exam year."}, status=status.HTTP_400_BAD_REQUEST)
            details["exam_year"] = int(raw_year)

        for field in ("pyq_session", "difficulty", "conducting_body"):
            if field in body:
                details[field] = body[field]

        cached["paper_details"] = details
        _persist(upload_id, cached)
        return Response(details, status=status.HTTP_200_OK)


class PyqQuestionsListView(APIView):
    """View to list questions with pagination."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        questions     = cached["questions"]
        status_filter = request.query_params.get("status", "all")
        if status_filter != "all":
            questions = [q for q in questions if q["status"] == status_filter]

        subject_filter = request.query_params.get("subject")
        if subject_filter:
            questions = [q for q in questions
                         if (q.get("subject") or "").lower() == subject_filter.lower()]

        section_filter = request.query_params.get("section")
        if section_filter:
            questions = [q for q in questions
                         if (q.get("section") or "").lower() == section_filter.lower()]

        # ?indexes=1,5,9 -> only those questions (used by the Add-to-Test panel)
        indexes_param = (request.query_params.get("indexes") or "").strip()
        if indexes_param:
            wanted = {int(x) for x in indexes_param.split(",") if x.strip().lstrip("-").isdigit()}
            questions = [q for q in questions if q["index"] in wanted]

        page      = max(int(request.query_params.get("page",      1)),  1)
        page_size = min(max(int(request.query_params.get("page_size", 10)), 1), 500)
        start       = (page - 1) * page_size
        end         = start + page_size
        total_pages = max((len(questions) + page_size - 1) // page_size, 1)

        return Response({
            "summary":    _summary_counts(cached["questions"]),
            "page":       page,
            "pageSize":   page_size,
            "totalPages": total_pages,
            "results":    [_question_preview(q) for q in questions[start:end]],
        }, status=status.HTTP_200_OK)


class PyqBulkValidateView(APIView):
    """Bulk validate questions, especially those with diagrams."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        question_ids    = request.data.get("question_ids", [])
        validated_count = 0

        for q in cached["questions"]:
            if question_ids and q["index"] not in question_ids:
                continue

            option_images = q.get("option_images") or {}

            def _has_opt(letter):
                return bool(q.get(f"option_{letter}")) or bool(option_images.get(letter.upper()))

            filled_options = [c for c in ("a", "b", "c", "d") if _has_opt(c)]
            has_all_options = len(filled_options) == 4
            has_answer      = q["correct_answer"] in ALLOWED_CORRECT

            if has_all_options and has_answer:
                q["status"]        = STATUS_VALID
                q["status_reason"] = "Manually validated"
                validated_count   += 1

        _persist(upload_id, cached)
        return Response({
            "validated_count": validated_count,
            "summary":         _summary_counts(cached["questions"])
        }, status=status.HTTP_200_OK)


class PyqQuestionDetailView(APIView):
    """View to get/update individual question details."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def _find(self, cached, index):
        for q in cached["questions"]:
            if q["index"] == index:
                return q
        return None

    def get(self, request, upload_id, index):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)
        q = self._find(cached, int(index))
        if not q:
            return Response({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(_question_full(q, request), status=status.HTTP_200_OK)

    def patch(self, request, upload_id, index):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        q = self._find(cached, int(index))
        if not q:
            return Response({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)

        editable_fields = (
            "duplicate_action", "extra_chapter_ids", "concepts", "source_chapter_name",
            "question_text", "subject", "section", "question_type",
            "option_a", "option_b", "option_c", "option_d", "option_e",
            "correct_answer", "numerical_answer", "solution_text",
            "difficulty", "marks", "negative_marks",
        )
        for field in editable_fields:
            if field in request.data:
                q[field] = request.data[field]

        if "correct_answer" in request.data:
            q["correct_answer"]  = str(q["correct_answer"]).strip().upper()
        if "numerical_answer" in request.data:
            q["numerical_answer"] = str(q["numerical_answer"]).strip()

        if q["question_type"] == QUESTION_TYPE_NUMERICAL:
            has_answer = bool(q.get("numerical_answer"))
            if q["question_text"] and has_answer:
                q["status"], q["status_reason"] = STATUS_VALID, ""
            elif q["question_text"]:
                q["status"]        = STATUS_NEEDS_REVIEW
                q["status_reason"] = "Still missing a numerical answer value."
            else:
                q["status"]        = STATUS_FAILED
                q["status_reason"] = "Question text is empty."
        else:
            option_images = q.get("option_images") or {}

            def _option_present(letter):
                return bool(q.get(f"option_{letter}")) or bool(option_images.get(letter.upper()))

            has_some_options = any(_option_present(c) for c in ("a", "b", "c", "d"))
            has_min_options  = all(_option_present(c) for c in ("a", "b", "c", "d"))
            has_answer       = q["correct_answer"] in ALLOWED_CORRECT

            if q["question_text"] and has_min_options and has_answer:
                q["status"], q["status_reason"] = STATUS_VALID, ""
            elif q["question_text"] and has_some_options and not has_answer:
                q["status"]        = STATUS_NEEDS_REVIEW
                q["status_reason"] = "Options found but no correct answer selected."
            elif q["question_text"] and has_some_options:
                q["status"]        = STATUS_NEEDS_REVIEW
                q["status_reason"] = "Some options are empty. Please fill all options."
            elif q["question_text"]:
                q["status"]        = STATUS_NEEDS_REVIEW
                q["status_reason"] = "No options found. Please add options."
            else:
                q["status"]        = STATUS_FAILED
                q["status_reason"] = "Question text is empty."

        # Subject changed in the review screen -> the old chapter no longer
        # applies, so classify again inside the new subject.
        if "subject" in request.data:
            exam_obj = Exam.objects.filter(pk=cached["exam_id"]).first()
            if exam_obj:
                q.pop("mapping_source", None)
                _auto_map_questions(exam_obj, [q])

        _persist(upload_id, cached)
        return Response(_question_full(q, request), status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# Chapter / import helpers
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# PYQ -> CHAPTER AUTO-MAPPING (view functions only — no model changes)
# ─────────────────────────────────────────────────────────────
# Keyword bank covers the official JEE Main chapter list (Physics,
# Chemistry, Mathematics) and NEET UG chapter list (Physics, Chemistry,
# Biology — Botany + Zoology). Matched against your EXISTING
# Chapter.chapter_name values for each Subject — nothing is created.
# Extend/edit this dict directly; no migration needed.

import re as _re
from collections import defaultdict as _defaultdict
from rest_framework.decorators import api_view, permission_classes

DEFAULT_CHAPTER_KEYWORDS = {
    # ══════════════════════ JEE MAIN + NEET — PHYSICS (shared) ═══════════
    ("physics", "physics and measurement"): [
        "dimension", "dimensional formula", "significant figures", "least count",
        "error analysis", "unit", "si unit", "measurement", "vernier", "screw gauge",
    ],
    ("physics", "units and measurements"): [
        "dimension", "dimensional formula", "significant figures", "least count",
        "error analysis", "unit", "si unit", "measurement", "vernier", "screw gauge",
    ],
    ("physics", "kinematics"): [
        "velocity", "acceleration", "displacement", "projectile", "relative velocity",
        "equation of motion", "speed", "graph represent the motion", "thrown vertically",
    ],
    ("physics", "motion in a straight line"): [
        "velocity", "acceleration", "displacement", "speed", "uniform motion",
        "equation of motion", "graph represent the motion", "thrown vertically",
    ],
    ("physics", "motion in a plane"): [
        "projectile", "relative velocity", "vector addition", "circular motion",
        "resultant", "scalar and vector", "horizontal range",
    ],
    ("physics", "laws of motion"): [
        "newton's law", "friction", "tension", "pulley", "circular motion", "banking of road",
        "centripetal", "cyclist leaning", "normal reaction", "inertia", "momentum",
    ],
    ("physics", "work, energy and power"): [
        "work done", "kinetic energy", "potential energy", "power", "spring constant",
        "conservation of energy", "collision", "elastic collision",
    ],
    ("physics", "system of particles and rotational motion"): [
        "moment of inertia", "torque", "angular momentum", "rotational", "rolling",
        "hollow sphere", "solid sphere", "radius of gyration", "angular velocity",
        "centre of mass",
    ],
    ("physics", "rotational motion"): [
        "moment of inertia", "torque", "angular momentum", "rotational", "rolling",
        "hollow sphere", "solid sphere", "radius of gyration", "angular velocity",
    ],
    ("physics", "gravitation"): [
        "escape velocity", "orbital velocity", "gravitational", "kepler", "satellite",
        "acceleration due to gravity", "planet",
    ],
    ("physics", "mechanical properties of solids"): [
        "young's modulus", "stress", "strain", "elastic", "wire of length", "stretching force",
        "bulk modulus", "shear modulus", "elasticity",
    ],
    ("physics", "mechanical properties of fluids"): [
        "surface tension", "soap bubble", "viscosity", "capillary", "cohesion", "adhesion",
        "bernoulli", "pascal's law", "buoyancy", "pressure in fluid",
    ],
    ("physics", "thermal properties of matter"): [
        "specific heat", "calorimetry", "latent heat", "thermal expansion",
        "conduction", "convection", "radiation", "thermal conductivity",
    ],
    ("physics", "thermodynamics"): [
        "adiabatic", "isothermal", "isobaric", "entropy", "heat engine", "carnot",
        "first law of thermodynamics", "internal energy", "efficiency of engine",
    ],
    ("physics", "kinetic theory of gases"): [
        "kinetic theory", "rms speed", "degrees of freedom", "mean free path",
        "ideal gas equation", "boltzmann",
    ],
    ("physics", "oscillations"): [
        "shm", "simple harmonic", "time period", "amplitude", "oscillation", "angular frequency",
        "maximum velocity", "maximum acceleration", "simple pendulum",
    ],
    ("physics", "oscillations and waves"): [
        "shm", "simple harmonic", "time period", "amplitude", "oscillation",
        "wave equation", "standing wave", "beats", "doppler effect", "resonance",
    ],
    ("physics", "waves"): [
        "wave equation", "standing wave", "beats", "doppler effect", "resonance",
        "transverse wave", "longitudinal wave", "wavelength",
    ],
    ("physics", "electrostatics"): [
        "electric field", "electric potential", "coulomb", "capacitor", "gauss's law",
        "dipole", "charge", "electric flux",
    ],
    ("physics", "current electricity"): [
        "resistance", "resistivity", "ohm's law", "kirchhoff", "wheatstone bridge", "emf",
        "potentiometer", "drift velocity", "cell internal resistance",
    ],
    ("physics", "moving charges and magnetism"): [
        "magnetic field", "biot-savart", "ampere's law", "solenoid", "magnetic flux", "lorentz force",
        "cyclotron", "moving coil galvanometer",
    ],
    ("physics", "magnetic effects of current and magnetism"): [
        "magnetic field", "biot-savart", "ampere's law", "solenoid", "magnetic flux", "lorentz force",
    ],
    ("physics", "magnetism and matter"): [
        "bar magnet", "magnetic dipole moment", "earth's magnetism", "magnetic susceptibility",
        "curie's law", "diamagnetic", "paramagnetic", "ferromagnetic",
    ],
    ("physics", "electromagnetic induction"): [
        "faraday's law", "lenz's law", "induced emf", "self inductance", "mutual inductance",
        "eddy current",
    ],
    ("physics", "electromagnetic induction and alternating currents"): [
        "faraday's law", "lenz's law", "induced emf", "self inductance", "mutual inductance",
        "ac circuit", "rms value", "reactance", "resonant frequency", "transformer",
    ],
    ("physics", "alternating current"): [
        "ac circuit", "rms value", "reactance", "resonant frequency", "transformer",
        "power factor", "lcr circuit",
    ],
    ("physics", "electromagnetic waves"): [
        "electromagnetic spectrum", "displacement current", "poynting vector", "em wave",
    ],
    ("physics", "ray optics and optical instruments"): [
        "refraction", "reflection", "lens", "mirror", "focal length", "microscope",
        "telescope", "total internal reflection", "prism",
    ],
    ("physics", "wave optics"): [
        "interference", "diffraction", "young's double slit", "wavelength", "polarization",
        "coherent sources", "fringe width",
    ],
    ("physics", "optics"): [
        "refraction", "reflection", "lens", "mirror", "interference", "diffraction",
        "young's double slit", "focal length", "wavelength", "polarization",
    ],
    ("physics", "dual nature of radiation and matter"): [
        "photoelectric", "de broglie", "work function", "stopping potential", "threshold frequency",
    ],
    ("physics", "atoms"): [
        "bohr model", "hydrogen spectrum", "rutherford", "energy level", "atomic model",
    ],
    ("physics", "nuclei"): [
        "radioactivity", "half life", "nuclear", "binding energy", "mass defect",
        "nuclear fission", "nuclear fusion", "alpha decay", "beta decay",
    ],
    ("physics", "atoms and nuclei"): [
        "bohr model", "hydrogen spectrum", "rutherford", "radioactivity", "half life",
        "nuclear", "binding energy", "mass defect",
    ],
    ("physics", "dual nature of matter and radiation"): [
        "photoelectric", "de broglie", "work function", "stopping potential",
    ],
    ("physics", "semiconductor electronics"): [
        "diode", "transistor", "p-n junction", "rectifier", "semiconductor", "logic gate",
        "zener diode",
    ],
    ("physics", "electronic devices"): [
        "diode", "transistor", "p-n junction", "rectifier", "semiconductor", "logic gate",
    ],
    ("physics", "communication systems"): [
        "modulation", "amplitude modulation", "frequency modulation", "bandwidth",
        "antenna", "transmission",
    ],
    ("physics", "experimental skills"): [
        "experiment", "vernier callipers", "screw gauge", "simple pendulum experiment",
        "meter bridge", "post office box",
    ],

    # ══════════════════════ JEE MAIN — CHEMISTRY ═══════════════════════
    ("chemistry", "some basic concepts in chemistry"): [
        "molarity", "molality", "mole fraction", "empirical formula", "molecular formula",
        "limiting reagent", "equivalent weight", "mole concept", "normality",
    ],
    ("chemistry", "mole concept"): [
        "molarity", "molality", "mole fraction", "empirical formula", "molecular formula",
        "limiting reagent", "equivalent weight",
    ],
    ("chemistry", "atomic structure"): [
        "quantum number", "orbital", "electronic configuration", "aufbau", "hund's rule",
        "heisenberg", "schrodinger", "de broglie wavelength",
    ],
    ("chemistry", "structure of atom"): [
        "quantum number", "orbital", "electronic configuration", "aufbau", "hund's rule",
        "heisenberg", "schrodinger",
    ],
    ("chemistry", "chemical bonding and molecular structure"): [
        "hybridization", "vsepr", "sigma bond", "pi bond", "lewis structure", "bond order",
        "molecular orbital", "ionic bond", "covalent bond", "dipole moment",
    ],
    ("chemistry", "chemical bonding"): [
        "hybridization", "vsepr", "sigma bond", "pi bond", "lewis structure", "bond order",
        "molecular orbital", "ionic bond", "covalent bond",
    ],
    ("chemistry", "classification of elements and periodicity in properties"): [
        "periodic trend", "ionization energy", "electron affinity", "electronegativity",
        "atomic radius", "periodic property", "modern periodic table",
    ],
    ("chemistry", "periodic table"): [
        "periodic trend", "ionization energy", "electron affinity", "electronegativity",
        "atomic radius", "periodic property",
    ],
    ("chemistry", "states of matter"): [
        "gas laws", "ideal gas equation", "van der waals", "boyle's law", "charles's law",
        "critical temperature", "compressibility factor",
    ],
    ("chemistry", "thermodynamics"): [
        "enthalpy", "entropy", "gibbs free energy", "hess's law", "exothermic", "endothermic",
        "spontaneity", "internal energy",
    ],
    ("chemistry", "equilibrium"): [
        "equilibrium constant", "le chatelier", "ksp", "ph", "buffer", "acid dissociation",
        "common ion effect", "kw", "solubility product",
    ],
    ("chemistry", "redox reactions and electrochemistry"): [
        "electrode potential", "nernst equation", "galvanic cell", "electrolysis", "emf of cell",
        "faraday's law", "oxidation number", "redox",
    ],
    ("chemistry", "electrochemistry"): [
        "electrode potential", "nernst equation", "galvanic cell", "electrolysis", "emf of cell",
        "faraday's law",
    ],
    ("chemistry", "chemical kinetics"): [
        "rate of reaction", "order of reaction", "rate constant", "activation energy",
        "arrhenius equation", "half life of reaction",
    ],
    ("chemistry", "surface chemistry"): [
        "adsorption", "colloid", "catalysis", "emulsion", "micelle", "tyndall effect",
    ],
    ("chemistry", "classification of elements and periodicity"): [
        "periodic trend", "ionization energy", "electron affinity", "electronegativity",
    ],
    ("chemistry", "general principles and processes of isolation of metals"): [
        "metallurgy", "ore", "extraction of metal", "roasting", "calcination", "smelting",
        "electrolytic refining",
    ],
    ("chemistry", "hydrogen"): [
        "hydrogen", "hydride", "heavy water", "hydrogen peroxide",
    ],
    ("chemistry", "s-block elements"): [
        "alkali metal", "alkaline earth metal", "group 1", "group 2", "s-block",
    ],
    ("chemistry", "p-block elements"): [
        "group 13", "group 14", "group 15", "group 16", "group 17", "group 18",
        "boron family", "carbon family", "nitrogen family", "oxygen family", "halogen", "noble gas",
    ],
    ("chemistry", "d and f block elements"): [
        "transition element", "lanthanide", "actinide", "d-block", "f-block",
    ],
    ("chemistry", "coordination compounds"): [
        "coordination number", "ligand", "crystal field", "werner", "chelate", "isomerism in complex",
    ],
    ("chemistry", "environmental chemistry"): [
        "pollutant", "greenhouse effect", "ozone depletion", "smog", "bod",
    ],
    ("chemistry", "purification and characterisation of organic compounds"): [
        "distillation", "crystallization", "chromatography", "qualitative analysis",
    ],
    ("chemistry", "some basic principles of organic chemistry"): [
        "iupac name", "inductive effect", "resonance", "hyperconjugation", "nucleophile",
        "electrophile", "carbocation", "reaction mechanism",
    ],
    ("chemistry", "organic chemistry basics"): [
        "iupac name", "inductive effect", "resonance", "hyperconjugation", "nucleophile",
        "electrophile", "carbocation",
    ],
    ("chemistry", "hydrocarbons"): [
        "alkane", "alkene", "alkyne", "aromatic", "markovnikov", "combustion",
    ],
    ("chemistry", "organic compounds containing halogens"): [
        "haloalkane", "haloarene", "sn1", "sn2", "grignard reagent",
    ],
    ("chemistry", "organic compounds containing oxygen"): [
        "alcohol", "phenol", "ether", "aldehyde", "ketone", "carboxylic acid",
    ],
    ("chemistry", "organic compounds containing nitrogen"): [
        "amine", "diazonium salt", "cyanide", "isocyanide",
    ],
    ("chemistry", "biomolecules"): [
        "carbohydrate", "protein", "enzyme", "nucleic acid", "vitamin", "amino acid",
    ],
    ("chemistry", "polymers"): [
        "polymer", "monomer", "polymerization", "addition polymer", "condensation polymer",
    ],
    ("chemistry", "chemistry in everyday life"): [
        "drug", "antibiotic", "analgesic", "antiseptic", "detergent", "soap",
    ],
    ("chemistry", "solutions"): [
        "colligative property", "raoult's law", "osmotic pressure", "elevation of boiling point",
        "depression of freezing point", "vapour pressure",
    ],
    ("chemistry", "solid state"): [
        "unit cell", "crystal lattice", "packing efficiency", "bragg's law", "fcc", "bcc",
        "voids", "coordination number in solid",
    ],

    # ══════════════════════ JEE MAIN — MATHEMATICS ═════════════════════
    ("mathematics", "sets, relations and functions"): [
        "set theory", "relation", "function", "domain and range", "one-one function",
        "onto function",
    ],
    ("mathematics", "complex numbers and quadratic equations"): [
        "complex number", "quadratic equation", "roots of the equation", "discriminant",
        "argand plane", "modulus of complex number",
    ],
    ("mathematics", "quadratic equations"): [
        "quadratic equation", "roots of the equation", "discriminant", "sum of roots", "product of roots",
    ],
    ("mathematics", "matrices and determinants"): [
        "matrix", "determinant", "adjoint", "inverse of matrix", "cramer's rule", "rank of matrix",
    ],
    ("mathematics", "permutations and combinations"): [
        "permutation", "combination", "arrangement", "selection", "factorial", "ncr", "npr",
    ],
    ("mathematics", "binomial theorem and its simple applications"): [
        "binomial theorem", "binomial expansion", "binomial coefficient", "general term",
    ],
    ("mathematics", "sequence and series"): [
        "arithmetic progression", "geometric progression", "sum of series", "nth term", "a.p.", "g.p.",
        "harmonic progression",
    ],
    ("mathematics", "sequences and series"): [
        "arithmetic progression", "geometric progression", "sum of series", "nth term", "a.p.", "g.p.",
    ],
    ("mathematics", "limit, continuity and differentiability"): [
        "limit", "continuity", "differentiability", "derivative", "rate of change",
    ],
    ("mathematics", "limits and derivatives"): [
        "limit", "derivative", "differentiability", "continuity", "rate of change",
    ],
    ("mathematics", "integral calculus"): [
        "integral", "definite integral", "indefinite integral", "area under curve",
        "integration by parts",
    ],
    ("mathematics", "integration"): [
        "integral", "definite integral", "indefinite integral", "area under curve", "integration by parts",
    ],
    ("mathematics", "differential equations"): [
        "differential equation", "order and degree", "general solution", "particular solution",
    ],
    ("mathematics", "coordinate geometry"): [
        "straight line", "circle equation", "parabola", "ellipse", "hyperbola", "locus", "slope",
    ],
    ("mathematics", "three dimensional geometry"): [
        "direction cosine", "plane equation", "3d geometry", "line in space", "shortest distance",
    ],
    ("mathematics", "vector algebra"): [
        "vector", "dot product", "cross product", "scalar triple product", "unit vector",
    ],
    ("mathematics", "vectors and 3d geometry"): [
        "vector", "dot product", "cross product", "direction cosine", "plane equation", "3d geometry",
    ],
    ("mathematics", "statistics and probability"): [
        "mean deviation", "variance", "standard deviation", "probability", "conditional probability",
        "bayes theorem", "random variable",
    ],
    ("mathematics", "probability"): [
        "probability", "conditional probability", "bayes", "random variable", "expected value",
    ],
    ("mathematics", "trigonometry"): [
        "trigonometric", "sin", "cos", "tan", "identity", "angle of elevation", "sine rule", "cosine rule",
        "height and distance",
    ],
    ("mathematics", "mathematical reasoning"): [
        "logical statement", "truth table", "negation", "tautology", "contrapositive",
    ],

    # ══════════════════════ NEET UG — BIOLOGY (Botany + Zoology) ═══════
    ("biology", "the living world"): [
        "taxonomy", "systematics", "binomial nomenclature", "classification of organisms",
    ],
    ("biology", "biological classification"): [
        "five kingdom", "monera", "protista", "fungi classification", "whittaker",
    ],
    ("biology", "plant kingdom"): [
        "algae", "bryophyte", "pteridophyte", "gymnosperm", "angiosperm classification",
    ],
    ("biology", "animal kingdom"): [
        "phylum", "porifera", "coelenterata", "annelida", "arthropoda", "mollusca", "chordata",
    ],
    ("biology", "morphology of flowering plants"): [
        "root", "stem", "leaf", "flower", "inflorescence", "fruit", "seed morphology",
    ],
    ("biology", "anatomy of flowering plants"): [
        "tissue system", "meristem", "vascular bundle", "secondary growth", "epidermis",
    ],
    ("biology", "structural organisation in animals"): [
        "epithelial tissue", "connective tissue", "muscular tissue", "nervous tissue",
        "earthworm", "cockroach",
    ],
    ("biology", "cell: the unit of life"): [
        "cell membrane", "mitochondria", "nucleus", "organelle", "cell theory", "ribosome",
    ],
    ("biology", "cell biology"): [
        "cell membrane", "mitochondria", "nucleus", "organelle", "mitosis", "meiosis",
        "cell cycle", "chromosome",
    ],
    ("biology", "cell cycle and cell division"): [
        "mitosis", "meiosis", "cell cycle", "chromosome", "cytokinesis",
    ],
    ("biology", "biomolecules"): [
        "carbohydrate", "protein", "enzyme", "nucleic acid", "amino acid", "lipid",
    ],
    ("biology", "photosynthesis in higher plants"): [
        "photosynthesis", "light reaction", "calvin cycle", "chlorophyll", "photophosphorylation",
    ],
    ("biology", "plant physiology"): [
        "photosynthesis", "transpiration", "respiration in plants", "plant hormone", "stomata",
    ],
    ("biology", "respiration in plants"): [
        "glycolysis", "krebs cycle", "electron transport chain", "fermentation", "atp",
    ],
    ("biology", "plant growth and development"): [
        "auxin", "gibberellin", "cytokinin", "ethylene", "abscisic acid", "photoperiodism",
    ],
    ("biology", "breathing and exchange of gases"): [
        "respiratory system", "lungs", "gas exchange", "hemoglobin", "vital capacity",
    ],
    ("biology", "body fluids and circulation"): [
        "blood", "heart", "cardiac cycle", "blood pressure", "lymph", "ecg",
    ],
    ("biology", "excretory products and their elimination"): [
        "nephron", "kidney", "urine formation", "excretory system", "uric acid",
    ],
    ("biology", "locomotion and movement"): [
        "muscle contraction", "skeletal system", "joint", "sarcomere", "actin myosin",
    ],
    ("biology", "neural control and coordination"): [
        "neuron", "synapse", "reflex arc", "brain", "nerve impulse",
    ],
    ("biology", "chemical coordination and integration"): [
        "hormone", "endocrine gland", "pituitary", "thyroid", "adrenal",
    ],
    ("biology", "human physiology"): [
        "digestive system", "respiratory system", "circulatory system", "nervous system",
        "excretory system", "hormone",
    ],
    ("biology", "digestion and absorption"): [
        "digestive system", "enzyme digestion", "alimentary canal", "absorption of nutrients",
    ],
    ("biology", "sexual reproduction in flowering plants"): [
        "pollination", "fertilization in plants", "double fertilization", "embryo development",
        "gametophyte",
    ],
    ("biology", "human reproduction"): [
        "spermatogenesis", "oogenesis", "menstrual cycle", "fertilization", "pregnancy",
        "reproductive system",
    ],
    ("biology", "reproductive health"): [
        "contraception", "sti", "infertility", "amniocentesis",
    ],
    ("biology", "reproduction in organisms"): [
        "asexual reproduction", "sexual reproduction", "budding", "fragmentation",
    ],
    ("biology", "principles of inheritance and variation"): [
        "mendel", "allele", "genotype", "phenotype", "dihybrid cross", "monohybrid cross",
        "linkage", "pedigree analysis",
    ],
    ("biology", "molecular basis of inheritance"): [
        "dna replication", "transcription", "translation", "genetic code", "operon", "rna",
    ],
    ("biology", "genetics"): [
        "mendel", "allele", "genotype", "phenotype", "dna", "rna", "chromosome", "mutation",
        "inheritance",
    ],
    ("biology", "evolution"): [
        "natural selection", "darwin", "hardy weinberg", "speciation", "adaptive radiation",
        "homologous organ",
    ],
    ("biology", "human health and disease"): [
        "pathogen", "immunity", "vaccine", "antibody", "aids", "cancer", "malaria",
    ],
    ("biology", "microbes in human welfare"): [
        "fermentation", "antibiotic production", "biogas", "sewage treatment", "curd",
    ],
    ("biology", "biotechnology: principles and processes"): [
        "recombinant dna", "gene cloning", "restriction enzyme", "vector", "pcr",
    ],
    ("biology", "biotechnology and its applications"): [
        "gm crop", "bt cotton", "gene therapy", "insulin production", "transgenic",
    ],
    ("biology", "organisms and populations"): [
        "population growth", "carrying capacity", "population interaction", "predation",
        "competition",
    ],
    ("biology", "ecosystem"): [
        "food chain", "food web", "energy flow", "ecological pyramid", "nutrient cycling",
    ],
    ("biology", "ecology"): [
        "ecosystem", "food chain", "population", "biodiversity", "biotic", "abiotic",
    ],
    ("biology", "biodiversity and conservation"): [
        "biodiversity", "species richness", "endangered species", "conservation", "red data book",
    ],
    ("biology", "environmental issues"): [
        "pollution", "global warming", "ozone depletion", "deforestation", "eutrophication",
    ],
}

_STOPWORDS = {
    "the", "a", "an", "of", "is", "are", "was", "were", "in", "on", "at", "to", "for",
    "and", "or", "if", "which", "what", "following", "given", "find", "value", "then",
    "with", "from", "by", "as", "be", "this", "that", "it", "its", "their", "has", "have",
    "assertion", "reason", "correct", "true", "false", "statement", "consider",
}

CHAPTER_MAP_CONFIDENCE_AUTO_ACCEPT = 60


def _tokenize(text: str) -> list:
    if not text:
        return []
    text = _re.sub(r"\\[a-zA-Z]+", " ", text)
    text = _re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    words = text.lower().split()
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _question_corpus(q: dict) -> str:
    parts = [
        q.get("question_text") or "",
        q.get("option_a") or "", q.get("option_b") or "",
        q.get("option_c") or "", q.get("option_d") or "",
    ]
    return " ".join(parts)


def _chapter_keyword_set(chapter, subject_name: str) -> list:
    seed = DEFAULT_CHAPTER_KEYWORDS.get(
        (subject_name.strip().lower(), chapter.chapter_name.strip().lower())
    )
    if seed:
        return seed
    return _tokenize(chapter.chapter_name)


def classify_question_chapter(question_dict: dict, chapters: list) -> dict:
    if not chapters:
        return {"chapter_id": None, "chapter_name": None, "confidence": 0, "matched_keywords": []}

    corpus_tokens = _tokenize(_question_corpus(question_dict))
    if not corpus_tokens:
        return {"chapter_id": None, "chapter_name": None, "confidence": 0, "matched_keywords": []}

    corpus_counts = _defaultdict(int)
    for tok in corpus_tokens:
        corpus_counts[tok] += 1
    corpus_text = " ".join(corpus_tokens)

    best = {"chapter": None, "score": 0.0, "matched": []}

    for chapter in chapters:
        subject_name = chapter.subject.subject_name if getattr(chapter, "subject_id", None) else ""
        keywords = _chapter_keyword_set(chapter, subject_name)
        if not keywords:
            continue

        raw_score = 0.0
        matched = []
        for kw in keywords:
            kw = kw.strip().lower()
            if not kw:
                continue
            if " " in kw:
                if kw in corpus_text:
                    raw_score += 3.0
                    matched.append(kw)
            else:
                hits = corpus_counts.get(kw, 0)
                if hits:
                    weight = 1.0 if len(kw) <= 5 else 1.5 if len(kw) <= 9 else 2.0
                    raw_score += min(hits, 3) * weight
                    matched.append(kw)

        normalized = raw_score / max(len(keywords), 6) ** 0.5

        if normalized > best["score"]:
            best = {"chapter": chapter, "score": normalized, "matched": matched}

    if not best["chapter"]:
        return {"chapter_id": None, "chapter_name": None, "confidence": 0, "matched_keywords": []}

    confidence = int(min(99, round(best["score"] * 28)))

    return {
        "chapter_id": best["chapter"].chapter_id,
        "chapter_name": best["chapter"].chapter_name,
        "confidence": confidence,
        "matched_keywords": best["matched"][:6],
    }


# ─────────────────────────────────────────────────────────────
# NEW ENGINE (rule based, no LLM) - defined right below
# ─────────────────────────────────────────────────────────────
# Physics / Chemistry / Mathematics use the new topic-rule engine below.
# Any other subject
# (e.g. NEET Biology) still uses DEFAULT_CHAPTER_KEYWORDS +
# classify_question_chapter() above as a fallback, so nothing is lost.

# ═════════ CHAPTER CLASSIFIER ENGINE (all names prefixed _cm_) ═════════
# What it does:
#  1. NORMALISE the question text (strip LaTeX, drop "Statement 1/2" boilerplate)
#  2. SCORE fine-grained topics with weighted regex rules
#       "++x" = +6 (very strong)   "+x" = +4 (strong)   "x" = +2   "-x" = -3
#     stem matches count fully, option-only matches count half
#  3. RESOLVE the winning topic to a real Chapter of THIS exam by fuzzy-matching
#     the topic's alias names against your DB chapter names (nothing is created)
# To improve accuracy later, edit only the topic lists (_cm_PHYSICS,
# _cm_CHEMISTRY, _cm_MATHEMATICS) below.

import difflib
import math
from collections import Counter, defaultdict

# ─────────────────────────────────────────────────────────────
# 1. NORMALISATION
# ─────────────────────────────────────────────────────────────

_cm__GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "θ": "theta", "λ": "lambda", "μ": "mu", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "phi", "ϕ": "phi", "ω": "omega",
    "Δ": "delta", "Ω": "omega", "Σ": "sigma", "Φ": "phi",
}
_cm__LATEX_NOISE = {
    "left", "right", "frac", "cdot", "times", "text", "mathrm", "mathbf",
    "quad", "qquad", "displaystyle", "begin", "end", "cdots", "ldots",
}

# "This question has Statement 1 and Statement 2. Of the four choices ... two Statements."
_cm__STATEMENT_BOILERPLATE = re.compile(
    r"this question has statement\s*1? and statement\s*2?.{0,260}?describes the two statements\.?",
    re.S,
)
_cm__STATEMENT_LABEL = re.compile(r"\bstatement[\s-]*[12ivx]+\s*[:.\-]?")
_cm__BOILERPLATE_OPTION = re.compile(
    r"statement\s*[12ivx]*\s*(is|are)\s*(true|false|correct|incorrect)"
    r"|both\s+(assertion|statements?)|assertion\s*(\(a\))?\s*(is|and)"
    r"|(is|are)\s+the\s+correct\s+explanation",
    re.I,
)


def _cm_normalize(text) -> str:
    """Lower-case, LaTeX-free, single-spaced text that regex rules can match."""
    if not text:
        return ""
    t = str(text)
    t = t.replace("’", "'").replace("‘", "'").replace("−", "-").replace("–", "-")
    t = t.replace("∫", " integral ").replace("∑", " summation ").replace("√", " sqrt ")
    for g, name in _cm__GREEK.items():
        t = t.replace(g, f" {name} ")

    # unit vectors written as ^i ^j ^k  (must run before ^ is stripped)
    t = re.sub(r"\^\s?[ijk]\b", " unitvector ", t)
    t = re.sub(r"\\(int|oint)(?![a-zA-Z])", " integral ", t)
    t = re.sub(r"\\lim(?![a-zA-Z])", " limit ", t)
    t = re.sub(r"\\sum(?![a-zA-Z])", " summation ", t)
    t = re.sub(r"\\(vec|overrightarrow|hat)(?![a-zA-Z])", " vector ", t)

    # \alpha -> alpha ,  \frac -> (dropped)
    t = re.sub(
        r"\\([a-zA-Z]+)",
        lambda m: " " if m.group(1) in _cm__LATEX_NOISE else f" {m.group(1)} ",
        t,
    )
    # nested sub/superscripts:  CO_{2} -> CO2 ,  x^{2} -> x2
    for _ in range(3):
        t = re.sub(r"[_^]\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"[_^]", "", t)
    t = t.replace("{", " ").replace("}", " ")

    t = t.lower()
    t = _cm__STATEMENT_BOILERPLATE.sub(" ", t)
    t = _cm__STATEMENT_LABEL.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def _cm__question_parts(q: dict):
    """Returns (stem_text, options_text) both normalised."""
    stem = _cm_normalize(q.get("question_text"))
    opts = []
    for k in ("option_a", "option_b", "option_c", "option_d", "option_e"):
        raw = q.get(k) or ""
        if not raw or _cm__BOILERPLATE_OPTION.search(raw):
            continue
        opts.append(_cm_normalize(raw))
    return stem, " | ".join(opts)


# ─────────────────────────────────────────────────────────────
# 2. TOPIC RULES   (edit here to improve accuracy)
# ─────────────────────────────────────────────────────────────
# Topic(label, [alias chapter names, best first], [rules])
# Rule prefixes:  "++" = 6   "+" = 4   ""(none) = 2   "-" = -3
# Rules are regex, matched at the START of a word (so "dimension" also hits
# "dimensions"/"dimensional").  Use \b at the end for exact short words.

class _cm_Topic:
    __slots__ = ("label", "aliases", "rules")

    def __init__(self, label, aliases, rules):
        self.label = label
        self.aliases = aliases
        self.rules = [self._compile(r) for r in rules]

    @staticmethod
    def _compile(rule):
        weight = 2.0
        if rule.startswith("++"):
            weight, rule = 6.0, rule[2:]
        elif rule.startswith("+"):
            weight, rule = 4.0, rule[1:]
        elif rule.startswith("-"):
            weight, rule = -3.0, rule[1:]
        # Literal keywords (letters/spaces only) of >= 6 letters are also kept in a
        # "spaceless" form. PDF watermarks sometimes split words ("e se2 ries"), and
        # after dropping digits/spaces the keyword is visible again ("eseries").
        literals = []
        if re.fullmatch(r"[a-z' \-|]+", rule):
            literals = [re.sub(r"[^a-z]", "", alt) for alt in rule.split("|")]
            literals = [x for x in literals if len(x) >= 6]
        return re.compile(r"(?<![a-z0-9])(?:" + rule + ")"), weight, rule, literals


_cm_T = _cm_Topic

_cm_PHYSICS = [
    _cm_T("Units, dimensions & errors",
      ["Physics and Measurement", "Units and Measurements", "Units and Measurement",
       "Physical World and Measurement", "Physics and Measurements"],
      ["++dimension(s|al)?\\b", "+dimensionless", "++maximum possible error|percentage error|relative error|fractional error|absolute error|error in the measure|errors? made in the measure",
       "+significant figure", "+least count", "+vernier", "+screw gauge", "+physical quantit",
       "+si unit|units? of", "measurement", "error"]),
    _cm_T("Kinematics",
      ["Kinematics", "Motion in a Straight Line", "Motion in a Plane", "Mechanics"],
      ["++accelerating uniformly|uniform(ly)? accelerat|uniform acceleration", "+projectile", "+relative velocity",
       "+thrown (vertically|horizontally|upward)|vertically upward", "+free(ly)? fall", "+equations? of motion",
       "+velocity[- ]time|position[- ]time|displacement[- ]time|v-t graph|x-t graph",
       "+retardation|deceleration", "+starts? from rest|starting from rest", "+stopping distance",
       "+horizontal range|angle of projection|time of flight|maximum height",
       "+average (speed|velocity)|instantaneous", "velocity", "acceleration", "displacement", "speed",
       "+train|car|particle moves|moving along a straight"]),
    _cm_T("Laws of motion & friction",
      ["Laws of Motion", "Newton's Laws of Motion", "Laws of Motion and Friction", "Mechanics"],
      ["++newton'?s? (first|second|third)? ?law", "++friction|frictional", "+coefficient of (static |kinetic |limiting )?friction",
       "+pulley|inclined plane|smooth incline|wedge", "+tension in", "+centripetal|centrifugal", "+banking|banked",
       "+normal reaction|normal force", "+impulse", "+conveyer|conveyor", "+rocket|variable mass|dropped on",
       "+lift|elevator|apparent weight", "+recoil", "+momentum", "force", "block", "string", "+circular (motion|path)",
       "+cyclist|turn"]),
    _cm_T("Work, energy, power & collisions",
      ["Work, Energy and Power", "Work Energy and Power", "Work Power and Energy", "Mechanics"],
      ["+work done by|work[- ]energy theorem|work is done", "++elastic collision|inelastic collision|head[- ]on (elastic )?collision|coefficient of restitution",
       "+collision|collides", "+kinetic energy", "+potential energy", "+conservative force", "+conservation of (mechanical )?energy",
       "+spring constant|compressed spring|spring is", "+power (of|delivered|developed)|horse ?power|watt", "+loss in (kinetic )?energy|percentage loss",
       "energy", "work"]),
    _cm_T("Rotational motion & centre of mass",
      ["Rotational Motion", "System of Particles and Rotational Motion", "Rotational Dynamics", "Mechanics"],
      ["++moment of inertia", "++torque", "++angular momentum", "+rolling|rolls without slipping", "+radius of gyration",
       "+cent(re|er) of mass", "+rigid body", "+angular (velocity|acceleration|speed)", "+(disc|disk|ring|cylinder|rod)\\b",
       "+(solid|hollow) (sphere|cylinder)", "+rotat", "+couple", "+inclined plane"]),
    _cm_T("Gravitation",
      ["Gravitation", "Gravity"],
      ["++gravitation", "++escape (velocity|speed)|orbital (velocity|speed)", "++kepler", "+satellite|geostationary", "+acceleration due to gravity",
       "+gravitational (potential|field|force|constant|energy)", "+planet", "+orbit", "+mass of (the )?earth|radius of (the )?earth|surface of (the )?earth",
       "+depth|altitude|height h above"]),
    _cm_T("Elasticity of solids",
      ["Properties of Solids and Liquids", "Mechanical Properties of Solids", "Properties of Matter", "Elasticity"],
      ["++young'?s modulus|bulk modulus|shear modulus|modulus of (rigidity|elasticity)", "++stress|strain", "+elastic", "++breaking (stress|force|load)|without breaking|can sustain|sustain",
       "+hooke", "+elongation|extension of (the )?wire|stretch", "+poisson", "+wire (of|is|has|can)", "+stretching force"]),
    _cm_T("Fluids & surface tension",
      ["Properties of Solids and Liquids", "Mechanical Properties of Fluids", "Properties of Matter"],
      ["++surface tension|surface energy", "++soap bubble|droplet|coalesce", "++viscosity|viscous|coefficient of viscosity", "+capillar", "+bernoulli", "+pascal",
       "+buoyan|archimedes|upthrust|floats?|immersed|submerged", "+terminal velocity|stokes", "+excess pressure", "+angle of contact",
       "+streamline|laminar|turbulent|equation of continuity", "+hydrostatic|manometer|barometer", "+orifice|torricelli|efflux", "+fluid|liquid", "+density"]),
    _cm_T("Heat transfer & calorimetry",
      ["Properties of Solids and Liquids", "Thermal Properties of Matter", "Heat and Thermodynamics", "Thermodynamics"],
      ["++specific heat|heat capacity", "+calorimet", "++latent heat", "+thermal expansion|coefficient of (linear|cubical|volume|superficial) expansion",
       "++conduction|conductivity|thermal conductivity", "+convection", "+radiation|stefan|wien|black ?body", "++newton'?s law of cooling|rate of cooling",
       "+temperature of (the )?junction|thermal resistance", "+insulated", "+melting|ice at|steam|boiling water", "+thermal", "+heat (transfer|flow|lost|gained|required|absorbed)",
       "temperature"]),
    _cm_T("Thermodynamics",
      ["Thermodynamics", "Heat and Thermodynamics"],
      ["++carnot", "++heat engine|efficiency of (a |the )?(real |ideal )?engine|refrigerator|coefficient of performance", "++adiabatic|isothermal|isobaric|isochoric|isentropic",
       "++first law of thermodynamics|second law of thermodynamics|thermodynamic", "+work done by (the )?gas|work done in (the )?(process|expansion)", "+internal energy", "+entropy",
       "+cyclic process|p-?v diagram|indicator diagram", "+molar specific heat|cp|cv", "+reversible|irreversible", "+expansion", "+ideal gas", "+pressure of an ideal gas",
       "+boiling and freezing points of water|between the same two temperatures", "+efficiency"]),
    _cm_T("Kinetic theory of gases",
      ["Kinetic Theory of Gases", "Kinetic Theory", "Thermodynamics"],
      ["++kinetic theory", "++rms (speed|velocity)|root mean square|most probable speed", "++degrees? of freedom|equipartition", "+mean free path", "+boltzmann|avogadro",
       "+maxwell", "+monatomic|diatomic|polyatomic", "+molecules?", "+average kinetic energy", "+ideal gas", "+mixture of gases|two gases|gas at temperature",
       "+vessel|container"]),
    _cm_T("Simple harmonic motion",
      ["Oscillations and Waves", "Oscillations", "Simple Harmonic Motion"],
      ["++simple harmonic|shm\\b", "++oscillat", "++time period|period of (oscillation|the)", "+amplitude", "+pendulum", "+spring[- ]mass|mass[- ]spring|spring constant",
       "+phase (constant|difference)?|phi\\b", "+angular frequency", "+restoring force", "+displacement y|y ?\\(t\\)", "+sin ?\\(? ?omega ?t"]),
    _cm_T("Waves & sound",
      ["Oscillations and Waves", "Waves", "Waves and Sound"],
      ["++sound", "++wave equation|progressive wave|stationary wave|standing wave|transverse wave|longitudinal wave|travelling wave", "++resonan", "++beats?\\b", "++doppler",
       "+organ pipe|closed pipe|open pipe|tube|air column", "+vibrating string|stretched string|string vibrat|sonometer", "+harmonic|overtone|fundamental (frequency|mode)",
       "+node|antinode", "+intensity level|decibel", "+frequency of (the )?(source|note|tuning)", "+wave speed|speed of (a )?wave|velocity of (a )?wave", "frequency", "wavelength"]),
    _cm_T("Electrostatics",
      ["Electrostatics", "Electric Charges and Fields", "Electrostatic Potential and Capacitance"],
      ["++electric field", "++electric potential|potential (at|due to)", "++coulomb", "++capacitor|capacitance", "++gauss", "++electric flux|flux through", "++electric dipole",
       "+surface charge density|charge density", "+point charge|test charge", "+dielectric", "+equipotential", "+charged (sphere|particle|conductor|ring|rod|plate)",
       "+concentric", "+hemisphere", "charge"]),
    _cm_T("Current electricity",
      ["Current Electricity", "Electric Current"],
      ["++resistance|resistor|resistivity", "++ohm", "++kirchh?off", "++wheatstone|meter bridge|potentiometer", "++emf|internal resistance|terminal (voltage|potential)", "++drift velocity",
       "+battery|bulb|filament", "+galvanometer|shunt|ammeter|voltmeter", "+heat produced|joule", "+electric power|power dissipated|watt", "+in (series|parallel)",
       "+current (of|is|through|flows|drawn)", "+cell\\b|cells\\b", "+conductor", "+generator", "+ampere\\b|amp\\b", "+volt"]),
    _cm_T("Magnetic effects of current & magnetism",
      ["Magnetic Effects of Current and Magnetism", "Moving Charges and Magnetism", "Magnetic Effects & Magnetism", "Magnetism and Matter", "Magnetism"],
      ["++magnetic field", "++biot|ampere'?s (circuital )?law|lorentz", "+magnetic (force|moment|induction|dipole|flux density)", "+cyclotron|mass spectrometer", "+solenoid|toroid",
       "+bar magnet|magnetisation|susceptibility|permeability|diamagnet|paramagnet|ferromagnet|hysteresis|earth'?s magnetic|dip angle|declination",
       "+moving charge|charged particle|proton|deuteron|alpha particle|electron (enters|moves)", "+circular path|radius of (its |the )?path|helical path",
       "+torque on (a )?(current )?loop|current[- ]carrying", "+accelerated through (the same )?potential", "+galvanometer"]),
    _cm_T("Electromagnetic induction & AC",
      ["Electromagnetic Induction and Alternating Currents", "Electromagnetic Induction & AC", "Electromagnetic Induction", "Alternating Current"],
      ["++induced (emf|current)|motional emf", "++faraday|lenz", "++self[- ]?inductance|mutual inductance|inductor|inductance|coil of self", "+eddy", "+uniform magnetic field|coil|loop", "+alternating|ac (circuit|voltage|source|current)",
       "+rms (value|current|voltage)|peak value", "+reactance|impedance", "+lcr|l-c-r|lc circuit|series lcr", "+power factor|wattless", "+transformer", "+rails|connector|slide[s]? (freely )?over",
       "+magnetic flux (through|linked)|flux linked", "+resonant frequency"]),
    _cm_T("Electromagnetic waves",
      ["Electromagnetic Waves", "EM Waves"],
      ["++electromagnetic (wave|spectrum|radiation)|em wave", "++displacement current|poynting", "+gamma rays|x-rays|infrared|ultraviolet|microwave|radio waves",
       "+travels in the|propagat", "+magnetic field is along|electric field (of|is) along|vector equation"]),
    _cm_T("Ray optics",
      ["Optics", "Ray Optics and Optical Instruments", "Ray Optics"],
      ["++refractive index|refraction|refract", "++lens|mirror|focal length", "++prism|minimum deviation", "++total(ly)? (internal )?reflect|critical angle", "+telescope|microscope|magnif|optical instrument|eye ?piece|objective",
       "+reflection|reflect", "+snell|dispersion|rainbow", "+concave|convex|plano", "+image", "+ray\\b|rays\\b", "+immersed in (water|liquid)", "+incident (normally|ray|beam)", "+optical fib"]),
    _cm_T("Wave optics",
      ["Optics", "Wave Optics"],
      ["++interference|diffraction", "++young'?s double slit|double slit|ydse", "++fringe|fringes", "++coherent", "++polari[sz]", "+brewster|malus", "+huygen|wavefront",
       "+path difference", "+slit", "+intensity of light", "wavelength"]),
    _cm_T("Photoelectric effect & matter waves",
      ["Dual Nature of Matter and Radiation", "Dual Nature of Radiation and Matter", "Dual Nature of Matter & Radiation"],
      ["++photoelectric|photo ?current|photoelectron|photo ?emission", "++de[- ]?broglie|matter wave|davisson", "++work function|stopping potential|threshold (frequency|wavelength)", "+photon",
       "+incident (light|radiation|frequency)", "+monochromatic"]),
    _cm_T("Atomic models & spectra",
      ["Atoms and Nuclei", "Atoms"],
      ["++bohr", "++hydrogen (atom|spectrum|like|spectral)|balmer|lyman|paschen|brackett", "++rutherford", "+energy levels?", "++ionisation energy|ionization energy|binding energy of (an )?electron",
       "+spectral (line|series)", "+orbits? of (an )?electron|electron in (the )?(nth|hydrogen|ground|excited)", "+ground state|excited state", "+moseley|characteristic x", "+lithium|li\\+\\+?|li atom"]),
    _cm_T("Nuclear physics",
      ["Atoms and Nuclei", "Nuclei"],
      ["++radioactiv", "++half[- ]?life|decay constant|mean life|activity of", "+decay", "++nuclear|nucleus|nuclei|nucleon", "++mass defect|binding energy per nucleon", "+fission|fusion",
       "+alpha (particle|decay|emission)|beta (particle|decay|emission)|gamma (ray|decay)|alpha and beta", "+isotope|isobar|isotone", "+becquerel"]),
    _cm_T("Semiconductors & logic gates",
      ["Electronic Devices", "Semiconductor Electronics", "Semiconductor Devices"],
      ["++diode|transistor|semiconductor", "++p-?n junction|rectifier|zener", "++logic gate|nor gate|nand gate|and gate|or gate|not gate|boolean|truth table", "+amplifier|oscillator",
       "+n-?type|p-?type|doping|forward bias|reverse bias|depletion", "+conduction band|valence band|energy gap"]),
    _cm_T("Communication systems",
      ["Communication Systems", "Communication System", "Electronic Devices", "Semiconductor Electronics"],
      ["++modulat|demodulat", "++carrier wave|amplitude modulated|side ?band", "+bandwidth", "+antenna", "+ground wave|sky wave|space wave|ionosphere", "+transmitter|receiver|transmission|signal",
       "+satellite communication"]),
    _cm_T("Experimental skills",
      ["Experimental Skills", "Experimental Physics", "Practical Physics"],
      ["++experiment", "++meter bridge|post office box", "+screw gauge|vernier call?ip", "+least count", "+simple pendulum"]),
]

_cm_CHEMISTRY = [
    _cm_T("Mole concept & stoichiometry",
      ["Some Basic Concepts in Chemistry", "Some Basic Concepts of Chemistry", "Basic Concepts of Chemistry", "Mole Concept"],
      ["++mole concept|stoichiometr", "++limiting (reagent|reactant)", "++empirical formula|molecular formula", "+equivalent (weight|mass)", "+atomic mass|molecular mass|molar mass|avogadro",
       "+percentage (composition|yield|purity)", "+law of (conservation of mass|definite proportion|multiple proportion)", "+at stp|at s\\.t\\.p", "+mass of .{0,30}(produced|formed|required)|how many (grams|moles)",
       "+molarity|molality|normality|mole fraction", "+gaseous mixture", "+reduced to|is passed over|is burnt", "mole", "+litre|volume of"]),
    _cm_T("Gaseous state",
      ["States of Matter", "Gaseous State", "Gaseous and Liquid States", "Some Basic Concepts in Chemistry", "Some Basic Concepts of Chemistry"],
      ["++ideal gas|boyle|charles|gay[- ]?lussac|graham|dalton'?s law of partial|van der waals|compressibility", "+critical (temperature|pressure)|liquefaction", "+kinetic (molecular )?theory|rms speed|average speed",
       "+partial pressure", "++open vessel|vessel is heated|air (in it )?is expelled", "+pressure and temperature|volume remains constant"]),
    _cm_T("Atomic structure",
      ["Atomic Structure", "Structure of Atom"],
      ["++atomic (structure|orbital|model)", "++quantum number", "++bohr", "++de[- ]?broglie|heisenberg", "++aufbau|hund|pauli", "+electronic configuration", "+orbitals?\\b|subshell|shell",
       "++unpaired electrons?", "+spin[- ]only|magnetic moment", "+wavelength of .{0,30}electron|kinetic energy of an electron", "+hydrogen (spectrum|atom)|balmer|lyman|paschen", "+radial|nodes",
       "+isoelectronic|isotope|isobar", "+rutherford|thomson|photoelectric", "+at\\.? ?nos?\\.?"]),
    _cm_T("Chemical bonding",
      ["Chemical Bonding and Molecular Structure", "Chemical Bonding", "Chemical Bonding & Molecular Structure"],
      ["++hybridi[sz]ation|hybrid orbital", "++vsepr|bond (order|angle|length|energy|enthalpy)", "++dipole moment", "++molecular orbital|bonding molecular|antibonding", "+sigma|pi bond",
       "+shape of|geometry of|structure of (the )?(molecule|ion)", "+square[- ]planar|tetrahedral|octahedral|trigonal|pyramidal|see[- ]?saw|linear|bent", "+lone pair",
       "+ionic (bond|character)|covalent|hydrogen bond|fajan", "+polar|non-?polar", "+lattice (energy|enthalpy)", "+resonance structure|resonance hybrid", "+paramagnetic|diamagnetic",
       "+lowest dipole|zero dipole"]),
    _cm_T("Chemical thermodynamics",
      ["Chemical Thermodynamics", "Thermodynamics"],
      ["++enthalpy of (neutrali[sz]ation|formation|combustion|atomi[sz]ation|solution|ionisation|hydration|vapori[sz]ation|fusion)", "++enthalpy|entropy|gibbs", "++hess'?s? law", "+heat of|calorimeter",
       "+spontaneous", "+internal energy|first law", "+delta ?[hgsu]\\b|standard state", "+adiabatic|isothermal|reversible process", "+bond enthalpy"]),
    _cm_T("Solutions",
      ["Solutions", "Solution"],
      ["++raoult", "++vapou?r pressure", "++colligative", "++molality|mole fraction", "++osmotic|osmosis", "solution", "+elevation (of|in) boiling|depression (of|in) freezing|boiling point elevation|freezing point depression",
       "+van'?t hoff", "+ideal solution|non-?ideal|azeotrope", "+henry'?s law", "+solute|solvent|aqueous solution", "+ebullioscopic|cryoscopic|abnormal molar mass", "molarity"]),
    _cm_T("Chemical & ionic equilibrium",
      ["Equilibrium", "Chemical Equilibrium", "Ionic Equilibrium"],
      ["++equilibrium constant|k ?p\\b|k ?c\\b", "++le chatelier", "++solubility product|ksp", "++degree of dissociation|percentage dissociation|dissociation of", "++ph of|\\bph\\b|poh",
       "+buffer", "+hydrolysis", "+ionisation constant|ionization constant|\\bka\\b|\\bkb\\b|ionic product", "+common ion", "+(strong|weak) (acid|base)", "+precipitat", "+equilibri", "+bronsted|lewis (acid|base)"]),
    _cm_T("Electrochemistry & redox",
      ["Redox Reactions and Electrochemistry", "Electrochemistry", "Redox Reactions"],
      ["++electrode potential|standard potential|standard electrode|reduction potential", "++electrolysis|electrolyt|electroly[sz]ed", "++cathode|anode", "++galvanic|electrochemical cell|daniell",
       "++nernst", "+emf of (the )?cell|cell (potential|reaction)", "+conductance|conductivity|kohlrausch", "+faraday", "+oxidation (number|state)", "+redox|oxidi[sz]ing agent|reducing agent|disproportionation",
       "+corrosion|fuel cell|dry cell|lead storage", "+deposition"]),
    _cm_T("Chemical kinetics",
      ["Chemical Kinetics"],
      ["++order of (the )?reaction|rate law|rate constant|rate of (the )?reaction", "++half[- ]?life|t ?1/2", "++activation energy|arrhenius", "+(first|second|zero|third)[- ]order|pseudo", "+molecularity",
       "+rate[- ]determining", "+integrated rate", "+initial concentration"]),
    _cm_T("Periodic table & periodicity",
      ["Classification of Elements and Periodicity in Properties", "Periodic Classification", "Periodic Table"],
      ["++periodic (table|trend|property|properties|law)", "++ionisation (energy|enthalpy|potential)|ionization (energy|enthalpy)", "++electron (affinity|gain enthalpy)|electronegativity",
       "+atomic (radius|radii|size)|ionic (radius|radii|size)", "+diagonal relationship", "+similar properties|atomic numbers?", "+isoelectronic", "+group\\b.{0,20}period"]),
    _cm_T("s-block elements & hydrogen",
      ["s-Block Elements", "s Block Elements", "The s-Block Elements", "Hydrogen", "Classification of Elements and Periodicity in Properties"],
      ["++alkali metal|alkaline earth|s-?block", "++(react|reacts) (most )?vigorously with water|reactivity with water", "+sodium|potassium|lithium|rubidium|caesium|magnesium|calcium|beryllium",
       "+quicklime|slaked lime|plaster of paris|washing soda|baking soda|caustic soda", "+hydride|heavy water|hydrogen peroxide|h2o2", "\\b(li|na|rb|cs)\\b"]),
    _cm_T("p-block elements",
      ["p- BLOCK ELEMENTS", "p-Block Elements", "p Block Elements"],
      ["++p-?block", "++group[- ](13|14|15|16|17|18)", "++halogen|noble gas|interhalogen", "++xenon|xef|xeo|xe\\b", "+oxoacid|oxyacid|oxide", "+ozone|sulphuric acid|nitric acid|phosphor|phosphine|ammonia",
       "+boron|borax|diborane|silicon|silicone|carbon monoxide|allotrope|graphite|diamond|fullerene", "chlorine|fluorine|bromine|iodine|sulphur|nitrogen family|oxygen family", "+hno3|h2so4|h3po4|hclo"]),
    _cm_T("d & f block elements",
      ["d and f- BLOCK ELEMENTS", "d and f Block Elements", "d- and f-Block Elements"],
      ["++d-? ?and f|transition (element|metal)|lanthanoid|actinoid|lanthanide|inner transition", "++kmno4|k2cr2o7|potassium (permanganate|dichromate)", "+lanthanoid contraction",
       "+coloured (ions|compounds)|colou?r of", "+variable oxidation|magnetic moment", "\\b(mn|cr|fe|cu|zn|ti|sc|ni)\\b"]),
    _cm_T("Coordination compounds",
      ["Coordination Compounds"],
      ["++coordination (compound|complex|number|sphere|entity|isomer)", "++ligand", "++spectrochemical|crystal field|cfse|splitting", "+cis[- ]?trans|geometrical isomer|linkage isomer|ionisation isomer|ambidentate|chelat|werner",
       "++\\[[a-z]{1,2}[a-z0-9()]*\\]", "+complex (ion|compound)|hybridi[sz]ation of (the )?(central|metal)", "+ptcl|nicl|cocl|k4\\[|k3\\[",
       "+square[- ]planar|octahedral|tetrahedral"]),
    _cm_T("Metallurgy",
      ["General Principles and Processes of Isolation of Elements", "Metallurgy", "Isolation of Elements"],
      ["++metallurgy|isolation of (elements|metals)", "++roasting|calcination|smelting|froth flotation|leaching|zone refining|van arkel", "+ore\\b|ores\\b|zinc blende|bauxite|haematite|hematite|galena|pyrites|cinnabar|malachite",
       "+extraction of|self[- ]reduction|blast furnace|ellingham|slag|flux"]),
    _cm_T("Solid state",
      ["Solid State", "The Solid State"],
      ["++unit cell|crystal lattice|solid state", "++body[- ]cent(re|er)d|face[- ]cent(re|er)d|simple cubic|\\bbcc\\b|\\bfcc\\b|\\bhcp\\b|\\bccp\\b", "+packing|voids?\\b|interstitial|schottky|frenkel",
       "+edge length|radius ratio", "+ionic solid|crystalline|amorphous|lattice"]),
    _cm_T("Surface chemistry",
      ["Surface Chemistry"],
      ["++colloid", "++gold number|coagulation|peptization|tyndall|brownian|electrophoresis|dialysis|hardy[- ]schulze",
       "++adsorption|freundlich", "+emulsion|micelle|aerosol|lyophilic|lyophobic|dispersed|dispersion medium",
       "+\\bsol\\b|\\bgel\\b|\\bfog\\b|smoke|catalysis|catalyst"]),
    _cm_T("Environmental chemistry",
      ["Environmental Chemistry"],
      ["++pollution|pollutant|greenhouse|ozone (layer|depletion)|acid rain|smog|global warming|bod\\b|cod\\b"]),
    _cm_T("Purification & characterisation of organic compounds",
      ["PURIFICATION AND CHARACTERISATION OF ORGANIC COMPOUNDS", "Purification and Characterisation of Organic Compounds"],
      ["++beilstein|lassaigne|sodium fusion|kjeldahl|dumas|carius", "++chromatograph|crystalli[sz]ation|distillation|sublimation|steam distillation", "+qualitative analysis|quantitative analysis|estimation of",
       "+detection of (nitrogen|sulphur|halogen|carbon|hydrogen)"]),
    _cm_T("General organic chemistry",
      ["SOME BASIC PRINCIPLES OF ORGANIC CHEMISTRY", "Some Basic Principles of Organic Chemistry", "Organic Chemistry - Basics", "General Organic Chemistry"],
      ["++iupac|nomenclature", "++isomer", "++inductive|mesomeric|hyperconjugation|electromeric|resonance effect", "++carbocation|carbanion|free radical|carbene", "+electrophile|nucleophile",
       "+homolytic|heterolytic", "+stability of", "+optical|chiral|enantiomer|geometrical|\\([ezrs]\\)-", "+functional group", "+yne\\b|-ene\\b|hept|pent[ae]n"]),
    _cm_T("Hydrocarbons",
      ["HYDROCARBONS", "Hydrocarbons"],
      ["++alkane|alkene|alkyne|benzene|arene|aromatic|hydrocarbon", "++photobromination|photochlorination|halogenation of|free radical (substitution|halogenation)", "++markovnikov|peroxide effect|ozonolysis",
       "++wurtz|friedel|crafts", "++nbs|n-?bromosuccin[ai]mide", "+ethyl ?benzene|toluene|xylene|naphthalene|methylbutane|butane|propane|ethane|pentane|hexane|propene|ethene|propyne|ethyne|cyclo",
       "+cracking|reforming", "+conformation|staggered|eclipsed", "+hydrogenation|dehydrohalogenation|electrophilic substitution|benzylic"]),
    _cm_T("Haloalkanes & haloarenes",
      ["ORGANIC COMPOUNDS CONTAINING HALOGENS", "Haloalkanes and Haloarenes"],
      ["++alkyl halide|haloalkane|haloarene|aryl halide", "++sn1|sn2|nucleophilic substitution", "++grignard", "+chloroform|iodoform|carbon tetrachloride|ddt|freon", "+walden|finkelstein|swarts|sandmeyer", "+elimination"]),
    _cm_T("Alcohols, phenols, carbonyls & acids",
      ["ORGANIC COMPOUNDS CONTAINING OXYGEN"],
      ["++alcohol|phenol|ether\\b|ethers\\b", "++aldehyde|ketone|carboxylic|ester\\b|esters\\b|anhydride|acid chloride", "++aldol|cannizzaro|clemmensen|wolff|rosenmund|etard|reimer|hell[- ]volhard",
       "+acrolein|acetone|acetaldehyde|formaldehyde|benzaldehyde|acetic acid|formic acid|benzoic|salicylic|aspirin|lucas|esterification", "+allyl|glycerol|glycol", "+carbonyl|tollen|fehling|schiff",
       "+pcc|jones reagent|oxidation of"]),
    _cm_T("Amines & nitrogen compounds",
      ["ORGANIC COMPOUNDS CONTAINING NITROGEN"],
      ["++amine|aniline|diazonium|nitro ?compound|nitrobenzene|nitrile|isocyanide|cyanide|amide\\b", "++basicity|basic (strength|character)|pkb", "+hoffmann|hofmann|gabriel|carbylamine|hinsberg|coupling", "+pyridine|pyrrole|piperidine|morpholine|azo"]),
    _cm_T("Biomolecules",
      ["BIOMOLECULES"],
      ["++carbohydrate|amino acid|protein|peptide|zwitterion|nucleic", "+glucose|fructose|sucrose|lactose|maltose|starch|cellulose|glycogen", "+vitamin|hormone|enzyme|\\bdna\\b|\\brna\\b|nucleotide",
       "+reducing sugar|anomer|glycosidic|mutarotation|pyranose|furanose|osazone", "+denaturation|lipid|\\bfats?\\b"]),
    _cm_T("Polymers",
      ["Polymers", "Polymer"],
      ["++polymer|polyamide|polyester|nylon|terylene|teflon|orlon|bakelite|buna|neoprene|polythene|\\bpvc\\b|vulcani[sz]ation|monomer", "+addition polymer|condensation polymer|copolymer"]),
    _cm_T("Chemistry in everyday life",
      ["Chemistry in Everyday Life"],
      ["++drug|antacid|antibiotic|analgesic|antiseptic|disinfectant|detergent|soap|preservative|sweetener|tranquili[sz]er|antihistamine"]),
    _cm_T("Practical chemistry",
      ["PRINCIPLES RELATED TO PRACTICAL CHEMISTRY", "Practical Chemistry"],
      ["++titration|indicator|end point|volumetric|burette|pipette", "++salt analysis|confirmatory test|flame test|group reagent|brown ring", "+mohr'?s salt|potash alum|double salt", "+practical"]),
]

_cm_MATHEMATICS = [
    _cm_T("Sets, relations & functions",
      ["Sets, Relations and Functions", "Sets Relations and Functions", "Relations and Functions", "Sets and Functions"],
      ["++subsets?|power set|cardinal|p ?\\(s\\)", "++relation|reflexive|symmetric relation|transitive|equivalence", "++one[- ]to[- ]one|onto function|bijective|injective|surjective|codomain|composite function|inverse function|domain",
       "+one[- ]one|many[- ]one|onto\\b|into function", "+f ?: ?[a-z\\[\\]0-9,]+ ?(→|rightarrow) ?[a-z]", "\\bsets?\\b", "function", "range of"]),
    _cm_T("Complex numbers",
      ["Complex Numbers and Quadratic Equations", "Complex Numbers", "Complex Numbers & Quadratic Equations"],
      ["++complex (number|root|plane)|imaginary|conjugate|argand|de moivre|cube roots? of unity|iota", "++arg ?[a-z]|argument of|principal argument|amp\\b", "+modulus|\\|[zw]\\d?\\||z ?bar|omega", "+real and imaginary", "+\\bz ?= ?\\d*\\.?\\d* ?[+-] ?\\d*i\\b"]),
    _cm_T("Quadratic equations",
      ["Complex Numbers and Quadratic Equations", "Quadratic Equations", "Quadratic Equations and Inequalities"],
      ["++quadratic (equation|expression|polynomial)|discriminant", "++(sum|product) of (the )?roots|nature of (the )?roots|real roots|equal roots|roots of the (equation|polynomial)", "+ax2 ?\\+ ?bx ?\\+ ?c|px2 ?\\+ ?qx ?\\+ ?r|x2 ?[-+] ?\\d*x ?[-+] ?\\d+ ?= ?0",
       "+cubic|biquadratic|polynomial", "+rolle"]),
    _cm_T("Matrices & determinants",
      ["Matrices and Determinants", "Matrices & Determinants", "Matrices", "Determinants"],
      ["++matrix|matrices|determinant|adjoint|\\badj\\b", "++transpose|singular|inverse of (a )?matrix|skew[- ]symmetric|orthogonal matrix|cramer|eigen|\\btrace\\b", "+system of (linear )?equations|consistent|unique solution",
       "++\\bab ac\\b|\\bac bc\\b|\\bab bc\\b|\\bbc ab\\b"]),   # rows of a symmetric determinant, e.g. | b2+c2  ab  ac |
    _cm_T("Permutations & combinations",
      ["Permutations and Combinations", "Permutation and Combination"],
      ["++permutation|combination|arrangements?|factorial|number of ways|ways (can|to|in which)", "++selection|committee|circular arrangement|derangement|distribution of|distinct (objects|balls)|letters of the word|vowel|consonant",
       "++[mnr](?:[+-]\\d)? ?c ?\\d\\b|\\bncr\\b|\\bnpr\\b", "+n!|\\d!"]),
    _cm_T("Mathematical induction",
      ["Mathematical Induction"],
      ["++induction|by induction", "+divisible by|for all natural numbers"]),
    _cm_T("Binomial theorem",
      ["Binomial Theorem and its Simple Applications", "Binomial Theorem"],
      ["++binomial (theorem|expansion|coefficient)", "++coefficient of x|general term|middle term|independent of x|greatest (coefficient|term)", "+\\(1 ?\\+ ?x\\)|expansion of", "+pascal"]),
    _cm_T("Sequences & series",
      ["Sequences and Series", "Sequence and Series", "Progressions"],
      ["++arithmetic progression|geometric progression|harmonic progression|\\ba\\.?p\\.?\\b|\\bg\\.?p\\.?\\b|\\bh\\.?p\\.?\\b", "++series", "++sum of (the )?(first )?n terms|upto n terms|n terms|nth term|common (ratio|difference)",
       "+arithmetic mean|geometric mean|\\bam\\b|\\bgm\\b|\\bhm\\b", "+infinite (series|gp)|sequence", "+terms"]),
    _cm_T("Limits, continuity & differentiability",
      ["Limit, Continuity and Differentiability", "Limits, Continuity and Differentiability", "Limits Continuity and Differentiability", "Differential Calculus"],
      ["++limit|\\blim ?(x|h|n|t|alpha)|\\bli ?m ?(alpha|x|h)", "++continuity|continuous|discontinuous|differentiab", "++derivative|differentiate|f ?'|dy ?/ ?dx", "+rolle|lagrange|mean value theorem", "+l'?hospital|greatest integer function",
       "+lim.{0,10}(x|alpha|h)"]),
    _cm_T("Applications of derivatives",
      ["Application of Derivatives", "Applications of Derivatives", "Limit, Continuity and Differentiability", "Limits, Continuity and Differentiability", "Differential Calculus"],
      ["++maxima|minima|maximum value|minimum value|monoton|increasing|decreasing", "++rate of change|rate at which|tangent to the curve|normal to the curve", "+radius of (a )?(sphere|circle|balloon)|volume is increasing|with respect to t"]),
    _cm_T("Integral calculus",
      ["Integral Calculus", "Integrals", "Integration"],
      ["++integral", "++integrate|integration|antiderivative|primitive", "++area (bounded|under|enclosed|of the region)|region bounded|bounded by (the )?(curve|lines?)|enclosed by", "+\\bdx\\b|\\bdt\\b|\\bd theta\\b", "+definite|indefinite", "+greatest integer"]),
    _cm_T("Differential equations",
      ["Differential Equations"],
      ["++differential equation|order and degree|integrating factor|homogeneous differential|linear differential", "++general solution|particular solution|solution of the differential", "+dy ?/ ?dx|dy dx|dx ?/ ?dy", "+variable separable|orthogonal trajector|family of (curves|circles|parabolas)"]),
    _cm_T("Straight lines",
      ["Straight Lines", "Co-ordinate Geometry", "Coordinate Geometry", "Coordinate Geometry (Straight Lines, Circles, Conics)"],
      ["++straight line|line y ?=|equation of the (line|normal)|slope|intercept|angle between (the )?lines", "+centroid|circumcent(re|er)|orthocent(re|er)|incent(re|er)|collinear points?|section formula|ratio in which|mid-?point",
       "+image of (the )?point|reflection of (the )?point|foot of (the )?perpendicular|distance of (a )?point|equidistant", "+triangle|vertices|quadrilateral|locus|x-?axis|y-?axis|origin", "+pair of (straight )?lines"]),
    _cm_T("Circles",
      ["Circles", "Co-ordinate Geometry", "Coordinate Geometry", "Coordinate Geometry (Straight Lines, Circles, Conics)"],
      ["++circle", "+x2 ?\\+ ?y2|radius|centre of|center of", "+tangent to|chord|common chord|orthogonal circles|radical axis|director circle"]),
    _cm_T("Conic sections",
      ["Conic Sections", "Parabola, Ellipse and Hyperbola", "Co-ordinate Geometry", "Coordinate Geometry", "Coordinate Geometry (Straight Lines, Circles, Conics)"],
      ["++parabola|ellipse|hyperbola|conic", "++focus|foci|directrix|latus rectum|eccentricity", "+normal to the (parabola|ellipse|hyperbola)|tangent to the (parabola|ellipse|hyperbola)", "+x2 ?/ ?\\d+|x2 ?[-+] ?y2 ?/ ?\\d+|x2 \\d+ [+-] y2"]),
    _cm_T("Three dimensional geometry",
      ["Three Dimensional Geometry", "3D Geometry", "Three Dimensional Geometry"],
      ["++direction (cosines|ratios)|skew lines|shortest distance|planes\\b|common line|three planes|coplanar lines", "+\\bplane\\b", "+x ?-? ?\\d+ ?/ ?\\d+|x ?\\d+ ?= ?y|x[^a-z]{0,12}= ?y[^a-z]{0,12}= ?z", "+sphere|line in space|angle between (a )?(line|plane)"]),
    _cm_T("Vector algebra",
      ["Vector Algebra", "Vectors"],
      ["++vector|unitvector|dot product|cross product|scalar triple|coplanar|position vector", "++angle between (the )?(two )?(vectors|a and b)", "+parallel to the plane of|projection|magnitude|\\|a\\||\\|b\\||\\|c\\|", "+a ?\\+ ?b ?\\+ ?c ?= ?0"]),
    _cm_T("Statistics",
      ["Statistics and Probability", "Statistics"],
      ["++median|mean deviation|variance|standard deviation|frequency distribution|class interval|dispersion", "+observations?|\\bmode\\b|mean of", "+grouped|classes"]),
    _cm_T("Probability",
      ["Statistics and Probability", "Probability"],
      ["++probability|bayes|conditional|independent events|mutually exclusive|random variable|bernoulli", "+dice|die\\b|coin|cards?\\b|drawn|at random|expected value", "+stand in a row|arranged in a row|separated"]),
    _cm_T("Trigonometry",
      ["Trigonometry", "Trigonometric Functions", "Trigonometry and Inverse Trigonometric Functions"],
      ["++trigonometric|height and distance|angle of elevation|angle of depression", "++\\b(sin|cos|tan|sec|cosec|csc|cot)\\b", "+identity|identities|principal solution|general solution of", "+theta|phi\\b", "+triangle abc|sine rule|cosine rule|circumradius|inradius"]),
    _cm_T("Inverse trigonometric functions",
      ["Inverse Trigonometric Functions", "Trigonometry", "Trigonometric Functions"],
      ["++(sin|cos|tan|cot|sec|cosec)-1|inverse trigonometric|arcsin|arccos|arctan", "+principal value"]),
    _cm_T("Mathematical reasoning",
      ["Mathematical Reasoning", "Logic", "Mathematical Logic"],
      ["++tautology|contradiction|negation|converse|contrapositive|truth table|logically|biconditional", "++equivalent to|statements?\\b", "+p ?[∧∨→↔] ?q|[∧∨∼~] ?q|∼|~ ?p", "+implication|compound statement"]),
]

_cm_TAXONOMY = {
    "physics": _cm_PHYSICS,
    "chemistry": _cm_CHEMISTRY,
    "mathematics": _cm_MATHEMATICS,
    "maths": _cm_MATHEMATICS,
    "math": _cm_MATHEMATICS,
}


def _cm_supports(subject_name) -> bool:
    return (subject_name or "").strip().lower() in _cm_TAXONOMY


# ─────────────────────────────────────────────────────────────
# 3. RESOLVING a topic -> a real Chapter row from the DB
# ─────────────────────────────────────────────────────────────

def _cm__name_key(name: str) -> str:
    s = (name or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _cm__find_chapter(alias: str, chapters: list):
    """chapters = [(chapter_id, chapter_name), ...] -> matching tuple or None"""
    a = _cm__name_key(alias)
    a_tokens = set(a.split())
    # 1) exact
    for c in chapters:
        if _cm__name_key(c[1]) == a:
            return c
    # 2) token containment (only for multi-word names -> avoids "Waves" ~ "Electromagnetic Waves")
    for c in chapters:
        c_tokens = set(_cm__name_key(c[1]).split())
        small, big = (a_tokens, c_tokens) if len(a_tokens) <= len(c_tokens) else (c_tokens, a_tokens)
        if len(small) >= 3 and small <= big:
            return c
    # 3) fuzzy spelling difference (token by token; short tokens such as the
    #    "s" / "p" in "s-block" / "p-block" must match exactly)
    for c in chapters:
        c_list = _cm__name_key(c[1]).split()
        a_list = a.split()
        if len(a_list) != len(c_list):
            continue
        if all(x == y or (len(x) > 3 and len(y) > 3 and difflib.SequenceMatcher(None, x, y).ratio() >= 0.85)
               for x, y in zip(a_list, c_list)):
            return c
    return None


# ─────────────────────────────────────────────────────────────
# 4. Optional learned booster (Naive Bayes on your own verified questions)
# ─────────────────────────────────────────────────────────────

_cm__TOKEN = re.compile(r"[a-z][a-z0-9']{2,}")
_cm__STOP = set("the and for are with that this from which what following value then have has was were its their "
            "will can not all any one two three four given find correct answer question option none".split())


def _cm__tokens(text):
    return [w for w in _cm__TOKEN.findall(_cm_normalize(text)) if w not in _cm__STOP]


class _cm_LearnedBooster:
    """
    Multinomial Naive Bayes over words. fit() takes [(question_text, chapter_id)].
    predict() -> (chapter_id, probability) or (None, 0).
    Pure python. Small on purpose: it only nudges / rescues the rule engine.
    """

    MIN_SAMPLES = 60
    MIN_CHAPTERS = 3

    def __init__(self):
        self.ready = False

    def fit(self, samples):
        self.class_docs = Counter()
        self.word_counts = defaultdict(Counter)
        self.class_words = Counter()
        vocab = set()
        for text, cid in samples:
            toks = _cm__tokens(text)
            if not toks:
                continue
            self.class_docs[cid] += 1
            self.word_counts[cid].update(toks)
            self.class_words[cid] += len(toks)
            vocab.update(toks)
        self.vocab_size = max(len(vocab), 1)
        self.total_docs = sum(self.class_docs.values())
        self.ready = self.total_docs >= self.MIN_SAMPLES and len(self.class_docs) >= self.MIN_CHAPTERS
        return self.ready

    def predict(self, text):
        if not self.ready:
            return None, 0.0
        toks = _cm__tokens(text)
        if not toks:
            return None, 0.0
        logp = {}
        for cid, n_docs in self.class_docs.items():
            lp = math.log(n_docs / self.total_docs)
            denom = self.class_words[cid] + self.vocab_size
            wc = self.word_counts[cid]
            for w in toks:
                lp += math.log((wc.get(w, 0) + 1) / denom)
            logp[cid] = lp
        m = max(logp.values())
        exp = {c: math.exp(v - m) for c, v in logp.items()}
        z = sum(exp.values())
        best = max(exp, key=exp.get)
        return best, exp[best] / z


# ─────────────────────────────────────────────────────────────
# 5. The mapper
# ─────────────────────────────────────────────────────────────

_cm_MAPPED_MIN_CONFIDENCE = 60      # >= this  -> status "mapped"
_cm_REVIEW_MIN_CONFIDENCE = 25      # >= this  -> "needs_review", below -> "unmapped"


class _cm_ChapterMapper:
    """
    mapper = ChapterMapper("Physics", [(23, "Rotational Motion"), (24, "Gravitation"), ...])
    mapper.classify(question_dict) -> {
        chapter_id, chapter_name, topic, confidence, status, matched_keywords, runner_up, source
    }
    """

    def __init__(self, subject_name, chapters, booster: _cm_LearnedBooster = None):
        self.subject_name = subject_name
        self.topics = _cm_TAXONOMY[(subject_name or "").strip().lower()]
        # ignore the catch-all bucket when resolving
        self.chapters = [c for c in chapters if "imported" not in c[1].lower()]
        self.booster = booster if booster and booster.ready else None
        # topic label -> (chapter_id, chapter_name) or None if the DB has no such chapter
        self.resolved = {}
        for t in self.topics:
            hit = None
            for alias in t.aliases:
                hit = _cm__find_chapter(alias, self.chapters)
                if hit:
                    break
            self.resolved[t.label] = hit

    # -- scoring ---------------------------------------------------------
    def _score_topic(self, topic, stem, opts, stem_letters):
        score, matched = 0.0, []
        for pat, weight, raw, literals in topic.rules:
            label = raw.split("|")[0].replace("\\b", "").replace("\\", "")[:30]
            if pat.search(stem):
                score += weight
            elif opts and pat.search(opts):
                score += weight * 0.5
            elif weight > 0 and any(lit in stem_letters for lit in literals):
                score += weight * 0.7          # garbled text, found spaceless
            else:
                continue
            if weight > 0:
                matched.append(label)
        return score, matched

    def classify(self, q: dict) -> dict:
        empty = {"chapter_id": None, "chapter_name": None, "topic": None, "confidence": 0,
                 "status": "unmapped", "matched_keywords": [], "runner_up": None, "source": "rules"}
        stem, opts = _cm__question_parts(q)
        if not stem and not opts:
            return empty

        stem_letters = re.sub(r"[^a-z]", "", stem)
        topic_scores = []
        for t in self.topics:
            s, m = self._score_topic(t, stem, opts, stem_letters)
            if s > 0:
                topic_scores.append((s, t, m))
        topic_scores.sort(key=lambda x: -x[0])

        # Learned booster (optional)
        nb_cid, nb_p = (None, 0.0)
        if self.booster:
            nb_cid, nb_p = self.booster.predict((q.get("question_text") or "") + " " + opts)

        if not topic_scores:
            return self._from_booster_only(nb_cid, nb_p, empty)

        best_topic_score, best_topic, _ = topic_scores[0]

        # combine topics that resolve to the SAME chapter: max + 25% of the rest
        by_chapter = defaultdict(list)
        for s, t, m in topic_scores:
            res = self.resolved.get(t.label)
            if res:
                by_chapter[res].append((s, t, m))
        chap_rows = []
        for res, rows in by_chapter.items():
            rows.sort(key=lambda r: -r[0])
            total = rows[0][0] + 0.25 * sum(r[0] for r in rows[1:])
            if nb_cid is not None and nb_p >= 0.6 and res[0] == nb_cid:
                total += 3.0                       # learned model agrees -> small boost
            chap_rows.append((total, res, rows[0][1], rows[0][2]))
        chap_rows.sort(key=lambda r: -r[0])

        # the strongest topic has NO chapter in this exam's DB (e.g. "Polymers"
        # in a syllabus that dropped it) -> don't force a weaker wrong chapter.
        unresolved_best = self.resolved.get(best_topic.label) is None
        if not chap_rows or (unresolved_best and chap_rows[0][0] <= best_topic_score):
            out = dict(empty)
            out["topic"] = best_topic.label
            out["matched_keywords"] = topic_scores[0][2][:6]
            out["confidence"] = 0
            return out

        top, res, topic, matched = chap_rows[0]
        second = chap_rows[1][0] if len(chap_rows) > 1 else 0.0
        strength = 1 - math.exp(-top / 6.0)
        margin = (top - second) / top if top else 0
        confidence = int(round(100 * strength * (0.55 + 0.45 * margin)))
        confidence = max(0, min(99, confidence))

        status = ("mapped" if confidence >= _cm_MAPPED_MIN_CONFIDENCE
                  else "needs_review" if confidence >= _cm_REVIEW_MIN_CONFIDENCE else "unmapped")
        runner = None
        if len(chap_rows) > 1:
            runner = {"chapter_id": chap_rows[1][1][0], "chapter_name": chap_rows[1][1][1]}

        return {
            "chapter_id": res[0] if status != "unmapped" else None,
            "chapter_name": res[1] if status != "unmapped" else None,
            "topic": topic.label,
            "confidence": confidence,
            "status": status,
            "matched_keywords": matched[:6],
            "runner_up": runner,
            "source": "rules",
        }

    def _from_booster_only(self, nb_cid, nb_p, empty):
        """Rules found nothing at all -> trust the learned model only if it is very sure."""
        if nb_cid is not None and nb_p >= 0.75:
            for cid, name in self.chapters:
                if cid == nb_cid:
                    conf = int(min(70, nb_p * 70))
                    return {"chapter_id": cid, "chapter_name": name, "topic": None,
                            "confidence": conf, "status": "needs_review", "matched_keywords": [],
                            "runner_up": None, "source": "learned"}
        return empty


def _cm_build_mapper(subject_name, chapters, booster=None):
    """chapters: iterable of (chapter_id, chapter_name). Returns None if subject unsupported."""
    if not _cm_supports(subject_name):
        return None
    return _cm_ChapterMapper(subject_name, list(chapters), booster)


_build_chapter_mapper = _cm_build_mapper
_mapper_supports      = _cm_supports
_LearnedBooster       = _cm_LearnedBooster

# Train a tiny Naive-Bayes from questions already saved in this exam's chapters
# and let it nudge / rescue the rules.  Needs >= 60 saved questions spread over
# >= 3 chapters of the subject, otherwise it silently stays off.
USE_LEARNED_BOOSTER = True

_SUBJECT_SYNONYMS = {"maths": "Mathematics", "math": "Mathematics"}


def _find_subject(exam, subject_name):
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


def _learned_booster_for(subject):
    if not USE_LEARNED_BOOSTER:
        return None
    try:
        rows = (
            Question.objects
            .filter(chapter__subject=subject, is_active=True)
            .exclude(chapter__chapter_name__icontains="imported")
            .values_list("question_text", "chapter_id")[:6000]
        )
        booster = _LearnedBooster()
        return booster if booster.fit(list(rows)) else None
    except Exception:
        return None


def _apply_mapping(q, result, source):
    q["chapter_id"]          = result.get("chapter_id")
    q["chapter_name"]        = result.get("chapter_name")
    q["topic"]               = result.get("topic")
    q["mapping_confidence"]  = result.get("confidence", 0)
    q["mapping_status"]      = result.get("status", "unmapped")
    q["matched_keywords"]    = result.get("matched_keywords", [])
    q["runner_up"]           = result.get("runner_up")
    q["mapping_source"]      = result.get("source", source)


MAX_QUESTIONS_PER_AI_CALL = 50


def _parse_ai_chapter_response(response_text: str, valid_ids: set) -> dict:
    """
    Parse 'Q<n>: <id>' lines.
    Ignore any chapter_id not in valid_ids (hallucination guard).
    Returns {index -> chapter_id} (0-based, so Q1 -> index 0)
    """
    result = {}
    if not response_text:
        return result
    for line in response_text.strip().splitlines():
        line = line.strip()
        m = re.search(r"Q(\d+)\s*[:=\-]\s*(\d+)", line, re.IGNORECASE)
        if not m:
            continue
        try:
            q_num = int(m.group(1)) - 1
            chap_id = int(m.group(2))
            if chap_id == 0 or chap_id in valid_ids:
                result[q_num] = chap_id
        except (ValueError, TypeError):
            continue
    return result


def _ai_map_questions_batch(subject_name, exam_name, chapters, questions):
    """
    Sends batched prompts to OpenRouter.
    Returns a mapping of question list index -> chapter_id.
    """
    api_key = getattr(settings, "OPENROUTER_API_KEY", "")
    if not api_key or not questions or not chapters:
        return {}

    valid_ids = {cid for cid, _ in chapters}
    chapter_list = "\n".join(f"{cid}. {name}" for cid, name in chapters)
    results = {}

    for chunk_start in range(0, len(questions), MAX_QUESTIONS_PER_AI_CALL):
        chunk = questions[chunk_start : chunk_start + MAX_QUESTIONS_PER_AI_CALL]

        q_lines = "\n".join(
            f"Q{i+1}: {(q.get('question_text') or '')[:300].strip()}"
            for i, q in enumerate(chunk)
        )

        prompt = (
            f"You are a curriculum classifier for {exam_name}.\n"
            f"Subject: {subject_name}\n\n"
            f"Available chapters (use ONLY these IDs):\n{chapter_list}\n\n"
            f"Reply with EXACTLY {len(chunk)} lines, one per question, and NOTHING else -\n"
            f"no reasoning, no notes, no markdown, no headers.\n"
            f"Each line must be in the literal form: Q<n>: <chapter_id>\n"
            f"If unclear or not in list, output: Q<n>: 0\n\n"
            f"Questions:\n{q_lines}"
        )

        try:
            resp = requests.post(
                getattr(settings, "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": getattr(settings, "OPENROUTER_SITE_URL", "https://nxtturn.com"),
                    "X-Title": getattr(settings, "OPENROUTER_SITE_NAME", "NxtTurn Exam Admin"),
                },
                json={
                    "model": getattr(settings, "OPENROUTER_MODEL", "openrouter/free"),
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 5000,
                    "temperature": 0,
                    # Disables chain-of-thought output on reasoning-capable models -
                    # openrouter/free routes to a random free model per call, and some
                    # of those are reasoning models that otherwise burn max_tokens on
                    # hidden "thinking" before ever writing the actual Q<n>: <id> lines.
                    "reasoning": {"enabled": False},
                },
                timeout=35,
            )
            if resp.status_code == 200:
                data = resp.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                content = msg.get("content") or msg.get("reasoning") or ""
                chunk_result = _parse_ai_chapter_response(content, valid_ids)
                if len(chunk_result) < len(chunk):
                    logger.warning(
                        "AI mapping for '%s' chunk only parsed %d/%d questions: %r",
                        subject_name, len(chunk_result), len(chunk), content[:300],
                    )
                for local_idx, chap_id in chunk_result.items():
                    results[chunk_start + local_idx] = chap_id
            else:
                logger.warning("OpenRouter API returned status %s: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("AI chapter mapping failed for '%s': %s", subject_name, e)

    return results


def _auto_map_questions(exam, questions) -> dict:
    """
    Fills chapter_id / chapter_name / topic / mapping_confidence / mapping_status
    on every question dict IN PLACE (questions the admin fixed by hand -
    mapping_source == "manual" - are left alone).
    """
    by_subject = _defaultdict(list)
    for q in questions:
        by_subject[(q.get("subject") or "").strip()].append(q)

    api_key = getattr(settings, "OPENROUTER_API_KEY", "")
    subject_debug = {}   # ← NEW: one entry per subject explaining what happened

    for subject_name, qs in by_subject.items():
        subject  = _find_subject(exam, subject_name)
        chapters = list(
            Chapter.objects.filter(subject=subject, is_active=True)
            .values_list("chapter_id", "chapter_name")
        ) if subject else []

        debug = {
            "subject_name":   subject_name or "(blank)",
            "subject_found":  subject is not None,
            "chapters_found": len(chapters),
            "api_key_present": bool(api_key),
            "ai_called":      False,
            "ai_results_count": 0,
            "reason_skipped": None,
        }

        for q in qs:
            if q.get("mapping_source") == "manual":
                continue
            _apply_mapping(q, {"status": "unmapped"}, "ai")

        if not subject:
            debug["reason_skipped"] = "no Subject row found for this exam matching the extracted subject name"
        elif not chapters:
            debug["reason_skipped"] = f"Subject '{subject.subject_name}' has 0 active chapters"
        elif not api_key:
            debug["reason_skipped"] = "OPENROUTER_API_KEY not set"
        else:
            unmapped_qs = [
                q for q in qs
                if q.get("mapping_status") in ("unmapped", "needs_review")
                and q.get("mapping_source") != "manual"
            ]
            if unmapped_qs:
                debug["ai_called"] = True
                exam_name = getattr(exam, "exam_name", "") or "Exam"
                ai_results = _ai_map_questions_batch(
                    subject_name, exam_name, chapters, unmapped_qs
                )
                debug["ai_results_count"] = len(ai_results)
                if not ai_results:
                    debug["reason_skipped"] = "AI call returned no usable results (see logs: 'AI chapter mapping failed' / 'returned status' / 'only parsed')"

                chap_lookup = dict(chapters)
                for local_idx, chapter_id in ai_results.items():
                    if chapter_id == 0 or local_idx >= len(unmapped_qs):
                        continue
                    q = unmapped_qs[local_idx]
                    chap_name = chap_lookup.get(chapter_id)
                    if chap_name:
                        _apply_mapping(q, {
                            "chapter_id": chapter_id,
                            "chapter_name": chap_name,
                            "topic": None,
                            "confidence": 75,
                            "status": "mapped",
                            "matched_keywords": [],
                        }, "ai")

        subject_debug[subject_name or "(blank)"] = debug

    return {
        "total":          len(questions),
        "mapped":         sum(1 for q in questions if q.get("mapping_status") == "mapped"),
        "needs_review":   sum(1 for q in questions if q.get("mapping_status") == "needs_review"),
        "unmapped":       sum(1 for q in questions if q.get("mapping_status") == "unmapped"),
        "subjects_count": len({q.get("subject") for q in questions if q.get("subject")}),
        "chapters_count": len({q.get("chapter_id") for q in questions if q.get("chapter_id")}),
        "topics_count":   len({q.get("topic") for q in questions if q.get("topic")}),
        "debug":          subject_debug,   # ← NEW
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def auto_map_questions_to_chapters(request, upload_id):
    """
    POST /api/pyq-import/<upload_id>/auto-map-chapters/
    Re-runs the chapter mapping for every cached question (it already runs once
    automatically at upload time - use this after changing subjects or after
    adding new chapters).  Manual overrides are kept.
    """
    cached = _get_cached_or_404(upload_id)
    if not cached:
        return Response({"error": "Upload session has expired or was not found."},
                        status=status.HTTP_404_NOT_FOUND)
    try:
        exam = Exam.objects.get(pk=cached["exam_id"])
    except Exam.DoesNotExist:
        return Response({"error": "The exam for this upload no longer exists."},
                        status=status.HTTP_404_NOT_FOUND)

    questions = cached["questions"]
    summary = _auto_map_questions(exam, questions)
    _persist(upload_id, cached)
    return Response({**summary, "questions": [_question_full(q, request) for q in questions]},
                    status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([AllowAny])
def update_question_chapter(request, upload_id, question_index):
    """
    PATCH /api/pyq-import/<upload_id>/questions/<question_index>/chapter/
    Body: {"chapter_id": 123}
    Manual override - only ever assigns an EXISTING Chapter row, and is never
    overwritten by a later auto-map run.
    """
    cached = _get_cached_or_404(upload_id)
    if not cached:
        return Response({"error": "Upload session has expired or was not found."},
                        status=status.HTTP_404_NOT_FOUND)

    questions = cached["questions"]
    try:
        q = questions[int(question_index)]
    except (IndexError, ValueError):
        return Response({"error": "Question not found in this upload."},
                        status=status.HTTP_404_NOT_FOUND)

    try:
        chapter = Chapter.objects.get(pk=request.data.get("chapter_id"))
    except (Chapter.DoesNotExist, TypeError, ValueError):
        return Response({"error": "Invalid chapter_id."}, status=status.HTTP_400_BAD_REQUEST)

    _apply_mapping(q, {
        "chapter_id": chapter.chapter_id, "chapter_name": chapter.chapter_name,
        "topic": q.get("topic"), "confidence": 100, "status": "mapped",
        "matched_keywords": [], "source": "manual",
    }, "manual")
    _persist(upload_id, cached)
    return Response(_question_full(q, request), status=status.HTTP_200_OK)

class PyqChaptersForSubjectView(APIView):
    """
    GET /api/pyq-import/<upload_id>/chapters-for-subject/?subject=<name>

    Returns the real Chapter rows for whichever DB Subject this upload's exam
    resolves `subject` to — using the SAME `_find_subject()` lookup (incl.
    the maths/math synonym handling) that the auto-mapper itself uses, so the
    "Select chapter" dropdown in the review UI always lines up with what the
    classifier considers valid targets for that subject. This replaces the
    old frontend-only approach of fetching every Subject for the exam and
    fuzzy-matching names client-side, which silently produced an empty list
    whenever the PDF's subject label didn't normalise to the same string the
    DB used.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        subject_name = (request.query_params.get("subject") or "").strip()
        if not subject_name:
            return Response({"error": "subject is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam = Exam.objects.get(pk=cached["exam_id"])
        except Exam.DoesNotExist:
            return Response({"error": "The exam for this upload no longer exists."},
                            status=status.HTTP_404_NOT_FOUND)

        subject = _find_subject(exam, subject_name)
        if not subject:
            return Response({"subject": subject_name, "subject_id": None, "chapters": []},
                            status=status.HTTP_200_OK)

        chapters = (
            Chapter.objects
            .filter(subject=subject, is_active=True)
            .exclude(chapter_name__iexact=IMPORTED_CHAPTER_NAME)
            .order_by("chapter_name")
            .values("chapter_id", "chapter_name")
        )

        return Response({
            "subject":    subject_name,
            "subject_id": subject.pk,
            "chapters":   list(chapters),
        }, status=status.HTTP_200_OK)

# ─────────────────────────────────────────────────────────────
# PYQ Dashboard — stats card + recent tests table
# ─────────────────────────────────────────────────────────────

def _iter_pyq_appearances():
    """Yield (question, appearance_dict) for every PYQ appearance stored on Question."""
    qs = Question.objects.filter(is_previousyear=True).only(
        "question_id", "appearances", "is_practice", "is_custom", "is_mock", "mock_exam", "created_at")
    for q in qs.iterator(chunk_size=500):
        for a in (q.appearances or []):
            yield q, a


class PyqStatsView(APIView):
    """GET /api/pyq/stats/  (a repeated question counts once as a question, but
    inside every paper it appeared in). Read from Question.appearances."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request):
        week_ago = (timezone.now() - timedelta(days=7)).isoformat()

        sources, sources_week = set(), set()
        questions, questions_week = set(), set()
        mock_ids, mock_ids_week = set(), set()
        for q, a in _iter_pyq_appearances():
            key    = (a.get("exam_id"), a.get("year"), a.get("session", ""), a.get("paper", ""))
            recent = (a.get("added_at") or "") >= week_ago
            sources.add(key)
            questions.add(q.pk)
            if recent:
                sources_week.add(key)
                questions_week.add(q.pk)
            if a.get("mock_exam_id"):
                mock_ids.add(a["mock_exam_id"])
                if recent:
                    mock_ids_week.add(a["mock_exam_id"])
        mock_ids |= set(Question.objects.filter(is_previousyear=True, mock_exam__isnull=False)
                        .values_list("mock_exam_id", flat=True))

        mock_qs     = MockExam.objects.filter(pk__in=mock_ids)
        archived_qs = mock_qs.filter(exam__is_active=False)

        return Response({
            "total":           len(sources),
            "published":       len(questions),
            "draft":           mock_qs.count(),
            "archived":        archived_qs.count(),
            "delta_total":     len(sources_week),
            "delta_published": len(questions_week),
            "delta_draft":     mock_qs.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
            "delta_archived":  archived_qs.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
        })


class PyqTestListView(APIView):
    """GET /api/pyq/tests/?page=1&page_size=10&exam=&year=&status=&search=
    One row per imported paper, built from Question.appearances."""
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request):
        from django.utils.dateparse import parse_datetime
        page      = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        offset    = (page - 1) * page_size

        exam_filter   = (request.query_params.get("exam") or "").strip().lower()
        year_filter   = (request.query_params.get("year") or "").strip()
        status_filter = (request.query_params.get("status") or "").strip()
        search        = (request.query_params.get("search") or "").strip().lower()

        # One row per real paper (exam, year, session, paper). A question repeated in
        # several years is counted inside EVERY paper it appeared in.
        groups = {}
        for q, a in _iter_pyq_appearances():
            name = (a.get("exam_name") or "")
            if exam_filter and name.lower() != exam_filter:
                continue
            if year_filter and str(a.get("year")) != year_filter:
                continue
            if search and search not in name.lower():
                continue
            key = (a.get("exam_id"), a.get("year"), a.get("session", ""), a.get("paper", ""))
            when = parse_datetime(a.get("added_at") or "") or q.created_at
            g = groups.setdefault(key, {
                "exam_name": name, "question_ids": set(), "updated": when,
                "used_in_practice": False, "used_in_custom": False,
            })
            g["question_ids"].add(q.pk)
            if when > g["updated"]:
                g["updated"] = when
            g["used_in_practice"] = g["used_in_practice"] or q.is_practice
            g["used_in_custom"]   = g["used_in_custom"] or q.is_custom

        exams = Exam.objects.in_bulk({k[0] for k in groups if k[0]})
        rows = []
        for (exam_id, year, session, paper), g in groups.items():
            exam  = exams.get(exam_id)
            label = " ".join(x for x in (session, paper) if x)
            rows.append({
                "id":               f"{exam_id}-{year or 'na'}-{session or 'na'}-{paper or 'na'}",
                "name":             g["exam_name"] + (f" ({label})" if label else ""),
                "exam":             g["exam_name"],
                "year":             year,
                "questions":        len(g["question_ids"]),
                "test_type":        "Mock",
                "used_in_practice": g["used_in_practice"],
                "used_in_custom":   g["used_in_custom"],
                "status":           "Published" if (exam is None or exam.is_active) else "Archived",
                "updated":          g["updated"].strftime("%-d %b %Y"),
                "_sort":            g["updated"],
            })

        if status_filter:
            rows = [r for r in rows if r["status"].lower() == status_filter.lower()]

        rows.sort(key=lambda r: r["_sort"], reverse=True)
        for r in rows:
            r.pop("_sort")
        total = len(rows)

        return Response({
            "count": total,
            "page": page,
            "results": rows[offset: offset + page_size],
        })


IMPORTED_CHAPTER_NAME = "Imported (Ungrouped)"   # LEGACY hidden bucket - still excluded from chapter lists
MISC_CHAPTER_NAME     = "Miscellaneous"          # visible chapter for every question with no real chapter


def _misc_chapter_for_subject(subject):
    """The subject's 'Miscellaneous' chapter (created on first use). Holds all
    ungrouped questions, and is used by Practice and Custom tests like any chapter."""
    chapter, _ = Chapter.objects.get_or_create(
        subject=subject, chapter_name=MISC_CHAPTER_NAME, defaults={"is_active": True},
    )
    return chapter


def _get_or_create_chapter_for_subject(exam, subject_name):
    if not subject_name:
        return None
    # Reuse the SAME fuzzy/synonym lookup the rest of the mapping pipeline
    # uses (_find_subject) before ever creating a new Subject row. Without
    # this, a casing mismatch or synonym (e.g. "biology" vs the DB's
    # "Botany"/"Zoology" split) would silently spawn a brand-new, wrong
    # Subject under whichever exam happened to be mid-import - including
    # subjects that exam's syllabus should never have at all (e.g. a
    # stray "Botany" subject appearing under JEE Main).
    subject = _find_subject(exam, subject_name)
    if not subject:
        subject, _ = Subject.objects.get_or_create(
            exam=exam,
            subject_name=subject_name.strip().title()
        )
    return _misc_chapter_for_subject(subject)


# ─────────────────────────────────────────────────────────────
# Shared: write extracted questions into the question bank
# ─────────────────────────────────────────────────────────────
# A question is stored ONCE in the bank (Question / QuestionOption /
# CorrectAnswer). Practice tests, Custom tests and the PYQ MockExam only hold
# *references* to it. The row id is remembered on the cached question dict as
# q["question_db_id"], so:
#   * "Add to Practice" then "Add to Custom" then "Create PYQ Test"
#     never creates duplicate Question rows, and
#   * running any of them first / last / not at all all work.

def _chapter_for_question(exam, q, chapter_cache):
    """Chapter chosen in the review step; falls back to the subject's 'Miscellaneous' chapter."""
    mapped_id = q.get("chapter_id")
    if mapped_id:
        key = ("id", mapped_id)
        if key not in chapter_cache:
            chapter_cache[key] = Chapter.objects.filter(pk=mapped_id).first()
        if chapter_cache[key]:
            return chapter_cache[key]
    subj = q.get("subject")
    if subj not in chapter_cache:
        chapter_cache[subj] = _get_or_create_chapter_for_subject(exam, subj)
    return chapter_cache[subj]


def _write_question_content(row, q):
    """Create/refresh options + correct answer so edits made after an earlier
    'Add to Test' are not lost when the same row is reused."""
    if q.get("question_type") == QUESTION_TYPE_NUMERICAL:
        CorrectAnswer.objects.update_or_create(
            question=row, defaults={"option_id": str(q.get("numerical_answer") or "")},
        )
        return

    option_imgs = {k: v for k, v in (q.get("option_images") or {}).items() if v}
    QuestionOption.objects.update_or_create(
        question=row,
        defaults={
            "option_a": q.get("option_a") or "",
            "option_b": q.get("option_b") or "",
            "option_c": q.get("option_c") or "",
            "option_d": q.get("option_d") or "",
            "option_e": q.get("option_e") or "",
            "option_images": option_imgs,
        },
    )
    CorrectAnswer.objects.update_or_create(
        question=row, defaults={"option_id": q.get("correct_answer") or ""},
    )


# ═════════════════════════════════════════════════════════════
# MASTER QUESTION + OCCURRENCE ENGINE
# ─────────────────────────────────────────────────────────────
# * one MASTER Question row per distinct question
# * Question.appearances = every (exam, year, shift/session, paper, question no.,
#   mock test) the question appeared in -> multi-year / multi-exam repeats
# * QuestionChapterMapping (existing table) = many chapters per question
# Duplicate classes: exact / near_duplicate / new (same-concept questions are
# simply different masters that share chapter/topic).
# ═════════════════════════════════════════════════════════════

NEAR_DUP_RATIO = 0.93      # stem similarity needed to call two questions near-duplicates
MIN_STEM_LEN   = 15        # shorter stems are too generic to match on

# A PYQ question is stored once. Every mock test it belongs to is recorded in
# Question.appearances[*]["mock_exam_id"]; the first mock also sets the plain
# Question.mock_exam FK so older screens that read the FK keep working.
# (JSON "contains" lookups need PostgreSQL.)

def _mock_question_q(mockexam_id):
    """Q() selecting every question that belongs to a mock test."""
    return Q(mock_exam_id=mockexam_id) | Q(appearances__contains=[{"mock_exam_id": mockexam_id}])


def questions_for_mock_exam(mock_exam):
    return Question.objects.filter(_mock_question_q(getattr(mock_exam, "pk", mock_exam)))


def questions_for_standard_chapter(standard_chapter):
    """All questions under one internal chapter, across every exam's own chapter name."""
    return Question.objects.filter(
        chapter_mappings__chapter__standard_chapter=standard_chapter
    ).distinct()


# ── fingerprints ────────────────────────────────────────────────

def _hash_norm(text) -> str:
    """Lower-case, LaTeX-free, letters+digits only. Numbers are KEPT so
    'mass = 5 kg' and 'mass = 10 kg' never fingerprint the same."""
    return re.sub(r"[^a-z0-9]+", "", _cm_normalize(text))


def _numbers_signature(text) -> list:
    return re.findall(r"\d+(?:\.\d+)?", _cm_normalize(text))


def _q_has_images(q: dict) -> bool:
    return bool(q.get("images")) or any((q.get("option_images") or {}).values())


def question_fingerprints(q: dict):
    """
    -> (text_hash, content_hash, stem_key)
      text_hash    stem only
      content_hash stem + options IN ORDER; "" for questions with diagrams (image
                   bytes differ between PDFs, so diagrams are never auto-merged as
                   'exact' - they surface as near_duplicate for review).
    Reordered options => different content_hash => near_duplicate (the correct
    answer letter would differ between the two papers).
    """
    stem = _hash_norm(q.get("question_text"))
    text_hash = hashlib.sha256(stem.encode()).hexdigest() if stem else ""
    content_hash = ""
    if stem and not _q_has_images(q):
        opts = "|".join(_hash_norm(q.get(f"option_{l}")) for l in "abcd")
        content_hash = hashlib.sha256(f"{stem}#{opts}".encode()).hexdigest()
    return text_hash, content_hash, stem[:24]


def _norm_opts(d):
    return [_hash_norm(d.get(f"option_{l}")) for l in "abcd"]


def _options_similar(q, master, min_ratio=0.85):
    """Same four options, in any order (papers often shuffle them)."""
    opt = QuestionOption.objects.filter(question=master).first()
    if not opt:
        return False
    a = sorted(_norm_opts(q))
    b = sorted(_hash_norm(getattr(opt, f"option_{l}", "") or "") for l in "abcd")
    if not any(a) or not any(b):
        return False
    return min(difflib.SequenceMatcher(None, x, y).ratio() for x, y in zip(a, b)) >= min_ratio


_GENERIC_WORDS = {
    "which", "following", "correct", "statement", "statements", "incorrect", "true", "false",
    "value", "given", "then", "with", "that", "this", "these", "those", "from", "have", "what",
    "will", "would", "shown", "figure", "below", "above", "same", "each", "both", "into", "than",
    "equal", "using", "when", "where", "there", "their", "them", "does", "found", "find", "case",
}


def _specific_stem(text) -> bool:
    """True when the stem has enough topic words (e.g. 'bakelite phenol reacting obtained') to
    identify the question by itself - so it can merge even if the options are worded differently.
    Generic stems ('Which one of the following is correct?') need matching options instead."""
    words = set(re.findall(r"[a-z]{4,}", _cm_normalize(text))) - _GENERIC_WORDS
    return len(words) >= 4


def _fuzzy_stem_master(q, stem, min_ratio=0.92):
    """Same question, slightly different wording / OCR noise. Numbers must match,
    so 'mass = 5 kg' never merges with 'mass = 10 kg'."""
    from django.db.models.functions import Length
    raw_len = len(q.get("question_text") or "")
    nums = _numbers_signature(q.get("question_text"))
    cands = (Question.objects.filter(is_previousyear=True)
             .annotate(qlen=Length("question_text"))
             .filter(qlen__gte=int(raw_len * 0.7), qlen__lte=int(raw_len * 1.4) + 1)
             .only("pk", "question_text"))
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(stem)
    best, best_r = None, 0
    for c in cands.iterator(chunk_size=500):
        sm.set_seq1(_hash_norm(c.question_text))
        if sm.real_quick_ratio() < min_ratio or sm.quick_ratio() < min_ratio:
            continue
        r = sm.ratio()
        if r >= min_ratio and r > best_r and _numbers_signature(c.question_text) == nums:
            best, best_r = c, r
    return best


def _find_master(q: dict):
    """-> (master Question | None, "exact" | "near_duplicate" | "new")"""
    stem = _hash_norm(q.get("question_text"))
    if len(stem) < MIN_STEM_LEN:
        return None, "new"

    text_hash, content_hash, _stem_key = question_fingerprints(q)

    if content_hash:
        hit = Question.objects.filter(content_hash=content_hash).order_by("pk").first()
        if hit:
            return hit, "exact"

    hit = Question.objects.filter(text_hash=text_hash).order_by("pk").first()
    if hit:                                   # same stem, options / order / diagram differ
        return hit, "near_duplicate"
    if len(stem) >= 25:                       # reworded / OCR-noisy repeat of the same question
        hit = _fuzzy_stem_master(q, stem)
        if hit:
            return hit, "near_duplicate"
    return None, "new"


def _annotate_duplicates(exam, questions, details) -> dict:
    """
    Sets q["duplicate"] = None | {match_type, question_id, seen_in[], already_in_this_paper}.
    Admin may set q["duplicate_action"]:
        "auto"     exact -> becomes another occurrence of the master,
                   near_duplicate -> separate question row (not linked)
        "merge"    force: treat as another occurrence of the master
        "separate" force: create a new master
    """
    year    = details.get("exam_year") or None
    session = details.get("pyq_session") or ""
    paper   = details.get("paper") or ""
    counts  = {"exact": 0, "near_duplicate": 0, "new": 0}

    for q in questions:
        if q.get("question_db_id"):          # already saved earlier in this session
            continue
        master, match_type = _find_master(q)
        counts[match_type] += 1
        if not master:
            q["duplicate"] = None
            continue
        occs = list(master.appearances or [])
        q["duplicate"] = {
            "match_type":  match_type,
            "question_id": master.pk,
            "seen_in": [{"exam": o.get("exam_name"), "year": o.get("year"),
                         "session": o.get("session", "")} for o in occs[:15]],
            "already_in_this_paper": any(
                o.get("exam_id") == exam.pk and o.get("year") == year
                and (o.get("session") or "") == session
                and (o.get("paper") or "") == paper for o in occs),
        }
        q.setdefault("duplicate_action", "auto")
    return counts


# ── saving ──────────────────────────────────────────────────────
def _strip_nul(obj):
    """Recursively remove NUL (\x00) chars, which PostgreSQL cannot store."""
    if isinstance(obj, str):
        return obj.replace("\x00", "")
    if isinstance(obj, list):
        return [_strip_nul(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _strip_nul(v) for k, v in obj.items()}
    return obj



def _save_questions_to_bank(exam, entries, details, mock_exam=None, source_file=""):
    """
    Persist validated question dicts into the Question model only.
    * exact repeat  -> the existing row is reused (never overwritten) and this
                       paper is added to its Question.appearances list
    * new / near    -> a new Question row is created
    * Every mock test is recorded in appearances[*]["mock_exam_id"]; the first
      one also sets Question.mock_exam (see _mock_question_q).
    Returns (rows, created_count, reused_count) aligned with entries.
    Must be called inside transaction.atomic().
    """
    # PDF extraction can leave NUL chars in question text / options / solutions.
    # PostgreSQL raises "A string literal cannot contain NUL (0x00) characters",
    # so clean everything before it reaches the ORM. Entries are cleaned in
    # place so the cached upload is fixed too.
    for _q in entries:
        _q.update(_strip_nul(_q))
    details     = _strip_nul(details or {})
    source_file = _strip_nul(source_file or "")
 
    pyq_year    = details.get("exam_year")   or None
    pyq_session = details.get("pyq_session") or ""
    paper       = details.get("paper")       or ""
 
    ids      = [q["question_db_id"] for q in entries if q.get("question_db_id")]
    existing = {r.pk: r for r in Question.objects.filter(pk__in=ids)} if ids else {}
 
    chapter_cache = {}
    rows, created, reused = [], 0, 0
    for q in entries:
        chapter = _chapter_for_question(exam, q, chapter_cache)
        # Ungrouped questions are filed under the subject's "Miscellaneous" chapter, so
        # they stay usable in Practice / Custom tests. The old hidden
        # "Imported (Ungrouped)" bucket is swapped for it.
        if chapter is not None and chapter.chapter_name == IMPORTED_CHAPTER_NAME:
            chapter = _misc_chapter_for_subject(chapter.subject)
        images  = q.get("images") or []
        fields  = dict(
            exam=exam,
            chapter=chapter,
            question_text=q.get("question_text", ""),
            question_type=q.get("question_type"),
            marks=q.get("marks"),
            negative_marks=q.get("negative_marks"),
            difficulty_level=q.get("difficulty"),
            is_previousyear=True,
            pyq_exam=exam,                      # "first seen" - kept for old screens
            pyq_year=pyq_year,
            pyq_session=pyq_session or None,
            is_active=True,
            image_url={"images": images} if images else {},
        )
 
        row         = existing.get(q.get("question_db_id"))
        refresh     = row is not None and not q.get("is_merged")   # merged masters are never overwritten
        match_type  = q.get("saved_match_type", "new") if row is not None else "new"

        if row is None:
            dup = q.get("duplicate")
            if dup:
                master, mt = Question.objects.filter(pk=dup["question_id"]).first(), dup["match_type"]
            else:
                master, mt = _find_master(q)
            action = q.get("duplicate_action", "auto")
            auto_ok = bool(master) and (
                mt == "exact"
                or (mt == "near_duplicate" and not _q_has_images(q)
                    and (_options_similar(q, master) or _specific_stem(q.get("question_text"))))
            )
            merge  = bool(master) and (action == "merge" or (action == "auto" and auto_ok))
            if action == "separate":
                merge = False
 
            if merge:
                row, match_type = master, ("exact" if mt == "new" else mt)
                q["is_merged"] = True
            else:
                match_type = mt if master else "new"   # near duplicate: separate row
 
        if row is None:
            row = Question.objects.create(**fields)
            created += 1
            refresh_hashes = True
        else:
            reused += 1
            if refresh:
                for k, v in fields.items():
                    if k == "chapter" and (v is None or (
                            v.chapter_name == MISC_CHAPTER_NAME and row.chapter_id)):
                        continue          # never wipe / downgrade an existing chapter
                    setattr(row, k, v)
                row.save()
            elif not row.is_previousyear:        # bank question that now also appears as a PYQ
                row.is_previousyear = True
                if not row.pyq_exam_id:
                    row.pyq_exam, row.pyq_year = exam, pyq_year
                    row.pyq_session = pyq_session or None
                row.save(update_fields=["is_previousyear", "pyq_exam", "pyq_year", "pyq_session"])
            refresh_hashes = refresh
 
        if refresh_hashes:
            row.text_hash, row.content_hash, _stem_key = question_fingerprints(q)
            row.save(update_fields=["text_hash", "content_hash"])
        q["saved_match_type"] = match_type

        # ── exam + year (+ mock test) stored on the Question row itself ──
        # Question.appearances keeps EVERY (exam, year, session, paper) the question
        # appeared in: JEE Main 2024, JEE Main 2019, NEET 2015 ... on ONE row.
        if pyq_year:
            changed = row.add_appearance(
                exam, pyq_year, session=pyq_session, question_number=q.get("question_number"),
                source="pdf", paper=paper, mock_exam=mock_exam, source_file=source_file,
            )
            if changed:
                row.save(update_fields=["appearances", "is_previousyear",
                                        "pyq_exam", "pyq_year", "pyq_session"])
        if mock_exam is not None:
            if row.mock_exam_id is None:      # first mock owns the FK; later ones live in appearances
                row.mock_exam = mock_exam
                row.save(update_fields=["mock_exam"])

        # ── chapters: primary + extra chapters (many-to-many) ────────────
        extra_ids = [int(i) for i in (q.get("extra_chapter_ids") or []) if str(i).isdigit()]
        to_map = []
        if chapter:
            already = QuestionChapterMapping.objects.filter(question=row).exists()
            is_fallback = chapter.chapter_name == MISC_CHAPTER_NAME
            if not (is_fallback and already):     # don't add "Miscellaneous" next to real chapters
                to_map.append((chapter, True))
        for ch in Chapter.objects.filter(pk__in=extra_ids).exclude(pk=getattr(chapter, "pk", None)):
            to_map.append((ch, False))
 
        has_primary = QuestionChapterMapping.objects.filter(question=row, is_primary=True).exists()
        for ch, wants_primary in to_map:
            _, was_new = QuestionChapterMapping.objects.get_or_create(
                question=row, chapter=ch,
                defaults={
                    "is_primary": wants_primary and not has_primary,
                    "source":     q.get("mapping_source") or "ai",
                    "confidence": q.get("mapping_confidence") or 75,
                },
            )
            if was_new and wants_primary and not has_primary:
                has_primary = True
        if chapter and not row.chapter_id:
            row.chapter = chapter
            row.save(update_fields=["chapter"])
 
        if refresh_hashes or refresh:
            _write_question_content(row, q)
        q["question_db_id"] = row.pk
        rows.append(row)
    return rows, created, reused
 


# ── one-off data helpers (run via the management command) ───────

def _backfill_pyq_appearances() -> dict:
    """
    One-off, idempotent. For every existing question:
    * fills text_hash / content_hash
    * turns the legacy pyq_exam / pyq_year / pyq_session into the first entry of
      Question.appearances (only when appearances is still empty)
    * is_mock     <- question already belongs to a mock test (Question.mock_exam)
    * is_practice <- PYQ question that has a chapter (practice is chapter-driven)
    * is_custom   <- question id is in an active Custom TestDefinition
    """
    hashed = made = 0
    for row in Question.objects.filter(text_hash="").iterator(chunk_size=500):
        opt = QuestionOption.objects.filter(question=row).first()
        as_dict = {
            "question_text": row.question_text,
            "option_a": getattr(opt, "option_a", ""), "option_b": getattr(opt, "option_b", ""),
            "option_c": getattr(opt, "option_c", ""), "option_d": getattr(opt, "option_d", ""),
            "images": (row.image_url or {}).get("images", []) if isinstance(row.image_url, dict) else [],
            "option_images": (getattr(opt, "option_images", None) or {}),
        }
        row.text_hash, row.content_hash, _stem_key = question_fingerprints(as_dict)
        row.save(update_fields=["text_hash", "content_hash"])
        hashed += 1

    for row in Question.objects.filter(is_previousyear=True, pyq_exam__isnull=False,
                                       pyq_year__isnull=False).select_related("pyq_exam").iterator(chunk_size=500):
        if row.appearances:
            continue
        row.add_appearance(row.pyq_exam, row.pyq_year, session=row.pyq_session or "",
                           source="legacy", mock_exam=row.mock_exam,
                           added_at=row.created_at.isoformat())
        row.save(update_fields=["appearances"])
        made += 1

    Question.objects.filter(mock_exam__isnull=False).update(is_mock=True)
    Question.objects.filter(is_previousyear=True, chapter__isnull=False) \
        .exclude(chapter__chapter_name=IMPORTED_CHAPTER_NAME).update(is_practice=True)
    custom_ids = set()
    for t in TestDefinition.objects.filter(test_type="Custom", is_active=True):
        custom_ids.update(_custom_ids(t))
    if custom_ids:
        Question.objects.filter(pk__in=custom_ids).update(is_custom=True)
    return {"hashed": hashed, "appearances_created": made, "occurrences_created": made}


_backfill_pyq_occurrences = _backfill_pyq_appearances   # old name, kept for the management command


_STD_SUBJECTS = (
    ("Physics",     ["Physics"],                          _cm_PHYSICS),
    ("Chemistry",   ["Chemistry"],                        _cm_CHEMISTRY),
    ("Mathematics", ["Mathematics", "Maths", "Math"],     _cm_MATHEMATICS),
)


def _seed_standard_chapters() -> int:
    """Group differently named chapters (Thermal Physics / Thermodynamics / Heat and
    Thermodynamics ...) under one StandardChapter using the alias lists of the topic
    engine. Only fills chapters that have no standard chapter yet - review in admin."""
    linked = 0
    for std_subject, db_names, topics in _STD_SUBJECTS:
        chapters = list(Chapter.objects.filter(
            subject__subject_name__in=db_names, standard_chapter__isnull=True
        ).exclude(chapter_name=IMPORTED_CHAPTER_NAME))
        pairs = [(c.chapter_id, c.chapter_name) for c in chapters]
        for topic in topics:
            std, _ = StandardChapter.objects.get_or_create(subject_name=std_subject, name=topic.label)
            for alias in topic.aliases:
                for hit in [p for p in pairs if _cm__find_chapter(alias, [p])]:
                    linked += Chapter.objects.filter(
                        pk=hit[0], standard_chapter__isnull=True).update(standard_chapter=std)
    return linked


# ─────────────────────────────────────────────────────────────
# Add reviewed questions to a Practice / Custom test (side action)
# ─────────────────────────────────────────────────────────────

_TEST_TYPE_LABELS = {"practice": "Practice", "custom": "Custom"}

# No schema changes: 
#  * PRACTICE = chapter-driven (the student side serves practice questions by
#    Question.chapter). "Add to Practice Test" therefore saves each question to
#    the bank under its mapped chapter – no test row is needed.
#  * CUSTOM = a TestDefinition(test_type="Custom"). There is no question link
#    table, so its question ids are kept as JSON inside TestDefinition.description.

def _custom_ids(test):
    try:
        data = json.loads(test.description or "")
        return [int(i) for i in data.get("question_ids", [])]
    except (ValueError, TypeError, AttributeError):
        return []


def _set_custom_ids(test, ids):
    notes = ""
    try:
        json.loads(test.description or "")
    except (ValueError, TypeError):
        notes = test.description or ""          # keep any hand-written text
    test.description = json.dumps({"notes": notes, "question_ids": ids})
    test.total_marks = Question.objects.filter(pk__in=ids).aggregate(s=Sum("marks"))["s"] or 0
    test.save(update_fields=["description", "total_marks"])


class PyqTargetTestsView(APIView):
    """
    GET /api/pyq-import/<upload_id>/target-tests/?type=custom
    Existing Custom tests of this exam. Practice has no target test (chapter-driven).
    """
    authentication_classes = []
    permission_classes     = [AllowAny]

    def get(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)
        kind = (request.query_params.get("type") or "").lower()
        if kind not in _TEST_TYPE_LABELS:
            return Response({"error": "type must be 'practice' or 'custom'."},
                            status=status.HTTP_400_BAD_REQUEST)
        if kind == "practice":
            return Response({"tests": []}, status=status.HTTP_200_OK)

        tests = TestDefinition.objects.filter(
            exam_id=cached["exam_id"], test_type="Custom", is_active=True).order_by("-created_at")
        return Response({"tests": [
            {"test_id": t.test_id, "test_name": t.test_name,
             "question_count": len(_custom_ids(t)), "created_at": t.created_at}
            for t in tests
        ]}, status=status.HTTP_200_OK)

IMPORTED_CUSTOM_TEST_NAME = "Imported Questions"


def _get_or_create_imported_custom_test(exam):
    """
    The one auto-maintained Custom test that every PYQ-imported question is
    linked into. Custom tests are still a named TestDefinition with an
    explicit id list under the hood (no schema change), but the admin no
    longer has to name/pick one on every import — there's a single running
    container per exam they can rename or split later from the Test
    Definitions screen if they want a purpose-built custom test instead.
    """
    target = TestDefinition.objects.filter(
        exam=exam, test_name=IMPORTED_CUSTOM_TEST_NAME, test_type="Custom", is_active=True
    ).first()
    if target is None:
        target = TestDefinition.objects.create(
            exam=exam, test_name=IMPORTED_CUSTOM_TEST_NAME, test_type="Custom", is_active=True)
    return target

def _eligible_for_practice_custom(questions):
    """
    Questions allowed into Practice / Custom tests: either a chapter was picked in
    the review step, or the question has a subject (then it is filed under that
    subject's 'Miscellaneous' chapter). Only questions with neither are left out;
    they stay available for the Mock test.
    """
    def _cid(q):
        v = q.get("chapter_id")
        return int(v) if str(v or "").isdigit() else None

    ids = {c for c in (_cid(q) for q in questions) if c}
    good = set(Chapter.objects.filter(pk__in=ids).values_list("pk", flat=True))
    return [q for q in questions
            if _cid(q) in good or str(q.get("subject") or "").strip()]


class PyqAddToTestView(APIView):
    """
    POST /api/pyq-import/<upload_id>/add-to-test/

    Body:
        question_indexes  [int, ...]   (required)

    Only VALID questions are added to Practice and Custom tests. A question with a
    chapter goes under that chapter; a question with only a subject goes under that
    subject's 'Miscellaneous' chapter. Questions with neither chapter nor subject
    are skipped and remain available for the Mock test in the final wizard step.
    """
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            exam = Exam.objects.get(pk=cached["exam_id"])
        except Exam.DoesNotExist:
            return Response({"error": "The exam for this upload no longer exists."},
                            status=status.HTTP_404_NOT_FOUND)

        try:
            indexes = [int(i) for i in (request.data.get("question_indexes") or [])]
        except (TypeError, ValueError):
            return Response({"error": "question_indexes must be a list of integers."},
                            status=status.HTTP_400_BAD_REQUEST)
        if not indexes:
            return Response({"error": "Select at least one question."},
                            status=status.HTTP_400_BAD_REQUEST)

        by_index  = {q["index"]: q for q in cached["questions"]}
        selected  = [by_index[i] for i in dict.fromkeys(indexes) if i in by_index]
        not_valid = [q for q in selected if q.get("status") != STATUS_VALID]
        valid     = [q for q in selected if q.get("status") == STATUS_VALID]

        if not valid:
            return Response({
                "error": "None of the selected questions can be added. Only valid questions can be added.",
                "skipped_not_valid": len(not_valid), "skipped_unmapped": 0,
            }, status=status.HTTP_400_BAD_REQUEST)

        # ── chapter-mapped questions, plus subject-only ones (-> Miscellaneous) ──
        eligible    = _eligible_for_practice_custom(valid)
        eligible_ix = {q["index"] for q in eligible}
        unmapped    = [q for q in valid if q["index"] not in eligible_ix]

        if not eligible:
            return Response({
                "error": ("None of the selected questions have a subject or chapter. "
                          "Assign a subject (ungrouped questions go under 'Miscellaneous') "
                          "to add them to Practice/Custom tests. "
                          "They can still be used in the Mock test."),
                "skipped_not_valid": len(not_valid),
                "skipped_unmapped":  len(unmapped),
            }, status=status.HTTP_400_BAD_REQUEST)

        details = cached["paper_details"]
        with transaction.atomic():
            rows, created, reused = _save_questions_to_bank(
                exam, eligible, details, source_file=cached.get("file_name", ""))

            practice_duplicates = sum(1 for q in eligible if "practice" in (q.get("added_to") or []))
            practice_added      = len(eligible) - practice_duplicates

            target  = _get_or_create_imported_custom_test(exam)
            ids     = _custom_ids(target)
            new_ids = [r.pk for r in rows if r.pk not in ids]
            custom_duplicates = len(rows) - len(new_ids)
            custom_added      = len(new_ids)
            _set_custom_ids(target, ids + new_ids)

            # Store on the Question model where it is used (every eligible question now
            # has a chapter - real or Miscellaneous - so both flags are valid).
            Question.objects.filter(pk__in=[r.pk for r in rows], chapter__isnull=False).update(
                is_practice=True, is_custom=True)

        for q in eligible:
            added_to = q.setdefault("added_to", [])
            for key in ("practice", "custom"):
                if key not in added_to:
                    added_to.append(key)
        _persist(upload_id, cached)

        return Response({
            "test_id":               target.test_id,
            "test_name":             target.test_name,
            "added":                 len(eligible) - min(practice_duplicates, custom_duplicates),
            "practice_added":        practice_added,
            "practice_duplicates":   practice_duplicates,
            "custom_added":          custom_added,
            "custom_duplicates":     custom_duplicates,
            "skipped_not_valid":     len(not_valid),
            "skipped_unmapped":      len(unmapped),
            "skipped_unmapped_indexes": [q["index"] for q in unmapped],
            "test_question_count":   len(ids) + len(new_ids),
            "summary":               _summary_counts(cached["questions"]),
            "question_states":       [{"index": q["index"], "added_to": q.get("added_to", [])} for q in eligible],
        }, status=status.HTTP_200_OK)

# ─────────────────────────────────────────────────────────────
# Final wizard step: create the PYQ MockExam
# ─────────────────────────────────────────────────────────────

class PyqCreateTestView(APIView):
    """
    Create the PYQ MockExam from the validated questions.

    Independent of Add-to-Practice / Add-to-Custom: questions that were already
    pushed to those tests are REUSED (not duplicated) and simply also linked to
    this MockExam.
    """
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request, upload_id):
        cached = _get_cached_or_404(upload_id)
        if not cached:
            return Response({"error": "Upload session has expired or was not found."},
                            status=status.HTTP_404_NOT_FOUND)

        try:
            exam = Exam.objects.get(pk=cached["exam_id"])
        except Exam.DoesNotExist:
            return Response({"error": "The exam for this upload no longer exists."},
                            status=status.HTTP_404_NOT_FOUND)

        details         = cached["paper_details"]
        questions       = cached["questions"]
        valid_questions = [q for q in questions if q["status"] == STATUS_VALID]
        skipped         = len(questions) - len(valid_questions)

        if not valid_questions:
            return Response(
                {"error": "No valid questions to import. Resolve the flagged rows first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subject_ids    = details.get("subject_ids")   or []
        subject_names  = details.get("subject_names") or []
        pyq_year       = details.get("exam_year")     or None
        pyq_session    = details.get("pyq_session")   or None

        total_marks      = sum(float(q.get("marks") or 0) for q in valid_questions)
        default_negative = valid_questions[0].get("negative_marks") or 0

        mock_exam_name = (request.data.get("test_name") or "").strip() or (
            f"{exam.exam_name} {pyq_year or ''}"
            f"{f' ({pyq_session})' if pyq_session else ''}".strip()
        )

        subject_breakdown = []
        if subject_ids:
            per_subject = len(valid_questions) // len(subject_ids)
            remainder   = len(valid_questions) % len(subject_ids)
            for idx, sid in enumerate(subject_ids):
                q_count = per_subject + (1 if idx < remainder else 0)
                subject_breakdown.append({
                    "subject_id": sid,
                    "name":       subject_names[idx] if idx < len(subject_names) else "",
                    "questions":  q_count,
                    "marks":      round(q_count * float(valid_questions[0].get("marks") or 0), 2),
                })

        with transaction.atomic():
            mock_exam = MockExam.objects.create(
                exam=exam,
                mockexam_name=mock_exam_name,
                year=pyq_year,
                description=f"Test imported from PDF ({cached['file_name']}).",
                total_marks=total_marks,
                duration_minutes=request.data.get("duration_minutes"),
                pattern={
                    "total_questions":    len(valid_questions),
                    "marks_per_question": float(valid_questions[0].get("marks") or 0),
                    "negative_marking":   float(default_negative or 0),
                    "subjects":           subject_breakdown,
                },
                is_active=True,
            )
            rows, created, reused = _save_questions_to_bank(
                exam, valid_questions, details, mock_exam=mock_exam,
                source_file=cached.get("file_name", ""),
            )
            # Store on the Question model that it belongs to a PYQ mock test.
            Question.objects.filter(pk__in=[r.pk for r in rows]).update(is_mock=True)

        _delete_storage(upload_id)

        return Response({
            "mockExamId":     mock_exam.pk,
            "mockExamName":   mock_exam.mockexam_name,
            "imported":       len(rows),
            "newQuestions":   created,
            "alreadyInBank":  reused,   # were added to a Practice/Custom test earlier
            "skipped":        skipped,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────
# urls.py additions for chapter auto-mapping (add to your urls.py)
# ─────────────────────────────────────────────────────────────
#   from .views import auto_map_questions_to_chapters, update_question_chapter
#
#   path('pyq-import/<str:upload_id>/auto-map-chapters/', auto_map_questions_to_chapters),
#   path('pyq-import/<str:upload_id>/questions/<int:question_index>/chapter/', update_question_chapter),
#
# NEW — Add to Practice / Custom test (optional, independent of PYQ creation):
#   from .views import PyqAddToTestView, PyqTargetTestsView
#   path('pyq-import/<str:upload_id>/add-to-test/',   PyqAddToTestView.as_view()),
#   path('pyq-import/<str:upload_id>/target-tests/',  PyqTargetTestsView.as_view()),