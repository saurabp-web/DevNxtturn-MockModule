// src/stores/importQuestions.ts
//
// Holds state for the Import Questions flow across its route-based steps
// (/exam-admin/questions/import -> .../import/map-columns -> .../import/preview
// -> .../import/progress -> .../import/success).
//
// CHANGED: the previous approach used a single parent component holding
// step state in local refs, switching steps with v-if. That doesn't work
// here — router/index.ts defines each step as its own route, lazy-loaded
// independently, so Vue Router unmounts the component (and any local
// state) on every navigation. A Pinia store is the fix: it lives outside
// any single component's lifecycle, so the uploaded file, upload_id, and
// validation results survive router.push() between steps.

import { defineStore } from 'pinia'
import {
  validateBulkUpload,
  importBulkUpload,
  type ValidateBulkUploadResponse,
  type ImportBulkUploadResponse,
} from '@/services/importQuestionsApi'

interface ImportQuestionsState {
  mockExamId: string | number | null
  fileName: string
  submitting: boolean
  uploadError: string
  importError: string
  validateResult: ValidateBulkUploadResponse | null
  importResult: ImportBulkUploadResponse | null
}

export const useImportQuestionsStore = defineStore('importQuestions', {
  state: (): ImportQuestionsState => ({
    mockExamId: null,
    fileName: '',
    submitting: false,
    uploadError: '',
    importError: '',
    validateResult: null,
    importResult: null,
  }),

  getters: {
    totalRows: (state) => state.validateResult?.totalRows ?? 0,
    validRows: (state) => state.validateResult?.validRows ?? [],
    invalidRows: (state) => state.validateResult?.invalidRows ?? [],
    duplicateRows: (state) => state.validateResult?.duplicateRows ?? [],
  },

  actions: {
    /** Call once, from the Upload step, before anything else — e.g. from
     *  the route's `?mockExamId=` query param. Nothing here can run
     *  without this, since every backend endpoint is scoped to a mock exam. */
    setMockExamId(id: string | number) {
      this.mockExamId = id
    },

    /** Reset everything — call when the admin starts a fresh import
     *  (navigates to the Upload step directly, or clicks "Import another file"). */
    reset() {
      this.fileName = ''
      this.submitting = false
      this.uploadError = ''
      this.importError = ''
      this.validateResult = null
      this.importResult = null
    },

    /** Client-side guardrails mirroring the backend's own checks in
     *  BulkUploadValidateView, so obviously-bad files fail fast. */
    validateFileClientSide(file: File): string | null {
      const allowed = ['.xlsx', '.xls', '.csv']
      const lower = file.name.toLowerCase()
      if (!allowed.some((ext) => lower.endsWith(ext))) {
        return 'Unsupported file type. Please upload .xlsx, .xls, or .csv.'
      }
      if (file.size > 10 * 1024 * 1024) {
        return 'File exceeds the 10 MB limit.'
      }
      return null
    },

    /** Uploads + validates the file. Returns true on success so the
     *  calling component knows whether to navigate to the next step. */
    async uploadAndValidate(file: File): Promise<boolean> {
      this.uploadError = ''

      if (!this.mockExamId) {
        this.uploadError = 'No mock exam selected. Go back to Question Bank and try again.'
        return false
      }

      const clientError = this.validateFileClientSide(file)
      if (clientError) {
        this.uploadError = clientError
        return false
      }

      this.fileName = file.name
      this.submitting = true
      try {
        this.validateResult = await validateBulkUpload(this.mockExamId, file)
        return true
      } catch (err: any) {
        this.uploadError =
          err?.response?.data?.error ||
          (err?.response?.data?.missing_columns
            ? `Missing required column(s): ${err.response.data.missing_columns.join(', ')}`
            : 'Could not validate the file. Please check your connection and try again.')
        console.error('bulk-upload validate failed:', err)
        return false
      } finally {
        this.submitting = false
      }
    },

    /** Confirms the import using the upload_id from the validate step.
     *  Returns true on success. */
    async confirmImport(): Promise<boolean> {
      this.importError = ''

      if (!this.mockExamId || !this.validateResult?.upload_id) {
        this.importError = 'Nothing to import — please upload a file first.'
        return false
      }

      this.submitting = true
      try {
        this.importResult = await importBulkUpload(this.mockExamId, this.validateResult.upload_id)
        return true
      } catch (err: any) {
        this.importError = err?.response?.data?.error || 'Import failed. Please try again.'
        console.error('bulk-upload import failed:', err)
        return false
      } finally {
        this.submitting = false
      }
    },
  },
})