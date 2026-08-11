// Mirrors the fields returned by ExamSerializer:
// ['exam_id', 'exam_name', 'exam_year', 'conducting_body']
export interface Exam {
  exam_id: number
  exam_name: string
  exam_year: number
  conducting_body: string
  exam_category?: string
  // Optional fields used by the new list-style TestCard design.
  // Add these to ExamSerializer when ready; the UI falls back gracefully
  // with sensible defaults if they're missing from the API response.
  question_count?: number
  duration_minutes?: number
  difficulty?: 'easy' | 'medium' | 'hard'
  language?: string
  is_bookmarked?: boolean
}

export interface ExamFilters {
  exam_category: string
  exam_year: string
  stream?: string
  graduation?: string
  subject?: string
  difficulty?: string[]
  // UI-only, carried through from the exam-first flow (Step 2/3).
  // Not yet sent to the API — wire in once the backend supports
  // exam_stage / mode filtering.
  exam_stage?: string
  mode?: TabValue
}

// UI-only filter state (not yet sent to the API — see Sidebar.vue)
export interface SidebarState extends ExamFilters {
  difficulty: string[]
  language: string[]
  status: string[]
  stream: string
  graduation: string
  subject: string
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

// --- New: exam-first flow (Step 1 and Step 2) ---------------------------

export interface ExamCategoryMeta {
  id: string
  label: string
  shortLabel: string // matches TestCard's logo-mark convention (<=6 chars)
  // Sub-stages shown in Step 2 (ExamVariantSelect). Omit for categories
  // that go straight from Step 1 to Step 3 (mode selection).
  variants?: string[]
}

// Same categories already wired into Sidebar.vue's exam_category select
// and used by DEMO_EXAMS in ExamView.vue, so filtering stays consistent
// end to end. Add exam_stage variants here as the backend gains support
// for them; categories without a `variants` array skip Step 2 entirely.
export const EXAM_CATEGORIES: ExamCategoryMeta[] = [
  { id: 'UPSC', label: 'UPSC', shortLabel: 'UPSC', variants: ['Prelims', 'Mains'] },
  { id: 'SSC', label: 'SSC', shortLabel: 'SSC', variants: ['CGL', 'CHSL'] },
  { id: 'BANKING', label: 'Banking', shortLabel: 'BANKIN', variants: ['PO', 'Clerk'] },
  { id: 'RAILWAY', label: 'Railway', shortLabel: 'RAIL' },
  { id: 'STATE_PSC', label: 'State PSC', shortLabel: 'STATE' },
]