// src/services/mockTestApi.ts
//
// API layer for the "Create Mock Test" admin wizard
// (BasicDetailsStep -> SelectExamStep -> SetPatternStep -> ReviewConfirmStep).
//
// Adjust the `api` import below to match whatever axios instance your
// project already uses elsewhere (e.g. the one used by filtersApi.ts).
// If you don't have one yet, a plain axios.create() is included as a
// fallback at the bottom — swap it out once you point this at your
// real base client.

import axios from 'axios'

// ── Base client ──────────────────────────────────────────────
// CHANGE THIS to import your project's existing shared axios
// instance instead, e.g.:
//   import api from './api'
// Kept local here so this file works standalone until you wire it in.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
})

// ── Types ─────────────────────────────────────────────────────

export interface ExamType {
  exam_type_id: number
  type_name: string
  description?: string | null
}

export interface ExamCategory {
  category_id: number
  category_name: string
  exam_type?: number
  exam_type_name?: string
  education_level?: number
  education_level_name?: string
  job_category?: number
  job_category_name?: string
  description?: string | null
}

export interface ExamSummary {
  exam_id: number
  exam_code: string
  exam_name: string
  conducting_body?: string | null
  exam_type?: number
  exam_type_name?: string | null
  category_id?: number | null
  category_name?: string | null
  education_levels?: number[]
  education_level_names?: string[]
  streams?: number[]
  stream_names?: string[]
  question_count?: number
  duration_minutes?: number | null
  difficulty?: string
  language?: string
  is_active?: boolean
}

export interface SubjectRow {
  subject_id: number
  subject_name: string
  chapter_count?: number
}

/** Raw shape actually returned by SubjectSerializer (serializers.py):
 *  { id, label, test_count } — aliased from subject_id/subject_name/chapter_count.
 *  fetchSubjectsForExam() normalizes this back to SubjectRow below. */
interface RawSubjectRow {
  id?: number
  subject_id?: number
  label?: string
  subject_name?: string
  name?: string
  test_count?: number
  chapter_count?: number
}

export interface MockExamPatternSubject {
  name: string
  subject_id?: number
  questions?: number | string
  marks?: number | string
}

export interface MockExamPattern {
  totalQuestions?: number | string
  totalMarks?: number | string
  marksPerQuestion?: number | string
  negativeMarking?: string
  sectionalTime?: boolean
  sectionalMinutes?: number | string
  subjects?: MockExamPatternSubject[]
}

export interface MockExamPayload {
  exam: number // exam_id chosen in SelectExamStep
  mockexam_name: string
  year?: number | string | null
  description?: string | null
  total_marks?: number | string | null
  duration_minutes?: number | string | null
  is_active?: boolean
  pattern?: MockExamPattern
  /**
   * Optional: question PKs to attach inline on creation/update.
   * Include if your backend supports it; otherwise omit here and call
   * addQuestionsToMockExam() separately after the exam is created.
   */
  question_ids?: number[]
}

export interface MockExam {
  mockexam_id: number
  exam_id: number
  exam_code: string
  mockexam_name: string
  year: number | null
  description: string | null
  total_marks: number | null
  duration_minutes: number | null
  question_count: number
  pattern: MockExamPattern | Record<string, never>
  is_active: boolean
  created_at: string
  updated_at: string
  // Optional fields the /mockexams/ list endpoint may include for display
  // (exam name/type/category, subject count, archive flag). All optional
  // so this type keeps working even if your serializer doesn't send them
  // yet — the table page falls back to '—' when they're missing.
  exam_name?: string
  exam_type_name?: string
  category_name?: string
  subjects_count?: number
  is_archived?: boolean
}

// ── Question Bank (Add Questions step) ───────────────────────

/**
 * A single question returned by the question bank endpoint.
 * Maps to the row shape used by AddQuestionsStep.vue.
 */
export interface QuestionBankItem {
  /** Internal PK */
  id: number
  /** Human-readable question identifier, e.g. "Q12345" */
  questionId: string
  /** Question stem / display text */
  text: string
  subject: string
  chapter: string
  /** e.g. "MCQ" | "MSQ" | "Integer" */
  type: string
  /** "Easy" | "Medium" | "Hard" */
  difficulty: string
  marks: number
  /** Runtime selection flag — managed by AddQuestionsStep, not stored on the backend */
  selected?: boolean
}

export interface QuestionBankParams {
  exam_id?: number | string
  subject?: string
  chapter?: string
  type?: string
  difficulty?: string
  search?: string
  page?: number
  page_size?: number
}

export interface QuestionBankResponse {
  results: QuestionBankItem[]
  count: number
}

/**
 * GET /api/questions/bank/
 * Returns paginated questions for the question bank table in AddQuestionsStep.
 * Pass exam_id to scope questions to the selected exam's syllabus.
 *
 * Backend note: expects the serializer to return fields:
 *   id, question_id (→ questionId), text (question stem), subject_name (→ subject),
 *   chapter_name (→ chapter), question_type (→ type), difficulty, marks
 *
 * If your serializer uses different field names, adjust the mapping in the
 * normaliseQuestion() helper below.
 */
export async function fetchQuestionBank(
  params: QuestionBankParams = {},
): Promise<QuestionBankItem[]> {
  const { data } = await api.get<QuestionBankResponse | QuestionBankItem[]>('/questions/bank/', {
    params: {
      ...(params.exam_id ? { exam_id: params.exam_id } : {}),
      ...(params.subject ? { subject: params.subject } : {}),
      ...(params.chapter ? { chapter: params.chapter } : {}),
      ...(params.type ? { question_type: params.type } : {}),
      ...(params.difficulty ? { difficulty: params.difficulty } : {}),
      ...(params.search ? { search: params.search } : {}),
      page: params.page ?? 1,
      page_size: params.page_size ?? 100,
    },
  })
  // Support both paginated { results, count } and plain array responses.
  const raw: any[] = Array.isArray(data) ? data : (data as QuestionBankResponse).results ?? []
  return raw.map(normaliseQuestion)
}

/** Maps backend field names → the shape AddQuestionsStep expects. */
function normaliseQuestion(raw: any): QuestionBankItem {
  return {
    id: raw.id,
    questionId: raw.question_id ?? raw.questionId ?? String(raw.id),
    text: raw.text ?? raw.question_text ?? raw.stem ?? '',
    subject: raw.subject_name ?? raw.subject ?? '',
    chapter: raw.chapter_name ?? raw.chapter ?? '',
    type: raw.question_type ?? raw.type ?? 'MCQ',
    difficulty: raw.difficulty ?? 'Medium',
    marks: Number(raw.marks ?? 4),
    selected: false,
  }
}

/**
 * POST /api/mockexams/<id>/questions/
 * Attaches a list of question IDs to an already-created mock exam.
 * Call this after createMockExam() succeeds (from ReviewConfirmStep or the
 * parent wizard) if your backend separates exam creation from question assignment.
 */
export async function addQuestionsToMockExam(
  mockexamId: number | string,
  questionIds: number[],
): Promise<void> {
  await api.post(`/mockexams/${mockexamId}/questions/`, { question_ids: questionIds })
}

export interface MockExamQuestionsResponse {
  results: QuestionBankItem[]
  count: number
}

/**
 * GET /api/mockexams/<id>/questions/
 * Returns the questions already attached to this mock test. Used by
 * AddQuestionsStep.vue in edit mode to re-mark previously-added
 * questions as selected when the wizard is re-opened for an existing
 * mock test — without this, editing a mock test would silently drop
 * its existing question set on save.
 */
export async function fetchMockExamQuestions(
  mockexamId: number | string,
): Promise<MockExamQuestionsResponse> {
  const { data } = await api.get<MockExamQuestionsResponse | QuestionBankItem[]>(
    `/mockexams/${mockexamId}/questions/`,
  )
  // Support both paginated { results, count } and plain array responses,
  // same as fetchQuestionBank() above.
  const raw: any[] = Array.isArray(data) ? data : (data as MockExamQuestionsResponse).results ?? []
  const results = raw.map(normaliseQuestion)
  return { results, count: Array.isArray(data) ? results.length : (data as MockExamQuestionsResponse).count ?? results.length }
}

// ── Bulk Upload Questions (Add Questions → Bulk Upload tab) ──

/**
 * One row as returned by the bulk-upload validation step, valid or not.
 * Matches the preview-row shape returned by BulkUploadValidateView on
 * the Django backend.
 */
export interface BulkUploadQuestionRow {
  id: number
  text: string
  subject: string
  chapter: string
  type: string
  difficulty: string
  marks: number
  /** Only present on invalid / duplicate rows — why the row was rejected. */
  reason?: string
}

export interface BulkUploadValidationResult {
  /** Backend cache key — pass directly to importBulkUploadQuestions(). Valid for 10 min. */
  upload_id: string
  totalRows: number
  validRows: BulkUploadQuestionRow[]
  invalidRows: BulkUploadQuestionRow[]
  duplicateRows: BulkUploadQuestionRow[]
}

/**
 * POST /api/mockexams/<mockexamId>/bulk-upload/validate/
 *
 * Sends the file as multipart/form-data (key: "file").
 * The backend (BulkUploadValidateView) parses the Excel/CSV, validates
 * every row for missing required fields, invalid correct-answer format,
 * in-file duplicates, and DB duplicates already linked to this mock exam.
 * Returns categorised row previews plus an upload_id for the import step.
 * Does NOT write anything to the database yet.
 */
export async function validateBulkUploadFile(
  mockexamId: number | string,
  file: File,
): Promise<BulkUploadValidationResult> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<BulkUploadValidationResult>(
    `/mockexams/${mockexamId}/bulk-upload/validate/`,
    formData,
    // Let axios set Content-Type with the correct multipart boundary automatically.
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export interface BulkUploadImportResult {
  /** Number of questions successfully created in the database. */
  imported: number
  /** Rows skipped (already 0 because duplicates were filtered at validate step). */
  skipped: number
}

/**
 * POST /api/mockexams/<mockexamId>/bulk-upload/import/
 *
 * Body: { upload_id }
 *
 * Commits the validated rows to the database: bulk-creates Question,
 * QuestionOption, and CorrectAnswer rows tied to this mock exam.
 * Subject / Chapter rows are created automatically if they don't exist yet.
 * The backend cache entry (keyed by upload_id) is deleted after import
 * so it cannot be replayed.
 */
export async function importBulkUploadQuestions(
  mockexamId: number | string,
  uploadId: string,
): Promise<BulkUploadImportResult> {
  const { data } = await api.post<BulkUploadImportResult>(
    `/mockexams/${mockexamId}/bulk-upload/import/`,
    { upload_id: uploadId },
  )
  return data
}

/**
 * Returns the URL for the Excel template download.
 * Used as the :href on the "Download Template" anchor in BulkUploadQuestions.vue.
 * Endpoint: GET /api/bulk-upload/template/
 */
export function bulkUploadTemplateUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL || '/api'
  return `${base}/bulk-upload/template/`
}

// ── Select Exam step ─────────────────────────────────────────

/** GET /api/filters/exam-types/ */
export async function fetchExamTypes(): Promise<ExamType[]> {
  const { data } = await api.get<ExamType[]>('/filters/exam-types/')
  return data
}

/**
 * GET /api/filters/exam-categories/?exam_type_id=&education_level_id=
 * exam_type_id is required by the backend (ExamCategoryListView).
 */
export async function fetchExamCategories(
  examTypeId: number | string,
  educationLevelId?: number | string,
): Promise<ExamCategory[]> {
  const { data } = await api.get<ExamCategory[]>('/filters/exam-categories/', {
    params: {
      exam_type_id: examTypeId,
      ...(educationLevelId ? { education_level_id: educationLevelId } : {}),
    },
  })
  return data
}

/**
 * GET /api/exams/?exam_type=&category_id=&search=
 * Backs the "Search and select exam" input in SelectExamStep.
 * Debounce calls to this on the frontend (see SelectExamStep.vue).
 */
export async function searchExams(params: {
  search?: string
  exam_type?: number | string
  category_id?: number | string
  page?: number
}): Promise<{ results: ExamSummary[]; count: number }> {
  const { data } = await api.get('/exams/', { params })
  return data
}

/** GET /api/exams/<exam_id>/ — full detail, used for the preview box. */
export async function fetchExamDetail(examId: number | string): Promise<ExamSummary> {
  const { data } = await api.get<ExamSummary>(`/exams/${examId}/`)
  return data
}

// ── Set Pattern step ─────────────────────────────────────────

/**
 * GET /api/subjects/?exam_id=
 * Populates the "Subjects & Questions" table in SetPatternStep once an
 * exam is chosen. Handles three common backend response shapes:
 *   1. { exam_id, count, subjects: [...] }   ← preferred
 *   2. { results: [...] }                    ← DRF paginated
 *   3. [...]                                 ← plain array
 *
 * The backend's SubjectSerializer returns items shaped like
 * { id, label, test_count } (aliased from subject_id/subject_name/
 * chapter_count) rather than { subject_id, subject_name, chapter_count }
 * directly — normalizeSubjectRow() below maps either shape onto
 * SubjectRow so callers (SetPatternStep.vue) always get subject_name /
 * subject_id populated regardless of which shape comes back.
 */
function normalizeSubjectRow(raw: RawSubjectRow): SubjectRow {
  return {
    subject_id: raw.subject_id ?? raw.id ?? 0,
    subject_name: raw.subject_name ?? raw.label ?? raw.name ?? '',
    chapter_count: raw.chapter_count ?? raw.test_count,
  }
}

export async function fetchSubjectsForExam(
  examId: number | string,
): Promise<{ exam_id: number; count: number; subjects: SubjectRow[] }> {
  const { data } = await api.get('/subjects/', { params: { exam_id: examId } })

  // Shape 1 — { exam_id, count, subjects: [...] }
  if (data && Array.isArray(data.subjects)) {
    return { ...data, subjects: data.subjects.map(normalizeSubjectRow) }
  }

  // Shape 2 — DRF paginated: { results: [...] }
  if (data && Array.isArray(data.results)) {
    return {
      exam_id: Number(examId),
      count: data.count ?? data.results.length,
      subjects: data.results.map(normalizeSubjectRow),
    }
  }

  // Shape 3 — plain array
  if (Array.isArray(data)) {
    return { exam_id: Number(examId), count: data.length, subjects: data.map(normalizeSubjectRow) }
  }

  return { exam_id: Number(examId), count: 0, subjects: [] }
}

// ── Review & Confirm step ────────────────────────────────────

/** POST /api/mockexams/ — creates the mock test. */
export async function createMockExam(payload: MockExamPayload): Promise<MockExam> {
  const { data } = await api.post<MockExam>('/mockexams/', payload)
  return data
}

/**
 * Creates a minimal DRAFT mock exam (is_active: false) as early as
 * possible in the wizard — right after Basic Details + Select Exam are
 * filled in — so that later steps (Add Questions / Bulk Upload) have a
 * real mockexam_id to attach to instead of null.
 *
 * The wizard should call this once (e.g. when leaving Step 2 "Select
 * Exam", or at the start of Step 4 "Add Questions" if not already
 * created) and store the returned mockexam_id in its own state. Every
 * later step should then use updateMockExam()/patchMockExam() against
 * that same id instead of calling createMockExam() again.
 */
export async function createDraftMockExam(
  examId: number | string,
  basic: Record<string, any>,
  pattern: Record<string, any> = {},
): Promise<MockExam> {
  const payload = buildMockExamPayload(examId, basic, pattern, [])
  payload.is_active = false
  const { data } = await api.post<MockExam>('/mockexams/', payload)
  return data
}

/** GET /api/mockexams/<id>/ — re-open an existing mock test in the wizard. */
export async function fetchMockExam(mockexamId: number | string): Promise<MockExam> {
  const { data } = await api.get<MockExam>(`/mockexams/${mockexamId}/`)
  return data
}

/** PUT /api/mockexams/<id>/ — full update (same shape as create). */
export async function updateMockExam(
  mockexamId: number | string,
  payload: MockExamPayload,
): Promise<MockExam> {
  const { data } = await api.put<MockExam>(`/mockexams/${mockexamId}/`, payload)
  return data
}

/** PATCH /api/mockexams/<id>/ — partial update, e.g. { is_active: true } to publish. */
export async function patchMockExam(
  mockexamId: number | string,
  partial: Partial<MockExamPayload>,
): Promise<MockExam> {
  const { data } = await api.patch<MockExam>(`/mockexams/${mockexamId}/`, partial)
  return data
}

// ── Mock Tests table page ────────────────────────────────────

export interface MockExamListParams {
  page?: number
  page_size?: number
  search?: string
  exam_type?: number | string
  category_id?: number | string
  /** 'Active' | 'Inactive' — passed straight through as ?status= to the backend. */
  status?: string
}

export interface MockExamListResponse {
  results: MockExam[]
  count: number
}

/**
 * GET /api/mockexams/?search=&exam_type=&category_id=&status=&page=&page_size=
 * Backs the Mock Tests table. exam_id/exam_code are intentionally
 * omitted here — the admin table browses across ALL exams, unlike the
 * student "Select Mock Test" screen which scopes to one exam.
 */
export async function listMockExams(params: MockExamListParams = {}): Promise<MockExamListResponse> {
  const { data } = await api.get('/mockexams/', { params })
  return {
    results: data.results ?? data,
    count: data.count ?? (data.results ?? data).length,
  }
}

export interface MockExamStats {
  total: number
  published: number
  draft: number
  archived: number
}

/**
 * GET /api/mockexams/stats/ — powers the 4 stat cards at the top of the
 * table page. If you don't have this endpoint yet, either add a small
 * DRF view that returns these 4 counts, or delete this function and
 * compute the numbers client-side from listMockExams() instead.
 */
export async function fetchMockExamStats(): Promise<MockExamStats> {
  const { data } = await api.get('/mockexams/stats/')
  return data
}

// ── Mock Test Action Buttons (👁 View · ✏ Edit · 🗑 Delete) ──

/** One subject row in the mock test detail panel (View modal). */
export interface MockExamSubjectDetail {
  name: string
  /** Planned questions from the pattern JSON */
  planned_questions: number
  /** Planned marks from the pattern JSON */
  planned_marks: number
  /** Live count of uploaded questions for this subject */
  uploaded_questions: number
}

/**
 * Full detail shape returned by GET /api/mockexams/<id>/.
 * Extends MockExam with subjects_detail for the View modal/page.
 */
export interface MockExamDetail extends MockExam {
  subjects_detail: MockExamSubjectDetail[]
}

/**
 * Returned by DELETE /api/mockexams/<id>/ when the mock exam has linked
 * questions and ?force=true was NOT passed.
 * Use question_count to populate the confirmation dialog.
 */
export interface MockExamDeleteConflict {
  error: string
  detail: string
  mockexam_id: number
  mockexam_name: string
  question_count: number
}

/** Returned by DELETE /api/mockexams/<id>/?force=true on success. */
export interface MockExamDeleteResult {
  message: string
  mockexam_id: number
  questions_deleted: number
}

/** Returned by PATCH /api/mockexams/<id>/toggle-status/ */
export interface MockExamToggleResult {
  mockexam_id: number
  is_active: boolean
  status_label: 'Active' | 'Inactive'
  /** Full updated row — replace the local list item in-place with this. */
  row: MockExam
}

/**
 * 👁 VIEW
 * GET /api/mockexams/<mockexamId>/
 *
 * Returns full mock test detail including subjects_detail
 * (planned vs uploaded questions per subject) for the View modal.
 */
export async function fetchMockExamDetail(
  mockexamId: number | string,
): Promise<MockExamDetail> {
  const { data } = await api.get<MockExamDetail>(`/mockexams/${mockexamId}/`)
  return data
}

/**
 * 🗑 DELETE
 * DELETE /api/mockexams/<mockexamId>/
 *
 * Two-step safe deletion:
 *
 * Step 1 — call without force (default):
 *   • No questions → deletes immediately → { deleted: true, result }
 *   • Has questions → backend returns HTTP 409 → { deleted: false, conflict }
 *     Use conflict.question_count to show a confirmation dialog.
 *
 * Step 2 — call with force=true after the user confirms:
 *   • Hard-deletes the mock exam + all child questions / options / answers.
 *   • Returns { deleted: true, result } with questions_deleted count.
 *
 * Usage in Vue component:
 *   const r = await deleteMockExam(row.mockexam_id)
 *   if (!r.deleted) {
 *     const ok = await confirm(`Also delete ${r.conflict.question_count} questions?`)
 *     if (ok) await deleteMockExam(row.mockexam_id, true)
 *   }
 */
export async function deleteMockExam(
  mockexamId: number | string,
  force = false,
): Promise<
  | { deleted: true; result: MockExamDeleteResult }
  | { deleted: false; conflict: MockExamDeleteConflict }
> {
  try {
    const { data } = await api.delete<MockExamDeleteResult>(
      `/mockexams/${mockexamId}/`,
      { params: force ? { force: 'true' } : {} },
    )
    return { deleted: true, result: data }
  } catch (err: any) {
    if (err?.response?.status === 409) {
      return { deleted: false, conflict: err.response.data as MockExamDeleteConflict }
    }
    throw err
  }
}

/**
 * 🔄 TOGGLE STATUS
 * PATCH /api/mockexams/<mockexamId>/toggle-status/
 *
 * Flips is_active (Active ↔ Inactive) with no request body needed.
 * Returns the updated row for in-place list replacement:
 *
 *   const result = await toggleMockExamStatus(row.mockexam_id)
 *   Object.assign(row, result.row)
 */
export async function toggleMockExamStatus(
  mockexamId: number | string,
): Promise<MockExamToggleResult> {
  const { data } = await api.patch<MockExamToggleResult>(
    `/mockexams/${mockexamId}/toggle-status/`,
  )
  return data
}

/**
 * Builds the POST/PUT payload from the wizard's step form objects.
 * Centralizing this mapping here means CreateMockTestView.vue doesn't
 * need to know the backend's exact field names.
 *
 * @param selectedQuestions - Questions chosen in AddQuestionsStep.
 *   If your backend accepts question_ids inline on the mockexam payload,
 *   they are included here. Otherwise call addQuestionsToMockExam()
 *   separately after the exam is created.
 */
export function buildMockExamPayload(
  examId: number | string,
  basic: Record<string, any>,
  pattern: Record<string, any>,
  selectedQuestions: QuestionBankItem[] = [],
): MockExamPayload {
  return {
    exam: Number(examId),
    mockexam_name: basic.name,
    year: basic.year || null,
    description: basic.description || null,
    total_marks: basic.totalMarks || null,
    duration_minutes: basic.duration || null,
    is_active: !!basic.active,
    pattern: {
      totalQuestions: pattern.totalQuestions,
      totalMarks: pattern.totalMarks,
      marksPerQuestion: pattern.marksPerQuestion,
      negativeMarking: pattern.negativeMarking,
      sectionalTime: pattern.sectionalTime,
      sectionalMinutes: pattern.sectionalMinutes,
      subjects: pattern.subjects,
    },
    // Include selected question IDs if your backend supports inline assignment.
    // If not, remove this line and call addQuestionsToMockExam() after creation.
    ...(selectedQuestions.length
      ? { question_ids: selectedQuestions.map(q => q.id) }
      : {}),
  }
}