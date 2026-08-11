"""
Django management command: import_exams
=======================================
Imports exams_by_type_merged_filled.json into the Exam catalog schema.

WHERE TO PUT THIS FILE
-----------------------
    <your_app>/management/commands/import_exams.py

    Also create (if not already present):
        <your_app>/management/__init__.py
        <your_app>/management/commands/__init__.py

HOW TO RUN
-----------
    python manage.py import_exams path/to/exams_by_type_merged_filled.json
    python manage.py import_exams path/to/exams_by_type_merged_filled.json --dry-run

JSON SHAPE (what this script handles)
---------------------------------------
The file is a dict with three top-level keys: "school", "entrance", "job".
Every entry — regardless of key or source — uses the same flat shape:

    {
      "exam_code":            "JEE_MAIN",
      "exam_name":            "JEE Main",
      "description":          "Engineering Entrance (National)",
      "source":               "vue_popular_exams" | "excel_education_level",
      "logo":                 "https://...",
      "testCount":            "12.5K+",
      "educationLevels":      ["12th", "engineering"],   ← raw tag list
      "streams":              ["cse", "mechanical", ...], ← raw tag list
      "graduations":          ["ug"],
      "jobTypes":             ["government" | "not_applicable" | ...],
      "jobCategories":        ["psu" | "not_applicable" | ...]
    }

NOTE: Fields like "education_level", "tier", "category", "field_of_study"
that appear in the legacy docstring do NOT exist in this JSON. All tags
live inside array fields and are mapped to DB rows via alias tables below.

WHAT GETS POPULATED
--------------------
For every exam entry the script will get-or-create (never blind-insert):

  ExamType          — from the top-level group key ("school"/"entrance"/"job")
  EducationLevel    — from educationLevels[] tags (via EDU_LEVEL_ALIASES)
  Stream            — from streams[] tags (via STREAM_ALIASES)
  State             — best-effort from exam_code prefix (STATE_PREFIX_MAP)
  ExamLevel         — from EXAM_LEVEL_MAP (National for most national codes,
                      State for known state-level prefixes, else None)
  JobCategory       — from jobCategories[] tags (via JOB_CAT_ALIASES),
                      job exams only (non-"not_applicable" values)
  JobExamCategory   — created per unique (exam_type, job_category) pair so
                      Exam.category_id is a real FK-resolvable value
  EntranceExamCategory — created per unique (exam_type, education_level,
                      stream) triple for entrance exams
  SchoolExamCategory — created per unique (exam_type, education_level,
                      stream) triple for school exams

  Exam              — update_or_create on exam_code (safe to re-run):
      exam_type, exam_name, description, logo, test_count (if field exists),
      level, state, category_id, is_active=True
      + M2M: education_levels, streams

Fields intentionally left blank:
  field / sub_field  — the merged JSON has no per-exam field_of_study column
  board              — the JSON carries no board_id; can be added separately
  conducting_body    — not present in this JSON shape

DEDUPLICATION
-------------
exam_code is unique. If the same code appears in more than one top-level
group (e.g. CSIR_NET in both "entrance" and "job") the second occurrence
is suffixed with _<TYPE> (e.g. "CSIR_NET_JOB") so nothing is silently lost.
"""

import re
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# ── Adjust this import to your project's actual app path if different ──
from MockAdmin.models import (
    ExamType, EducationLevel, Stream, Field, SubField, ExamLevel,
    JobCategory, EntranceExamCategory, JobExamCategory, SchoolExamCategory,
    Board, State, Exam,
)

# ---------------------------------------------------------------------------
# Best-effort exam_code prefix → Indian state name.
# Used for ALL entry types — purely substring-prefix matching on exam_code.
# ---------------------------------------------------------------------------
STATE_PREFIX_MAP = [
    ('MAH_',           'Maharashtra'),
    ('MHT_CET',        'Maharashtra'),
    ('MSCE_',          'Maharashtra'),
    ('MCAER',          'Maharashtra'),
    ('MAFSU',          'Maharashtra'),
    ('MAHA_TET',       'Maharashtra'),
    ('TS_',            'Telangana'),
    ('AP_',            'Andhra Pradesh'),
    ('KCET',           'Karnataka'),
    ('KARNATAKA_',     'Karnataka'),
    ('TNEA',           'Tamil Nadu'),
    ('WBJEE',          'West Bengal'),
    ('WB_JEE',         'West Bengal'),
    ('WEST_BENGAL',    'West Bengal'),
    ('JEXPO',          'West Bengal'),
    ('JENPAS',         'West Bengal'),
    ('PUBDET',         'West Bengal'),
    ('PUBDGET',        'West Bengal'),
    ('KEAM',           'Kerala'),
    ('KLEE',           'Kerala'),
    ('OJEE',           'Odisha'),
    ('OUAT',           'Odisha'),
    ('GUJCET',         'Gujarat'),
    ('RUHS_CET',       'Rajasthan'),
    ('RAJASTHAN_',     'Rajasthan'),
    ('UPCATET',        'Uttar Pradesh'),
    ('UPSEE_',         'Uttar Pradesh'),
    ('UPJEE_',         'Uttar Pradesh'),
    ('UP_',            'Uttar Pradesh'),
    ('JEECUP',         'Uttar Pradesh'),
    ('MP_PAT',         'Madhya Pradesh'),
    ('BCECE',          'Bihar'),
    ('DCECE_BIHAR',    'Bihar'),
    ('BIHAR_',         'Bihar'),
    ('CG_PET',         'Chhattisgarh'),
    ('GGSIPU',         'Delhi'),
    ('IPU_CET',        'Delhi'),
    ('UBTER',          'Uttarakhand'),
    ('MSBSHSE',        'Maharashtra'),
    ('UPMSP',          'Uttar Pradesh'),
    ('WBBSE',          'West Bengal'),
]

# ---------------------------------------------------------------------------
# Alias maps: raw JSON tag → canonical DB name
# ---------------------------------------------------------------------------

# educationLevels[] raw tags → EducationLevel.education_level
EDU_LEVEL_ALIASES = {
    '10th':        'Class 10',
    '12th':        'Class 12',
    'ug':          'Graduate',
    'graduation':  'Graduate',
    'pg':          'Postgraduate',
    'phd':         'Doctorate (PhD)',
    'engineering': 'Graduate',  # "engineering" in educationLevels means a graduate engineer
}

# streams[] raw tags → Stream.stream_name
STREAM_ALIASES = {
    'cse':                 'Computer Science',
    'it':                  'Information Technology',
    'ece':                 'Electronics and Communication Engineering',
    'electrical':          'Electrical Engineering',
    'mechanical':          'Mechanical Engineering',
    'civil':               'Civil Engineering',
    'chemical':            'Chemical Engineering',
    'aerospace':           'Aerospace Engineering',
    'electronics':         'Electronics Engineering',
    'science':             'Science',
    'maths':               'Mathematics',
    'social':              'Humanities',
    'general':             'General',
    'arts':                'Arts',
    'commerce':            'Commerce',
    'management':          'Management',
    'law':                 'Law',
    'mbbs':                'Medical',
    'nursing':             'Nursing',
    'pharmacy':            'Pharmacy',
    'agriculture':         'Agriculture',
    'biotechnology':       'Biotechnology',
    'architecture':        'Architecture',
    'design':              'Design',
    'fine_arts':           'Fine Arts',
    'fashion_design':      'Fashion Technology',
    'hospitality':         'Hotel Management',
    'aviation':            'Aviation',
    'maritime':            'Maritime Studies',
    'education':           'Education',
    'psychology':          'Psychology',
    'environmental_science': 'Environmental Science',
    'forensic_science':    'Forensic Science',
    'social_work':         'Social Work',
    'physical_education':  'Physical Education',
    'library_science':     'Library Science',
    'statistics':          'Statistics',
    'mass_communication':  'Mass Communication',
    'film_media':          'Journalism',
    'languages':           'Humanities',
    'veterinary':          'Veterinary Science',
    'defence':             'General',
    # degree tags that appear inside streams[]
    'btech':   'Engineering',
    'bsc':     'Science',
    'ba':      'Arts',
    'bcom':    'Commerce',
    'bba':     'Management',
    'bca':     'Computer Science',
    'llb':     'Law',
    'mtech':   'Engineering',
    'msc':     'Science',
    'ma':      'Arts',
    'mcom':    'Commerce',
    'mba':     'Management',
    'mca':     'Computer Science',
    'mbbs':    'Medical',
}

# jobCategories[] raw tags → JobCategory.job_category_name
JOB_CAT_ALIASES = {
    'psu':           'PSU',
    'civil_services': 'UPSC',
    'ssc':           'SSC',
    'banking':       'Banking',
    'railways':      'Railway',
    'defence':       'Defence',
    'teaching':      'Teaching',
    'research':      'Scientific Research',
    'software':      'Information Technology',
    'campus_hiring': 'Private Sector',
}

# Tags that are NOT real job categories — skip them
SKIP_JOB_CATEGORIES = {'not_applicable'}


class Command(BaseCommand):
    help = "Import exams_by_type_merged_filled.json into the Exam catalog schema."

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str, help='Path to exams_by_type_merged_filled.json')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Parse and report counts without writing to the database.',
        )

    def handle(self, *args, **options):
        path = Path(options['json_path'])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        dry_run = options['dry_run']

        # Accept a bare list too (treated as single "school" group)
        if isinstance(data, list):
            data = {'school': data}

        # ── in-memory caches so we only hit the DB once per distinct value ──
        exam_type_cache      = {}
        edu_level_cache      = {}
        stream_cache         = {}
        exam_level_cache     = {}
        job_category_cache   = {}
        state_cache          = {}
        school_cat_cache     = {}
        entrance_cat_cache   = {}
        job_exam_cat_cache   = {}

        # ── Helper: get-or-create ExamType by type_name ──
        def get_exam_type(raw_name: str) -> ExamType:
            key = raw_name.strip().lower()
            if key not in exam_type_cache:
                obj, _ = ExamType.objects.get_or_create(
                    type_name__iexact=raw_name,
                    defaults={'type_name': raw_name.capitalize()},
                )
                # get_or_create with __iexact lookup works in two steps:
                # first try to find, then create — safer to write explicitly:
                obj = ExamType.objects.filter(type_name__iexact=raw_name).first()
                if not obj:
                    obj = ExamType.objects.create(type_name=raw_name.capitalize())
                exam_type_cache[key] = obj
            return exam_type_cache[key]

        # ── Helper: resolve educationLevel tag → EducationLevel row ──
        def get_edu_level(raw_tag: str) -> EducationLevel:
            canonical = EDU_LEVEL_ALIASES.get(raw_tag.strip().lower(), raw_tag.strip())
            key = canonical.lower()
            if key not in edu_level_cache:
                obj = EducationLevel.objects.filter(education_level__iexact=canonical).first()
                if not obj:
                    obj = EducationLevel.objects.create(education_level=canonical)
                edu_level_cache[key] = obj
            return edu_level_cache[key]

        # ── Helper: resolve stream tag → Stream row ──
        def get_stream(raw_tag: str) -> Stream:
            canonical = STREAM_ALIASES.get(raw_tag.strip().lower(), raw_tag.strip().title())
            key = canonical.lower()
            if key not in stream_cache:
                obj = Stream.objects.filter(stream_name__iexact=canonical).first()
                if not obj:
                    obj = Stream.objects.create(stream_name=canonical)
                stream_cache[key] = obj
            return stream_cache[key]

        # ── Helper: resolve jobCategory tag → JobCategory row ──
        def get_job_category(raw_tag: str) -> JobCategory:
            canonical = JOB_CAT_ALIASES.get(raw_tag.strip().lower(), raw_tag.strip().title())
            key = canonical.lower()
            if key not in job_category_cache:
                obj = JobCategory.objects.filter(job_category_name__iexact=canonical).first()
                if not obj:
                    obj = JobCategory.objects.create(job_category_name=canonical)
                job_category_cache[key] = obj
            return job_category_cache[key]

        # ── Helper: State ──
        def get_state(state_name: str) -> State:
            key = state_name.strip().lower()
            if key not in state_cache:
                obj = State.objects.filter(state_name__iexact=state_name).first()
                if not obj:
                    obj = State.objects.create(
                        state_name=state_name,
                        state_code=state_name[:10].upper().replace(' ', ''),
                    )
                state_cache[key] = obj
            return state_cache[key]

        # ── Helper: best-effort State from exam_code prefix ──
        def guess_state(exam_code: str):
            for prefix, state_name in STATE_PREFIX_MAP:
                if exam_code.startswith(prefix):
                    return state_name
            return None

        # ── Helper: ExamLevel from state guess ──
        def get_exam_level(level_name: str) -> ExamLevel:
            key = level_name.strip().lower()
            if key not in exam_level_cache:
                obj = ExamLevel.objects.filter(level_name__iexact=level_name).first()
                if not obj:
                    obj = ExamLevel.objects.create(level_name=level_name)
                exam_level_cache[key] = obj
            return exam_level_cache[key]

        # ── Helper: SchoolExamCategory (get-or-create per type+edu+stream) ──
        def get_school_exam_category(
            exam_type_obj: ExamType,
            edu_level_obj: EducationLevel,
            stream_obj: Stream,
        ) -> SchoolExamCategory:
            edu_id  = edu_level_obj.education_level_id if edu_level_obj else None
            str_id  = stream_obj.stream_id             if stream_obj    else None
            cat_name = (stream_obj.stream_name if stream_obj else 'General')
            key = (exam_type_obj.exam_type_id, edu_id, str_id)
            if key not in school_cat_cache:
                obj = SchoolExamCategory.objects.filter(
                    exam_type=exam_type_obj,
                    education_level=edu_level_obj,
                    category_name__iexact=cat_name,
                ).first()
                if not obj:
                    obj = SchoolExamCategory.objects.create(
                        exam_type=exam_type_obj,
                        education_level=edu_level_obj,
                        category_name=cat_name,
                    )
                school_cat_cache[key] = obj
            return school_cat_cache[key]

        # ── Helper: EntranceExamCategory ──
        def get_entrance_category(
            exam_type_obj: ExamType,
            edu_level_obj: EducationLevel,
            stream_obj: Stream,
        ) -> EntranceExamCategory:
            edu_id  = edu_level_obj.education_level_id if edu_level_obj else None
            str_id  = stream_obj.stream_id             if stream_obj    else None
            cat_name = (stream_obj.stream_name if stream_obj else 'General')
            key = (exam_type_obj.exam_type_id, edu_id, str_id)
            if key not in entrance_cat_cache:
                obj = EntranceExamCategory.objects.filter(
                    exam_type=exam_type_obj,
                    education_level=edu_level_obj,
                    category_name__iexact=cat_name,
                ).first()
                if not obj:
                    obj = EntranceExamCategory.objects.create(
                        exam_type=exam_type_obj,
                        education_level=edu_level_obj,
                        category_name=cat_name,
                    )
                entrance_cat_cache[key] = obj
            return entrance_cat_cache[key]

        # ── Helper: JobExamCategory ──
        def get_job_exam_category(
            exam_type_obj: ExamType,
            job_cat_obj: JobCategory,
        ) -> JobExamCategory:
            cat_name = job_cat_obj.job_category_name
            key = (exam_type_obj.exam_type_id, job_cat_obj.job_category_id)
            if key not in job_exam_cat_cache:
                obj = JobExamCategory.objects.filter(
                    exam_type=exam_type_obj,
                    job_category=job_cat_obj,
                    category_name__iexact=cat_name,
                ).first()
                if not obj:
                    obj = JobExamCategory.objects.create(
                        exam_type=exam_type_obj,
                        job_category=job_cat_obj,
                        category_name=cat_name,
                    )
                job_exam_cat_cache[key] = obj
            return job_exam_cat_cache[key]

        # ── Map top-level group key → canonical ExamType name ──
        TYPE_KEY_MAP = {
            'school':   'School',
            'entrance': 'Entrance',
            'job':      'Job',
        }

        seen_codes = set()
        counters   = {'created': 0, 'updated': 0, 'skipped': 0}

        with transaction.atomic():
            for group_key, exam_list in data.items():
                type_name = TYPE_KEY_MAP.get(group_key, group_key.capitalize())

                for entry in exam_list:
                    raw_code = entry.get('exam_code', '').strip()
                    if not raw_code:
                        self.stdout.write(self.style.WARNING(
                            f"Skipping entry with no exam_code: {entry.get('exam_name')!r}"
                        ))
                        counters['skipped'] += 1
                        continue

                    # De-duplicate across groups
                    code = raw_code
                    if code in seen_codes:
                        code = f"{raw_code}_{group_key.upper()}"
                    seen_codes.add(code)

                    name        = entry.get('exam_name') or raw_code
                    description = entry.get('description') or ''
                    logo        = entry.get('logo') or ''

                    # ── Resolve all tag arrays ──
                    raw_edu_levels  = [t for t in (entry.get('educationLevels') or [])
                                       if t and t not in ('not_applicable',)]
                    raw_streams     = [t for t in (entry.get('streams') or [])
                                       if t and t not in ('not_applicable',)]
                    raw_job_cats    = [t for t in (entry.get('jobCategories') or [])
                                       if t and t not in SKIP_JOB_CATEGORIES]

                    # Tags like "engineering" in educationLevels are actually
                    # domain/stream words — keep them in edu_levels too because
                    # EDU_LEVEL_ALIASES maps "engineering" → "Graduate", which
                    # is semantically correct (graduate-level engineer).

                    if dry_run:
                        counters['created'] += 1
                        continue

                    # ── DB lookups (only executed when not dry-run) ──
                    exam_type_obj = get_exam_type(type_name)

                    edu_level_objs = [get_edu_level(t) for t in raw_edu_levels]
                    stream_objs    = [get_stream(t)    for t in raw_streams]

                    # State: best-effort from code prefix
                    guessed_state = guess_state(code)
                    state_obj = get_state(guessed_state) if guessed_state else None

                    # ExamLevel: National if no state guessed, else State
                    if guessed_state:
                        exam_level_obj = get_exam_level('State')
                    else:
                        # National for most codes without a known state prefix
                        exam_level_obj = get_exam_level('National')

                    # ── category_id: pick first meaningful pair ──
                    category_id = None

                    if group_key == 'job' and raw_job_cats:
                        job_cat_obj = get_job_category(raw_job_cats[0])
                        jec = get_job_exam_category(exam_type_obj, job_cat_obj)
                        category_id = jec.category_id

                    elif group_key == 'entrance':
                        first_edu = edu_level_objs[0] if edu_level_objs else None
                        first_str = stream_objs[0]    if stream_objs    else None
                        ec = get_entrance_category(exam_type_obj, first_edu, first_str)
                        category_id = ec.category_id

                    elif group_key == 'school':
                        first_edu = edu_level_objs[0] if edu_level_objs else None
                        first_str = stream_objs[0]    if stream_objs    else None
                        sc = get_school_exam_category(exam_type_obj, first_edu, first_str)
                        category_id = sc.category_id

                    # ── Upsert the Exam row ──
                    defaults = dict(
                        exam_type=exam_type_obj,
                        field=None,        # no per-exam field_of_study in this JSON
                        sub_field=None,    # same
                        level=exam_level_obj,
                        board=None,        # no board_id in this JSON
                        state=state_obj,
                        category_id=category_id,
                        exam_name=name,
                        description=description,
                        is_active=True,
                    )
                    # Conditionally add logo/test_count if the model has them
                    if hasattr(Exam, 'logo'):
                        defaults['logo'] = logo
                    if hasattr(Exam, 'test_count'):
                        defaults['test_count'] = entry.get('testCount') or ''

                    exam, created = Exam.objects.update_or_create(
                        exam_code=code,
                        defaults=defaults,
                    )

                    # ── M2M: set all tags (replaces any prior set) ──
                    exam.education_levels.set(edu_level_objs)
                    exam.streams.set(stream_objs)

                    counters['created' if created else 'updated'] += 1

        total = counters['created'] + counters['updated']
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[dry-run] Would import {total} exams "
                f"({len(seen_codes)} unique exam_codes, "
                f"{counters['skipped']} skipped for missing exam_code)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Done. {total} exams processed "
                f"(new={counters['created']}, updated={counters['updated']}, "
                f"skipped={counters['skipped']})."
            ))