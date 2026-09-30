<template>
  <ImportQuestionsSelectExam
    v-if="step === 0"
    @exam-selected="handleExamSelected"
  />

  <QuestionBankImportUpload
    v-if="step === 1"
    :error="uploadError"
    :submitting="submitting"
    :exam-name="selectedExam?.exam_name"
    @file-selected="handleFileSelected"
    @back="step = 0"
    @change-exam="step = 0"
  />

  <template v-else-if="step === 2">
    <ImportQuestionsPreviewValidate
      :total-rows="validateResult?.totalRows ?? 0"
      :valid-rows="validateResult?.validRows ?? []"
      :error-rows="validateResult?.invalidRows ?? []"
      :duplicate-rows="validateResult?.duplicateRows ?? []"
      :mapped-duplicates="mapDuplicates"
      :importing="submitting"
      :import-error="importError"
      @previous="step = 1"
      @confirm-import="handleConfirmImport"
    />

    <ImportDuplicateModal
      v-if="showDuplicateModal"
      :count="(validateResult?.duplicateRows ?? []).length"
      :exam-name="validateResult?.duplicateExamName || selectedExam?.exam_name"
      @choose="handleDuplicateChoice"
      @close="showDuplicateModal = false"
    />
  </template>

  <ImportQuestionsProgress
    v-else-if="step === 3"
    :total="validateResult?.totalRows ?? 0"
  />

  <ImportQuestionsSuccess
    v-else-if="step === 4"
    :total="validateResult?.totalRows ?? 0"
    :imported="importResult?.imported ?? 0"
    :failed="importResult?.skipped ?? 0"
    :duplicates="(validateResult?.duplicateRows ?? []).length"
    :mapped="importResult?.mapped ?? 0"
    @go-to-question-bank="goToQuestionBank"
  />
</template>

<script setup>
/**
 * QUESTION BANK import wizard — intentionally a SEPARATE component from
 * ImportQuestionsWizard.vue (the mock-exam import flow), not a shared/
 * branching one.
 *
 *   POST /api/exams/<examId>/question-bank/bulk-upload/validate/  (multipart: file)
 *   POST /api/exams/<examId>/question-bank/bulk-upload/import/    (json: { upload_id, mapDuplicates })
 *
 * CHANGED: dropped the separate "Map Columns" step per the updated
 * design — Upload now goes straight to Validate & Preview (4 steps
 * total: Select Exam / Upload File / Validate & Preview / Import Valid
 * Questions), instead of 5.
 *
 * CHANGED: when the validate step reports duplicate questions, a modal
 * ("Duplicate Questions Found!") is shown asking whether to still
 * import those rows ("Yes, Map Them") or leave them skipped ("No, Skip
 * Them"). The choice is sent as `mapDuplicates` on the import call.
 *
 * Other differences from the mock-exam wizard:
 *   - Keyed by examId, not mockexamId — Question Bank questions aren't
 *     attached to any mock test (mock_exam is left null server-side).
 *   - The uploaded file must include a 'subject' column per row
 *     (chapter is optional and auto-created under that subject).
 *   - Duplicate checks compare only against other Question Bank
 *     questions for this exam, not questions used in mock tests.
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ImportQuestionsSelectExam from './ImportQuestionsSelectExam.vue'
import QuestionBankImportUpload from './QuestionBankImportUpload.vue'
import ImportQuestionsPreviewValidate from './ImportQuestionsPreviewValidate.vue'
import ImportQuestionsProgress from './ImportQuestionsProgress.vue'
import ImportQuestionsSuccess from './ImportQuestionsSuccess.vue'
import ImportDuplicateModal from './ImportDuplicateModal.vue'

const router = useRouter()
function goToQuestionBank() {
  router.push({ name: 'question-bank' })
}

// '' works fine here: in dev, vite.config.ts proxies /api to the Django
// backend container, and in prod the frontend and API share an origin.
const API_BASE = ''

const selectedExam = ref(null) // { exam_id, exam_name, ... } — full object from ImportQuestionsSelectExam
const step = ref(0)

function handleExamSelected(exam) {
  selectedExam.value = exam
  step.value = 1
}
const submitting = ref(false)
const uploadError = ref('')
const importError = ref('')

const fileName = ref('')
const validateResult = ref(null) // { upload_id, totalRows, validRows, invalidRows, duplicateRows, duplicateExamName }
const importResult = ref(null)   // { imported, skipped, mapped }

const showDuplicateModal = ref(false)
const mapDuplicates = ref(false) // user's choice from the modal; sent on import

async function handleFileSelected(file) {
  uploadError.value = ''
  fileName.value = file.name

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
      `${API_BASE}/api/exams/${selectedExam.value.exam_id}/question-bank/bulk-upload/validate/`,
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
    mapDuplicates.value = false
    step.value = 2

    // If duplicates were found, ask the admin whether to import them anyway.
    if ((data.duplicateRows ?? []).length > 0) {
      showDuplicateModal.value = true
    }
  } catch (err) {
    uploadError.value = 'Could not reach the server. Please check your connection and try again.'
    console.error('question-bank bulk-upload validate failed:', err)
  } finally {
    submitting.value = false
  }
}

function handleDuplicateChoice(mapThem) {
  mapDuplicates.value = mapThem
  showDuplicateModal.value = false
}

async function handleConfirmImport() {
  if (!validateResult.value?.upload_id) return
  importError.value = ''
  submitting.value = true
  step.value = 3

  try {
    const res = await fetch(
      `${API_BASE}/api/exams/${selectedExam.value.exam_id}/question-bank/bulk-upload/import/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          upload_id: validateResult.value.upload_id,
          mapDuplicates: mapDuplicates.value,
        }),
      }
    )

    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      importError.value = data.error || 'Import failed.'
      step.value = 2
      return
    }

    importResult.value = data
    step.value = 4
  } catch (err) {
    importError.value = 'Could not reach the server during import.'
    step.value = 2
    console.error('question-bank bulk-upload import failed:', err)
  } finally {
    submitting.value = false
  }
}
</script>