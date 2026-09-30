<template>
  <ImportQuestionsUpload
    v-if="step === 1"
    :error="uploadError"
    :submitting="submitting"
    @file-selected="handleFileSelected"
  />

  <ImportQuestionsMapColumns
    v-else-if="step === 2"
    :file-name="fileName"
    :total-rows="validateResult?.totalRows ?? 0"
    @previous="step = 1"
    @next="step = 3"
  />

  <ImportQuestionsPreviewValidate
    v-else-if="step === 3"
    :total-rows="validateResult?.totalRows ?? 0"
    :valid-rows="validateResult?.validRows ?? []"
    :error-rows="validateResult?.invalidRows ?? []"
    :duplicate-rows="validateResult?.duplicateRows ?? []"
    :importing="submitting"
    :import-error="importError"
    @previous="step = 2"
    @confirm-import="handleConfirmImport"
  />

  <ImportQuestionsProgress
    v-else-if="step === 4"
    :total="validateResult?.totalRows ?? 0"
  />

  <ImportQuestionsSuccess
    v-else-if="step === 5"
    :total="validateResult?.totalRows ?? 0"
    :imported="importResult?.imported ?? 0"
    :failed="importResult?.skipped ?? 0"
    :duplicates="(validateResult?.duplicateRows ?? []).length"
    @go-to-question-bank="goToQuestionBank"
  />
</template>

<script setup>
/**
 * Owns the whole 5-step import flow and talks to the real backend:
 *   POST /api/mockexams/<mockexamId>/bulk-upload/validate/   (multipart: file)
 *   POST /api/mockexams/<mockexamId>/bulk-upload/import/     (json: { upload_id })
 *
 * Adjust API_BASE below (or wire it to your existing axios instance /
 * api client) to match how the rest of the app talks to the backend.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ImportQuestionsUpload from './ImportQuestionsUpload.vue'
import ImportQuestionsMapColumns from './ImportQuestionsMapColumns.vue'
import ImportQuestionsPreviewValidate from './ImportQuestionsPreviewValidate.vue'
import ImportQuestionsProgress from './ImportQuestionsProgress.vue'
import ImportQuestionsSuccess from './ImportQuestionsSuccess.vue'

const props = defineProps({
  mockexamId: { type: [String, Number], required: true },
})
defineEmits(['go-to-question-bank'])

const router = useRouter()
// CHANGED: this component is now mounted directly by the router (see
// router/index.ts) instead of being nested under a parent that listened
// for 'go-to-question-bank'. With no parent, that emit went nowhere, so
// the button did nothing. Navigate directly instead.
function goToQuestionBank() {
  router.push({ name: 'question-bank' })
}

// '' works fine here: in dev, vite.config.ts proxies /api to the Django
// backend container, and in prod the frontend and API share an origin.
const API_BASE = ''

const step = ref(1)
const submitting = ref(false)
const uploadError = ref('')
const importError = ref('')

const fileName = ref('')
const validateResult = ref(null) // { upload_id, totalRows, validRows, invalidRows, duplicateRows }
const importResult = ref(null)   // { imported, skipped }

async function handleFileSelected(file) {
  uploadError.value = ''
  fileName.value = file.name

  // Client-side guardrails matching the backend's own checks, so
  // obviously-bad files fail fast instead of round-tripping.
  const allowed = ['.xlsx', '.xls', '.csv']
  const lower = file.name.toLowerCase()
  if (!allowed.some((ext) => lower.endsWith(ext))) {
    uploadError.value = 'Unsupported file type. Please upload .xlsx, .xls, or .csv.'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    uploadError.value = 'File exceeds the 10 MB limit.'
    return
  }

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(
      `${API_BASE}/api/mockexams/${props.mockexamId}/bulk-upload/validate/`,
      { method: 'POST', body: formData }
    )

    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      uploadError.value =
        data.error ||
        (data.missing_columns
          ? `Missing required column(s): ${data.missing_columns.join(', ')}`
          : 'Something went wrong validating the file.')
      return
    }

    validateResult.value = data
    step.value = 2
  } catch (err) {
    uploadError.value = 'Could not reach the server. Please check your connection and try again.'
    console.error('bulk-upload validate failed:', err)
  } finally {
    submitting.value = false
  }
}

async function handleConfirmImport() {
  if (!validateResult.value?.upload_id) return
  importError.value = ''
  submitting.value = true
  step.value = 4

  try {
    const res = await fetch(
      `${API_BASE}/api/mockexams/${props.mockexamId}/bulk-upload/import/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ upload_id: validateResult.value.upload_id }),
      }
    )

    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      importError.value = data.error || 'Import failed.'
      step.value = 3
      return
    }

    importResult.value = data
    step.value = 5
  } catch (err) {
    importError.value = 'Could not reach the server during import.'
    step.value = 3
    console.error('bulk-upload import failed:', err)
  } finally {
    submitting.value = false
  }
}
</script>