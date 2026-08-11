from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db.models import Count, Q
from django.core.paginator import Paginator

from .models import (
    State, Board, Stream, Field, SubField, EducationLevel,
    ExamType, SchoolExamCategory, EntranceExamCategory,
    JobCategory, JobExamCategory, ExamLevel, Exam,
    Subject, Chapter, Question,MockExam
)
from .serializers import (
    StateSerializer, BoardSerializer, StreamSerializer, FieldSerializer,
    SubFieldSerializer,FieldWithSubFieldsSerializer, EducationLevelSerializer, ExamTypeSerializer,
    SchoolExamCategorySerializer, EntranceExamCategorySerializer,
    JobCategorySerializer, JobExamCategorySerializer, ExamLevelSerializer,
    ExamSerializer, SubjectSerializer, ChapterSerializer, QuestionSerializer,MockExamSerializer
)


# ─────────────────────────────────────────────────────────────
# APPLY FILTERS — cascading dropdown data (Process Flow steps 1-9)
# ─────────────────────────────────────────────────────────────

class ExamTypeListView(generics.ListAPIView):
    """GET /api/filters/exam-types/"""
    queryset = ExamType.objects.all()
    serializer_class = ExamTypeSerializer


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
    GET /api/filters/education-levels/?exam_type_id=  → only levels actually
        used by at least one Exam of that type (School/Entrance use this;
        Job exams have no education_level set, so this returns empty for Job)
    """
    serializer_class = EducationLevelSerializer
    pagination_class = None  # Return all education levels without pagination

    def get_queryset(self):
        qs = EducationLevel.objects.all()
        exam_type_id = self.request.query_params.get('exam_type_id')
        if exam_type_id:
            # CHANGED: education_levels is now M2M (see models.py) — walk
            # through it instead of filtering the old single FK column.
            used_ids = (
                Exam.objects
                .filter(exam_type_id=exam_type_id, education_levels__isnull=False)
                .values_list('education_levels__education_level_id', flat=True)
                .distinct()
            )
            qs = qs.filter(pk__in=used_ids)
        return qs


class StreamListView(generics.ListAPIView):
    """
    GET /api/filters/streams/
    GET /api/filters/streams/?exam_type_id=  → only streams actually used
        by at least one Exam of that type
    """
    serializer_class = StreamSerializer
    pagination_class = None  # Return all streams without pagination

    def get_queryset(self):
        qs = Stream.objects.all()
        exam_type_id = self.request.query_params.get('exam_type_id')
        if exam_type_id:
            # CHANGED: streams is now M2M (see models.py).
            used_ids = (
                Exam.objects
                .filter(exam_type_id=exam_type_id, streams__isnull=False)
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

class MockExamListView(APIView):
    """
    GET /api/mockexams/

    Returns actual attemptable mock papers (MockExam rows), e.g.
    "JEE Main 2024 Shift 1", for ONE parent Exam program — as opposed to
    /api/exams/ which lists exam *programs* themselves (e.g. "JEE Main")
    on the Select Exam screen.

    This is what "Select Mock Test" (step 3 of Practice/Mock flow) must
    call. Previously that screen called /api/exams/ and tried to
    text-match a removed `exam_category` field, which silently matched
    nothing and fell back to listing ALL exams alphabetically (AAFT,
    ACJ, AEEE... under "JEE Main"). MockExam rows are tied to their
    parent Exam via a real FK, so filtering here is exact.

    Params (provide exam_code OR exam_id — exam_code takes priority
    if both are passed):
        exam_code – Exam.exam_code, e.g. "JEE-MAIN" (unique, human-readable).
        exam_id   – PK of the parent Exam. Optional alternative to exam_code.
        page      – page number, default 1.
        search    – optional icontains match on mockexam_name.
    """
    PAGE_SIZE = 20

    def get(self, request):
        exam_code = request.query_params.get('exam_code', '').strip()
        exam_id   = request.query_params.get('exam_id', '').strip()

        if not exam_code and not exam_id:
            return Response(
                {'error': 'exam_code (or exam_id) is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = MockExam.objects.filter(is_active=True)

        if exam_code:
            qs = qs.filter(exam__exam_code=exam_code)
        else:
            if not exam_id.isdigit():
                return Response(
                    {'error': f'exam_id must be a valid integer, got "{exam_id}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(exam_id=int(exam_id))

        qs = qs.select_related('exam').order_by('-year', 'mockexam_name')

        if not qs.exists() and exam_code:
            # exam_code didn't match any Exam row at all — distinguish
            # "wrong/unknown code" from "valid exam, just no mock tests yet"
            if not Exam.objects.filter(exam_code=exam_code).exists():
                return Response(
                    {'error': f'No exam found with exam_code "{exam_code}".'},
                    status=status.HTTP_404_NOT_FOUND
                )

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(mockexam_name__icontains=search)

        page_param = request.query_params.get('page', '1').strip()
        page_number = int(page_param) if page_param.isdigit() else 1

        paginator = Paginator(qs, self.PAGE_SIZE)
        page = paginator.get_page(page_number)

        serializer = MockExamSerializer(page.object_list, many=True)
        return Response({'results': serializer.data, 'count': paginator.count})

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
    """

    def get(self, request):
        exam_id = request.query_params.get('exam_id', '').strip()
        exam_code = request.query_params.get('exam_code', '').strip()

        if not exam_id and not exam_code:
            return Response(
                {'error': 'exam_id or exam_code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
                .annotate(chapter_count=Count('chapter'))
                .order_by('subject_name')
            )

        else:
            if exam_code.isdigit():
                resolved_exam_id = int(exam_code)
                subjects = (
                    Subject.objects
                    .filter(exam_id=resolved_exam_id)
                    .annotate(chapter_count=Count('chapter'))
                    .order_by('subject_name')
                )
            else:
                subjects = (
                    Subject.objects
                    .filter(exam__exam_code__iexact=exam_code)
                    .annotate(chapter_count=Count('chapter'))
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
        subject_ids (required) – comma-separated Subject PKs, OR "all"
                                  combined with exam_id
        exam_id     (required only when subject_ids="all")
        difficulty  (optional) – "easy" | "medium" | "hard" | "mixed" (default: mixed)
        count       (optional) – number of questions to return, default 50

    CHANGED: `exam_category` support is gone (pass exam_id instead).
    Question has no `subject` FK — subject filtering now goes through
    `chapter__subject_id`, since Question only links to Chapter directly.
    `status` string-matching replaced with the real `is_active` boolean.
    """

    def get(self, request):
        subject_ids_param = request.query_params.get('subject_ids', '').strip()
        exam_id_param = request.query_params.get('exam_id', '').strip()
        difficulty = request.query_params.get('difficulty', 'mixed').strip().lower()
        count_param = request.query_params.get('count', '50').strip()

        if not subject_ids_param:
            return Response(
                {'error': 'subject_ids is required (comma-separated IDs, or "all").'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not count_param.isdigit() or int(count_param) <= 0:
            return Response(
                {'error': f'count must be a positive integer, got "{count_param}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        count = int(count_param)

        qs = Question.objects.filter(is_active=True)

        if subject_ids_param.lower() == 'all':
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
        else:
            ids = [s.strip() for s in subject_ids_param.split(',') if s.strip()]
            if not all(s.isdigit() for s in ids):
                return Response(
                    {'error': f'subject_ids must all be valid integers, got "{subject_ids_param}".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(chapter__subject_id__in=[int(s) for s in ids])

        if difficulty != 'mixed':
            qs = qs.filter(difficulty_level__iexact=difficulty)

        qs = (
            qs.select_related('chapter__subject')
              .prefetch_related('questionoption_set', 'solution_set', 'correctanswer_set')
              .order_by('?')[:count]
        )

        serializer = QuestionSerializer(qs, many=True, context={'mode': 'test'})

        return Response({
            'difficulty': difficulty,
            'count': len(serializer.data),
            'questions': serializer.data,
        })


class QuestionListView(APIView):
    """
    GET /api/questions/
    Params:
        chapter_id  — fetch by chapter (chapter-wise)
        subject_id  — fetch by subject (complete syllabus)
        mode        — 'test' | 'practice' (affects whether answers/explanations are hidden)
        scope       — 'full' signals complete syllabus (used with subject_id)
        count_only  — if 'true', return only { count } without questions

    CHANGED: subject_id filtering now goes through `chapter__subject_id`
    since Question has no direct `subject` FK. Both branches now also
    require `is_active=True`.
    """

    def get(self, request):
        chapter_id = request.query_params.get('chapter_id', '').strip()
        subject_id = request.query_params.get('subject_id', '').strip()
        mode = request.query_params.get('mode', 'test').strip().lower()
        scope = request.query_params.get('scope', '').strip().lower()
        count_only = request.query_params.get('count_only', 'false').strip().lower() == 'true'

        if not chapter_id and not subject_id:
            return Response(
                {'error': 'chapter_id or subject_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if subject_id and scope == 'full':
            qs = (
                Question.objects
                .filter(chapter__subject_id=subject_id, is_active=True)
                .select_related('chapter__subject')
                .prefetch_related('questionoption_set', 'solution_set', 'correctanswer_set')
                .order_by('?')
            )
        elif chapter_id:
            qs = (
                Question.objects
                .filter(chapter_id=chapter_id, is_active=True)
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
            'mode': mode,
            'scope': scope or 'chapter',
            'count': len(serializer.data),
            'questions': serializer.data,
        })


class SubmitAnswersView(APIView):
    """
    POST /api/questions/submit/
    Body: { "answers": { "<question_id>": "A"|"B"|"C"|"D" } }

    CHANGED: CorrectAnswer has no `answer_value` field — the correct
    option is stored in `option_id`.
    """

    def post(self, request):
        answers = request.data.get('answers', {})
        if not answers:
            return Response({'error': 'No answers provided.'}, status=status.HTTP_400_BAD_REQUEST)

        question_ids = list(answers.keys())
        questions = (
            Question.objects
            .filter(question_id__in=question_ids)
            .prefetch_related('correctanswer_set', 'solution_set')
        )

        results = []
        score = 0

        for q in questions:
            user_answer = answers.get(str(q.question_id), '').upper()
            ca = q.correctanswer_set.first()
            correct = ca.option_id.upper() if ca else ''
            is_correct = user_answer == correct
            if is_correct:
                score += 1

            sol = q.solution_set.first()
            results.append({
                'question_id': q.question_id,
                'question_text': q.question_text,
                'your_answer': user_answer,
                'correct_answer': correct,
                'is_correct': is_correct,
                'explanation': sol.explaination_text if sol else '',
                'hints': sol.hints if sol else '',
            })

        total = len(questions)
        return Response({
            'score': score,
            'total': total,
            'percentage': round((score / total) * 100, 1) if total else 0,
            'results': results,
        })