// Mirrors the fields returned by ExamSerializer (see serializers.py).
// CHANGED: exam_year is gone — the current Exam model has no such column.
// Added the real filter FKs (exam_type, category_id, education_level,
// stream, field, sub_field, board, state, level) plus their *_name
// companions, since ExamFilterView / the Sidebar now filter on these.
export interface Exam {
  exam_id: number
  exam_code: string
  exam_name: string
  conducting_body: string

  exam_type: number | null
  exam_type_name: string | null
  category_id: number | null
  category_name: string | null
  education_level: number | null
  education_level_name: string | null
  stream: number | null
  stream_name: string | null
  field: number | null
  field_name: string | null
  sub_field: number | null
  sub_field_name: string | null
  board: number | null
  board_name: string | null
  state: number | null
  state_name: string | null
  level: number | null
  level_name: string | null

  question_count?: number
  duration_minutes?: number | null
  difficulty?: 'easy' | 'medium' | 'hard'
  language?: string
  is_bookmarked?: boolean
  is_active?: boolean
}

// ── Filter dropdown option shapes (from /api/filters/*) ───────────────────────

export interface ExamTypeOption {
  exam_type_id: number
  type_name: string
  description?: string | null
}

export interface EducationLevelOption {
  education_level_id: number
  education_level: string
  description?: string | null
}

export interface StreamOption {
  stream_id: number
  stream_name: string
}

export interface FieldOption {
  field_id: number
  stream: number
  field_name: string
}

export interface SubFieldOption {
  sub_field_id: number
  field: number
  sub_field_name: string
}

export interface FieldWithSubFields {
  field_id: number
  field_name: string
  sub_fields: SubFieldOption[]
}

export interface BoardOption {
  board_id: number
  state: number | null
  board_name: string
  board_code?: string
}

export interface StateOption {
  state_id: number
  state_name: string
  state_code?: string
}

export interface ExamLevelOption {
  level_id: number
  level_name: string
  description?: string | null
}

export interface JobCategoryOption {
  job_category_id: number
  job_category_name: string
  description?: string | null
}

// Generic shape shared by SchoolExamCategory / EntranceExamCategory / JobExamCategory
export interface ExamCategoryOption {
  category_id: number
  category_name: string
  description?: string | null
  exam_type?: number
  exam_type_name?: string
  education_level?: number
  education_level_name?: string
  job_category?: number
  job_category_name?: string
}

// ── Filters sent to GET /api/exams/filter/ (ExamFilterView) ───────────────────
// Every *_id is what actually gets sent to the API. The *_label companions
// are UI-only (filled in by Sidebar.vue from the option lists it already
// fetched) so ExamView can render filter chips without a second round trip.
export interface ExamFilters {
  exam_type_id?: number
  exam_type_label?: string
  category_id?: number
  category_label?: string
  job_category_id?: number
  job_category_label?: string
  education_level_id?: number
  education_level_label?: string
  stream_id?: number
  stream_label?: string
  field_id?: number
  field_label?: string
  sub_field_id?: number
  sub_field_label?: string
  board_id?: number
  board_label?: string
  state_id?: number
  state_label?: string
  level_id?: number
  level_label?: string
  search?: string
  page?: number
  page_size?: number
}

export interface ExamFilterMeta {
  total_count: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

// Shape returned by GET /api/exams/filter/
export interface ExamFilterResponse {
  meta: ExamFilterMeta
  filters_applied: Record<string, number | string>
  results: Exam[]
  warnings?: string[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type TabValue = 'all' | 'previous' | 'practice' | 'mock'

export interface TabOption {
  label: string
  value: TabValue
}

export interface CheckboxOption {
  label: string
  value: string
}
// ─────────────────────────────────────────────────────────────────────────────
// ExamWizardForm — mirrors the wizard step structure used by examWizardApi.ts.
// Each nested interface maps 1-to-1 to a wizard step component and to the
// Django model/serializer it eventually writes to.
// ─────────────────────────────────────────────────────────────────────────────

// Step 1 — Basic Info  →  Exam (exam_name, exam_code, description, logo)
export interface WizardBasicInfo {
  examName: string
  shortName: string           // exam_code
  description: string
  examLogo?: File | null      // uploaded File — needs separate media endpoint
  bannerImage?: File | null   // same — URL written after upload
}

// Step 2 — Classification  →  Exam (exam_type FK, level FK, conducting_body)
export interface WizardClassification {
  examType: number | null       // exam_type PK  (from fetchExamTypes())
  examLevel: number | null      // level PK      (from fetchExamLevels())
  conductingBody: string
  examCategory?: number | null  // category PK   (future endpoint)
}

// Step 3 — Academic Mapping  →  Exam (education_levels, streams, field, sub_field)
export interface WizardAcademicMapping {
  educationLevel: number | null  // education_level PK (from fetchEducationLevels())
  stream: number | null          // stream PK          (from fetchStreams())
  field: number | null           // field PK           (from fetchFields())
  subField: number | null        // sub_field PK       (from fetchSubFields())
}

// Step 4 — Exam Details  →  ExamDetail (one-to-one with Exam)
export interface WizardExamDetails {
  ageLimit: string
  applicationMode: string
  examMode: string
  examFrequency: string
  duration: string
  totalMarks: string | number | null
  negativeMarking: boolean
  officialWebsite: string
  helplineContact: string
}

// Step 5 — Exam Pattern  →  ExamPattern + ExamPatternSection[]
export interface WizardPatternSection {
  name: string
  questions: number | string
  marks: number | string
  duration: string
}

export interface WizardExamPattern {
  negativeMarking: boolean
  markingScheme: string
  unattempted: string
  sections: WizardPatternSection[]
}

// Step 6 — Exam Boards  →  ExamBoard[]
export interface WizardExamBoard {
  name: string
  region: string
  status: string
}

// Step 7 — Important Dates  →  ExamImportantDate (one-to-one with Exam)
export interface WizardImportantDates {
  applicationStart: string | null   // ISO date string e.g. "2025-01-15"
  applicationEnd: string | null
  admitCardRelease: string | null
  examDate: string | null
  resultDate: string | null
}

// Step 8 — Eligibility  →  ExamEligibility (one-to-one with Exam)
export interface WizardEligibility {
  educationalQualification: string
  minimumMarks: string
  ageCriteria: string
  otherConditions: string
}

// Step 9 — Syllabus  →  Subject → Chapter → Topic (real relational tables)
export interface WizardTopic {
  name: string
}

export interface WizardChapter {
  name: string
  topics: string[]   // plain topic name strings; mapped to WizardTopic on submit
}

export interface WizardSubject {
  subject: string    // subject_name
  chapters: WizardChapter[]
}

// ── Root form type — one object holds the entire wizard state ─────────────────
export interface ExamWizardForm {
  basicInfo: WizardBasicInfo
  classification: WizardClassification
  academicMapping: WizardAcademicMapping
  examDetails: WizardExamDetails
  examPattern: WizardExamPattern
  examBoards: WizardExamBoard[]
  importantDates: WizardImportantDates
  eligibility: WizardEligibility
  syllabus: WizardSubject[]
}

// ── Blank form factory — use this to initialise the wizard store ──────────────
export function createEmptyExamWizardForm(): ExamWizardForm {
  return {
    basicInfo: {
      examName: '',
      shortName: '',
      description: '',
      examLogo: null,
      bannerImage: null,
    },
    classification: {
      examType: null,
      examLevel: null,
      conductingBody: '',
      examCategory: null,
    },
    academicMapping: {
      educationLevel: null,
      stream: null,
      field: null,
      subField: null,
    },
    examDetails: {
      ageLimit: '',
      applicationMode: '',
      examMode: '',
      examFrequency: '',
      duration: '',
      totalMarks: null,
      negativeMarking: false,
      officialWebsite: '',
      helplineContact: '',
    },
    examPattern: {
      negativeMarking: false,
      markingScheme: '',
      unattempted: '',
      sections: [],
    },
    examBoards: [],
    importantDates: {
      applicationStart: null,
      applicationEnd: null,
      admitCardRelease: null,
      examDate: null,
      resultDate: null,
    },
    eligibility: {
      educationalQualification: '',
      minimumMarks: '',
      ageCriteria: '',
      otherConditions: '',
    },
    syllabus: [],
  }
}