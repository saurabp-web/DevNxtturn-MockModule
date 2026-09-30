// src/services/questionAdminApi.ts
//
// API layer for the "Add New Question" admin wizard
// (QuestionClassification -> QuestionEditor -> OptionsAnswer -> MarksEvaluation).
//
// Adjust the `api` import below to match whatever axios instance your
// project already uses elsewhere (e.g. the one used by mockTestApi.ts /
// filtersApi.ts). If you don't have one yet, a plain axios.create() is
// included as a fallback at the bottom of the imports — swap it out
// once you point this at your real base client.

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

export interface ExamOption {
  exam_id: number
  exam_name: string
  exam_code?: string
}

export interface SubjectOption {
  subject_id: number
  subject_name: string
  chapter_count?: number
}

/** Raw shape actually returned by SubjectSerializer (serializers.py):
 *  { id, label, test_count } — aliased from subject_id/subject_name/chapter_count.
 *  normalizeSubjectOption() below maps this back to SubjectOption. */
interface RawSubjectOption {
  id?: number
  subject_id?: number
  label?: string
  subject_name?: string
  name?: string
  test_count?: number
  chapter_count?: number
}

export interface ChapterOption {
  chapter_id: number
  chapter_name: string
  question_count?: number
}

/** Raw shape actually returned by ChapterSerializer (serializers.py):
 *  { id, label, question_count } — aliased from chapter_id/chapter_name.
 *  normalizeChapterOption() below maps this back to ChapterOption. */
interface RawChapterOption {
  id?: number
  chapter_id?: number
  label?: string
  chapter_name?: string
  name?: string
  question_count?: number
}

export type QuestionType = 'single_correct' | 'multiple_correct' | 'integer' | 'subjective'
export type DifficultyLevel = 'easy' | 'medium' | 'hard'

export interface QuestionOptionInput {
  id: number | string
  text: string
}

/**
 * Payload assembled by AddQuestion.vue's handleSubmit() from the wizard's
 * four step objects (formData.step1..step4). See buildQuestionPayload()
 * below — that's the single place mapping step data -> this shape, so
 * AddQuestion.vue doesn't need to know the backend's exact field names.
 */
export interface CreateQuestionPayload {
  exam_id: number | string | null
  chapter_id: number | string | null
  question_type: QuestionType
  difficulty: DifficultyLevel
  question_text: string
  options: QuestionOptionInput[]
  correct_answer: number | string | null
  correct_marks: number | null
  negative_marks: number | null
  enable_negative: boolean
  explanation?: string
  /** The raw File object for the question stem image, if one was added. */
  imageFile?: File | null
  /** PYQ (Previous Year Question) source metadata — see QuestionClassification.vue's toggle. */
  is_pyq: boolean
  pyq_exam_id?: number | string | null
  pyq_year?: number | string | null
  pyq_session?: string | null
  /** Set when the admin confirmed the "Question Already Added" modal
   * (Step 2) and chose to map this new PYQ onto another exam/year rather
   * than cancel. References the pre-existing Question this was cloned
   * from, purely for backend logging/audit — it does not change how the
   * new Question row is created. */
  mapped_from_question_id?: number | string | null
}

/** Shape returned by QuestionSerializer (mode='practice') on success. */
export interface CreateQuestionResponse {
  question_id: number
  question_text: string
  difficulty_level: string
  language: string
  question_type: string
  subject_name: string | null
  chapter_name: string | null
  options: unknown[]
  solution: unknown[]
  correct_answer: unknown[]
  hint: string | null
  image_url: Record<string, unknown>
  question_text_latex: string
  is_pyq: boolean
  pyq_exam: number | null
  pyq_exam_name: string | null
  pyq_year: number | null
  pyq_session: string | null
}

/**
 * Shape returned on HTTP 400 by AddQuestionView — a map of
 * field name -> error message, e.g. { correct_answer: '...' }.
 * Use with isQuestionValidationError() below to narrow a caught error.
 */
export interface QuestionValidationError {
  errors: Record<string, string>
}

export function isQuestionValidationError(err: any): err is { response: { data: QuestionValidationError } } {
  return !!err?.response?.data?.errors
}

// ── Question Classification step ─────────────────────────────

/**
 * GET /api/exams/
 * Populates the "Exam" dropdown in QuestionClassification.vue.
 * Handles both the DRF paginated shape ({ results: [...] }) and a plain
 * array, same defensive pattern as fetchSubjectsForExam() in mockTestApi.ts.
 */
export async function fetchExams(): Promise<ExamOption[]> {
  const { data } = await api.get('/exams/')
  const raw: any[] = Array.isArray(data) ? data : data.results ?? []
  return raw.map((e) => ({
    exam_id: e.exam_id,
    exam_name: e.exam_name,
    exam_code: e.exam_code,
  }))
}

function normalizeSubjectOption(raw: RawSubjectOption): SubjectOption {
  return {
    subject_id: raw.subject_id ?? raw.id ?? 0,
    subject_name: raw.subject_name ?? raw.label ?? raw.name ?? '',
    chapter_count: raw.chapter_count ?? raw.test_count,
  }
}

/**
 * GET /api/subjects/?exam_id=
 * Populates the "Subject" dropdown once an exam is chosen. Backend's
 * SubjectListView returns { exam_id, count, subjects: [...] } with each
 * row already shaped like SubjectOption — normalizeSubjectOption() is
 * kept as a defensive pass so this also tolerates the aliased
 * { id, label, test_count } shape used elsewhere (SubjectSerializer).
 */
export async function fetchSubjects(examId: number | string): Promise<SubjectOption[]> {
  const { data } = await api.get('/subjects/', { params: { exam_id: examId } })
  const raw: RawSubjectOption[] = Array.isArray(data) ? data : data.subjects ?? data.results ?? []
  return raw.map(normalizeSubjectOption)
}

function normalizeChapterOption(raw: RawChapterOption): ChapterOption {
  return {
    chapter_id: raw.chapter_id ?? raw.id ?? 0,
    chapter_name: raw.chapter_name ?? raw.label ?? raw.name ?? '',
    question_count: raw.question_count,
  }
}

/**
 * GET /api/chapters/?subject_id=
 * Populates the "Chapter" dropdown once a subject is chosen.
 */
export async function fetchChapters(subjectId: number | string): Promise<ChapterOption[]> {
  const { data } = await api.get('/chapters/', { params: { subject_id: subjectId } })
  const raw: RawChapterOption[] = Array.isArray(data) ? data : data.chapters ?? data.results ?? []
  return raw.map(normalizeChapterOption)
}

// ── Duplicate question check (Step 2, Question Details) ───────

export interface DuplicateQuestionMatch {
  exam_name: string | null
  /** Which exam's paper this question was originally sourced from, if it's
   *  a previous-year question — distinct from exam_name (the exam it's
   *  currently filed under). Can differ or be null; shown separately so
   *  a mismatch (like a leftover bad save) is visible rather than hidden. */
  pyq_exam_name: string | null
  year: number | null
  session: string | null
}

export interface CheckDuplicateResponse {
  duplicate: boolean
  question_id?: number
  existing?: DuplicateQuestionMatch
}

/**
 * POST /api/questions/check-duplicate/
 *
 * Called from the Question Details step (Step 2) — on blur of the
 * question-text field, and again as a guard right before "Next Step" —
 * to detect an already-existing question with the same text and, if it's
 * a PYQ, show the "Question Already Added" modal with its exam/year/session
 * so the admin can choose to map this question onto another exam instead.
 */
export async function checkDuplicateQuestion(
  questionText: string,
  chapterId?: number | string | null,
): Promise<CheckDuplicateResponse> {
  const { data } = await api.post<CheckDuplicateResponse>('/questions/check-duplicate/', {
    question_text: questionText,
    chapter_id: chapterId ?? undefined,
  })
  return data
}

// ── Save Question (Marks & Evaluation → Save) ────────────────

/**
 * POST /api/questions/add/
 *
 * Creates a single Question + QuestionOption + CorrectAnswer (+ Solution
 * if an explanation was given). See AddQuestionView in views.py.
 *
 * Sends multipart/form-data when payload.imageFile is present (needed to
 * carry the file alongside the JSON fields); otherwise sends a plain
 * application/json body.
 *
 * On a 400 validation error, the rejected promise's `err.response.data`
 * matches QuestionValidationError — use isQuestionValidationError(err)
 * to narrow it before reading err.response.data.errors.
 */
export async function createQuestion(
  payload: CreateQuestionPayload,
): Promise<CreateQuestionResponse> {
  const { imageFile, options, ...rest } = payload

  if (imageFile) {
    const formData = new FormData()
    Object.entries(rest).forEach(([key, value]) => {
      if (value === null || value === undefined) return
      formData.append(key, String(value))
    })
    formData.append('options', JSON.stringify(options))
    formData.append('image', imageFile)

    const { data } = await api.post<CreateQuestionResponse>('/questions/add/', formData, {
      // Let axios set Content-Type with the correct multipart boundary automatically.
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  }

  const { data } = await api.post<CreateQuestionResponse>('/questions/add/', { ...rest, options })
  return data
}

/**
 * Builds the POST payload from the wizard's four step form objects.
 * Centralizing this mapping here means AddQuestion.vue doesn't need to
 * know the backend's exact field names.
 *
 * NOTE — Topic: step1.topic is intentionally NOT included. The backend
 * has no Topic model/FK on Question yet (see models.py), so there's
 * nothing to send it to. Add a Topic table + wire it into
 * AddQuestionView first if this needs to be persisted.
 */
export function buildQuestionPayload(
  step1: Record<string, any>,
  step2: Record<string, any>,
  step3: Record<string, any>,
  step4: Record<string, any>,
): CreateQuestionPayload {
  return {
    exam_id: step1?.exam ?? null,
    chapter_id: step1?.chapter ?? null,
    question_type: step1?.questionType,
    difficulty: step1?.difficulty,
    question_text: step2?.text || '',
    options: (step3?.options || []).map((o: any) => ({ id: o.id, text: o.text })),
    correct_answer: step3?.correctAnswer ?? null,
    correct_marks: step4?.correctMarks ?? null,
    negative_marks: step4?.negativeMarks ?? null,
    enable_negative: !!step4?.enableNegative,
    explanation: step4?.explanation || '',
    imageFile: step2?.imageFile ?? null,
    is_pyq: !!step1?.isPyq,
    pyq_exam_id: step1?.isPyq ? (step1?.pyqExam ?? null) : null,
    pyq_year: step1?.isPyq ? (step1?.pyqYear ?? null) : null,
    pyq_session: step1?.isPyq ? (step1?.pyqSession || null) : null,
    mapped_from_question_id: step2?.mappedFromQuestionId ?? null,
  }
}