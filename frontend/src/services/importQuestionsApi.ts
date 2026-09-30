// src/services/importQuestionsApi.ts
//
// API layer for the "Import Questions" bulk-upload admin flow
// (Upload -> Map Columns -> Preview & Validate -> Import -> Success).
// Mirrors the pattern used in questionAdminApi.ts.
//
// Adjust the `api` import below to match your project's existing shared
// axios instance if you have one (e.g. `import api from './api'`).

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
})

// ── Types ─────────────────────────────────────────────────────

/** Shape of one row in `validRows`, matching _row_to_preview() in views.py. */
export interface ValidQuestionPreview {
  id: number
  text: string
  subject: string
  chapter: string
  type: string
  difficulty: string
  marks: number
}

/** Shape of one row in `invalidRows` / `duplicateRows`, matching
 *  _invalid_row_to_preview() in views.py. */
export interface InvalidQuestionPreview {
  id: number
  text: string
  subject: string
  chapter: string
  type: string
  difficulty: string
  marks: number
  reason: string
}

export interface ValidateBulkUploadResponse {
  upload_id: string
  totalRows: number
  validRows: ValidQuestionPreview[]
  invalidRows: InvalidQuestionPreview[]
  duplicateRows: InvalidQuestionPreview[]
}

export interface ImportBulkUploadResponse {
  imported: number
  skipped: number
}

// ── Calls ─────────────────────────────────────────────────────

/**
 * POST /api/mockexams/<mockexam_id>/bulk-upload/validate/
 * Multipart body: { file }
 *
 * Parses and validates the uploaded file server-side; returns a
 * short-lived upload_id plus preview-shaped valid/invalid/duplicate rows.
 */
export async function validateBulkUpload(
  mockExamId: string | number,
  file: File,
): Promise<ValidateBulkUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post<ValidateBulkUploadResponse>(
    `/mockexams/${mockExamId}/bulk-upload/validate/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

/**
 * POST /api/mockexams/<mockexam_id>/bulk-upload/import/
 * JSON body: { upload_id }
 *
 * Creates the actual Question/QuestionOption/CorrectAnswer rows from the
 * cached valid rows referenced by upload_id.
 */
export async function importBulkUpload(
  mockExamId: string | number,
  uploadId: string,
): Promise<ImportBulkUploadResponse> {
  const { data } = await api.post<ImportBulkUploadResponse>(
    `/mockexams/${mockExamId}/bulk-upload/import/`,
    { upload_id: uploadId },
  )
  return data
}

/** GET /api/bulk-upload/template/ — triggers download of the .xlsx template. */
export function downloadBulkUploadTemplateUrl(): string {
  return `${api.defaults.baseURL}/bulk-upload/template/`
}