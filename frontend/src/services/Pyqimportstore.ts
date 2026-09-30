// pyqImportStore.ts
import { reactive } from 'vue'

export interface PyqPaperDetails {
  exam_id: number | null
  exam_name: string
  exam_year: number | null
  pyq_session: string
  subject_ids?: number[]
  subject_names?: string[]
  subject_id: number | null
  subject_name: string
  paper_type: string
  difficulty: string
  conducting_body: string
}

export interface PyqSummary {
  totalExtracted: number
  valid: number
  needsReview: number
  failed: number
  // how many questions were already added to a Practice / Custom test
  addedPractice?: number
  addedCustom?: number
}

export interface PyqQuestion {
  index: number
  questionNumber: number
  subject: string | null
  section: string | null
  question_text: string
  question_type: string
  options: {
    A: string
    B: string
    C: string
    D: string
    E: string
  }
  correct_answer: string
  numerical_answer: string
  solution_text: string
  difficulty: string
  marks: number
  negative_marks: number
  status: string
  status_reason: string
  images: string[]
  option_images: {
    A: string | null
    B: string | null
    C: string | null
    D: string | null
  }
  _raw?: string
}

export interface PyqImportState {
  examId: number | null
  uploadId: string | null
  fileName: string
  fileSize: string
  summary: PyqSummary
  paperDetails: PyqPaperDetails
  questions: PyqQuestion[]
  rawText: string
}

/**
 * Shared state for the 4-step "Previous Year Test" import wizard
 */
export const pyqImport: PyqImportState = reactive({
  examId: null,
  uploadId: null,
  fileName: '',
  fileSize: '',
  summary: { totalExtracted: 0, valid: 0, needsReview: 0, failed: 0, addedPractice: 0, addedCustom: 0 },
  paperDetails: {
    exam_id: null,
    exam_name: '',
    exam_year: null,
    pyq_session: '',
    subject_ids: [],
    subject_names: [],
    subject_id: null,
    subject_name: '',
    paper_type: '',
    difficulty: 'Medium',
    conducting_body: '',
  },
  questions: [],
  rawText: '',
})

export function resetPyqImport(): void {
  pyqImport.examId = null
  pyqImport.uploadId = null
  pyqImport.fileName = ''
  pyqImport.fileSize = ''
  pyqImport.summary = { totalExtracted: 0, valid: 0, needsReview: 0, failed: 0, addedPractice: 0, addedCustom: 0 }
  pyqImport.paperDetails = {
    exam_id: null,
    exam_name: '',
    exam_year: null,
    pyq_session: '',
    subject_ids: [],
    subject_names: [],
    subject_id: null,
    subject_name: '',
    paper_type: '',
    difficulty: 'Medium',
    conducting_body: '',
  }
  pyqImport.questions = []
  pyqImport.rawText = ''
}