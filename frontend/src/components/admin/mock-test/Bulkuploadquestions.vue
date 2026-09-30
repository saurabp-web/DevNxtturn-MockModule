<template>
  <div class="bulk-upload">
    <!-- Step header -->
    <div class="flow-header">
      <div class="flow-step" :class="stepHeaderClass(1)">
        <span class="flow-step-badge">
          <span v-if="stepIndex > 1">✓</span>
          <span v-else>1</span>
        </span>
        <span class="flow-step-label">Upload File</span>
      </div>
      <span class="flow-sep">—</span>
      <div class="flow-step" :class="stepHeaderClass(2)">
        <span class="flow-step-badge">
          <span v-if="stepIndex > 2">✓</span>
          <span v-else>2</span>
        </span>
        <span class="flow-step-label">Validate & Preview</span>
      </div>
      <span class="flow-sep">—</span>
      <div class="flow-step" :class="stepHeaderClass(3)">
        <span class="flow-step-badge">
          <span v-if="stepIndex > 3">✓</span>
          <span v-else>3</span>
        </span>
        <span class="flow-step-label">Import Valid Questions</span>
      </div>
    </div>

    <!-- ══════════════════════ STEP 1: Upload File ══════════════════════ -->
    <div v-if="stepIndex === 1" class="panel">
      <p class="panel-sub">Upload Excel or CSV file to import questions in bulk.</p>
      <p v-if="validationError" class="error-banner">{{ validationError }}</p>

      <div class="upload-grid">
        <div
          class="dropzone"
          :class="{ dragging: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <div class="dropzone-icon">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </div>
          <p class="dropzone-title">Drag &amp; drop your file here</p>
          <p class="dropzone-or">or</p>
          <input ref="fileInput" type="file" accept=".xlsx,.xls,.csv" class="hidden-input" @change="onFileSelected" />
          <button class="btn btn-primary" @click="fileInput?.click()">Choose File</button>
          <p class="dropzone-meta">Supports: .xlsx, .xls, .csv</p>
          <p class="dropzone-meta">Maximum file size: 10MB</p>

          <div v-if="selectedFile" class="selected-file">
            <span class="file-icon">📄</span>
            <span class="file-name">{{ selectedFile.name }}</span>
            <button class="file-remove" @click.stop="removeFile">✕</button>
          </div>
        </div>

        <div class="guidelines">
          <h4>Guidelines</h4>
          <ul>
            <li>First row must contain column headers.</li>
            <li>Each row will be treated as a separate question.</li>
            <li>Empty rows will be skipped.</li>
            <li>Duplicate questions will be ignored.</li>
            <li>Only valid questions will be imported.</li>
          </ul>
          <a class="btn btn-outline template-btn" :href="templateUrl" @click="$emit('download-template')">
            <span>⬇</span> Download Template
          </a>
        </div>
      </div>

      <div class="panel-footer">
        <button class="btn btn-outline" @click="$emit('cancel')">Cancel</button>
        <button
          class="btn btn-primary"
          :disabled="!selectedFile || !props.mockexamId"
          :title="!props.mockexamId ? 'Complete the earlier steps to save this mock test first' : ''"
          @click="startValidation"
        >
          Next →
        </button>
      </div>
    </div>

    <!-- ══════════════════ STEP 2a: Validating (progress) ══════════════════ -->
    <div v-else-if="stepIndex === 2 && !validationDone" class="panel">
      <p class="panel-sub">We are validating your file. This may take a few moments.</p>

      <div class="validate-grid">
        <ul class="check-list">
          <li v-for="(task, idx) in validationTasks" :key="task.key" class="check-item" :class="taskStatus(idx)">
            <span class="check-icon">
              <span v-if="taskStatus(idx) === 'completed'">✓</span>
              <span v-else-if="taskStatus(idx) === 'active'" class="spinner"></span>
              <span v-else class="dot"></span>
            </span>
            <span class="check-label">{{ task.label }}</span>
            <span class="check-status">{{ taskStatusLabel(idx) }}</span>
          </li>
        </ul>

        <div class="validate-illustration">
          <div class="illustration-circle">🔍</div>
          <p class="illustration-title">Validating your questions...</p>
          <p class="illustration-sub">Please wait while we check for errors and invalid data.</p>
        </div>
      </div>

      <div class="panel-footer">
        <button class="btn btn-outline" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>

    <!-- ══════════════════ STEP 2b: Validate & Preview results ══════════════════ -->
    <div v-else-if="stepIndex === 2 && validationDone" class="panel">
      <p class="panel-sub">Validation completed. Review the summary and preview your questions.</p>

      <div class="stat-cards">
        <div class="stat-card stat-neutral">
          <span class="stat-label">Total Rows</span>
          <span class="stat-value">{{ validation.totalRows }}</span>
        </div>
        <div class="stat-card stat-success">
          <span class="stat-label">Valid Questions</span>
          <span class="stat-value">{{ validation.validCount }}</span>
        </div>
        <div class="stat-card stat-danger">
          <span class="stat-label">Invalid Questions</span>
          <span class="stat-value">{{ validation.invalidCount }}</span>
        </div>
        <div class="stat-card stat-warning">
          <span class="stat-label">Duplicate Questions</span>
          <span class="stat-value">{{ validation.duplicateCount }}</span>
        </div>
        <div class="stat-card stat-primary">
          <span class="stat-label">Will be Imported</span>
          <span class="stat-value">{{ validation.validCount }}</span>
        </div>
      </div>

      <div class="info-banner">
        <span>ℹ</span> Only {{ validation.validCount }} valid questions will be imported. Invalid and duplicate questions will be skipped.
      </div>

      <div class="preview-tabs">
        <button
          class="preview-tab"
          :class="{ active: previewTab === 'valid' }"
          @click="previewTab = 'valid'"
        >
          Valid Questions ({{ validation.validCount }})
        </button>
        <button
          class="preview-tab"
          :class="{ active: previewTab === 'invalid' }"
          @click="previewTab = 'invalid'"
        >
          Invalid Questions ({{ validation.invalidCount }})
        </button>
        <button
          class="preview-tab"
          :class="{ active: previewTab === 'duplicate' }"
          @click="previewTab = 'duplicate'"
        >
          Duplicate Questions ({{ validation.duplicateCount }})
        </button>
      </div>

      <div class="preview-toolbar">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input v-model="previewSearch" type="text" :placeholder="`Search in ${previewTab} questions...`" />
        </div>
        <button class="btn btn-outline filters-btn"><span>▤</span> Filters</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="col-num">#</th>
              <th>Question</th>
              <th class="col-subject">Subject</th>
              <th class="col-chapter">Chapter</th>
              <th class="col-type">Type</th>
              <th class="col-difficulty">Difficulty</th>
              <th class="col-marks">Marks</th>
              <th v-if="previewTab !== 'valid'" class="col-reason">Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(q, idx) in currentPreviewRows" :key="q.id">
              <td class="col-num">{{ idx + 1 }}</td>
              <td class="question-text">{{ q.text }}</td>
              <td class="col-subject">{{ q.subject }}</td>
              <td class="col-chapter">{{ q.chapter }}</td>
              <td class="col-type"><span class="badge badge-type">{{ q.type }}</span></td>
              <td class="col-difficulty"><span class="badge" :class="difficultyClass(q.difficulty)">{{ q.difficulty }}</span></td>
              <td class="col-marks">{{ q.marks }}</td>
              <td v-if="previewTab !== 'valid'" class="col-reason">{{ q.reason }}</td>
            </tr>
            <tr v-if="currentPreviewRows.length === 0">
              <td :colspan="previewTab !== 'valid' ? 8 : 7" class="empty-row">No questions to show.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel-footer">
        <button class="btn btn-outline" @click="stepIndex = 1">← Back</button>
        <button class="btn btn-primary" :disabled="validation.validCount === 0" @click="startImport">
          Next: Import Valid Questions →
        </button>
      </div>
    </div>

    <!-- ══════════════════ STEP 3a: Importing (progress) ══════════════════ -->
    <div v-else-if="stepIndex === 3 && !importDone" class="panel">
      <p class="panel-sub">We will import only valid questions ({{ validation.validCount }}) to this mock test.</p>
      <p v-if="importError" class="error-banner">{{ importError }}</p>

      <div class="import-progress-card">
        <div class="import-progress-head">
          <strong>Importing questions...</strong>
          <span>{{ importProgress }}%</span>
        </div>
        <div class="progress-bar-track">
          <div class="progress-bar-fill" :style="{ width: importProgress + '%' }"></div>
        </div>

        <ul class="check-list">
          <li v-for="(task, idx) in importTasks" :key="task.key" class="check-item" :class="importTaskStatus(idx)">
            <span class="check-icon">
              <span v-if="importTaskStatus(idx) === 'completed'">✓</span>
              <span v-else-if="importTaskStatus(idx) === 'active'" class="spinner"></span>
              <span v-else class="dot"></span>
            </span>
            <span class="check-label">{{ task.label }}</span>
            <span class="check-status">{{ importTaskStatusLabel(idx) }}</span>
          </li>
        </ul>
      </div>

      <div class="panel-footer">
        <button class="btn btn-outline" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>

    <!-- ══════════════════ STEP 3b: Import Successful ══════════════════ -->
    <div v-else-if="stepIndex === 3 && importDone" class="panel">
      <p class="panel-sub">Import completed successfully.</p>

      <div class="success-grid">
        <div class="success-card">
          <div class="success-icon">✓</div>
          <p class="success-title">Import Successful!</p>
          <p class="success-sub">{{ importedResult.imported }} valid questions have been added to this mock test.</p>
        </div>

        <div class="success-stats">
          <div class="success-stat-row">
            <span>Total Rows</span>
            <strong>{{ validation.totalRows }}</strong>
          </div>
          <div class="success-stat-row">
            <span>Valid Questions Imported</span>
            <strong>{{ validation.validCount }}</strong>
          </div>
          <div class="success-stat-row">
            <span>Invalid Questions Skipped</span>
            <strong>{{ validation.invalidCount }}</strong>
          </div>
          <div class="success-stat-row">
            <span>Duplicate Questions Skipped</span>
            <strong>{{ validation.duplicateCount }}</strong>
          </div>
        </div>
      </div>

      <div class="panel-footer">
        <button class="btn btn-outline" @click="$emit('back-to-add-questions')">← Back to Add Questions</button>
        <button class="btn btn-primary" @click="$emit('done', { imported: importedResult.imported })">Done</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { validateBulkUploadFile, importBulkUploadQuestions, bulkUploadTemplateUrl } from '@/services/mockTestApi'

const props = defineProps({
  mockexamId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['cancel', 'download-template', 'back-to-add-questions', 'done', 'upload'])

const templateUrl = bulkUploadTemplateUrl()
const uploadId = ref(null)
const validationError = ref('')
const importError = ref('')

// ── Wizard state ──────────────────────────────────────────────
const stepIndex = ref(1) // 1 = upload, 2 = validate/preview, 3 = import

function stepHeaderClass(idx) {
  if (idx < stepIndex.value) return 'done'
  if (idx === stepIndex.value) return 'active'
  return 'upcoming'
}

// ── Step 1: file selection ───────────────────────────────────
const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)

function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (file) selectedFile.value = file
}

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) selectedFile.value = file
}

function removeFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

// ── Step 2: validation ────────────────────────────────────────
const validationTasks = [
  { key: 'reading', label: 'Reading file' },
  { key: 'validating', label: 'Validating data' },
  { key: 'duplicates', label: 'Checking duplicates' },
  { key: 'preview', label: 'Preparing preview' }
]
const validationTaskIndex = ref(0)
const validationDone = ref(false)

function taskStatus(idx) {
  if (idx < validationTaskIndex.value) return 'completed'
  if (idx === validationTaskIndex.value) return 'active'
  return 'pending'
}
function taskStatusLabel(idx) {
  const s = taskStatus(idx)
  if (s === 'completed') return 'Completed'
  if (s === 'active') return 'In progress'
  return 'Pending'
}

const validation = reactive({
  totalRows: 0,
  validCount: 0,
  invalidCount: 0,
  duplicateCount: 0,
  validRows: [],
  invalidRows: [],
  duplicateRows: []
})

const previewTab = ref('valid')
const previewSearch = ref('')

const currentPreviewRows = computed(() => {
  const rows =
    previewTab.value === 'valid'
      ? validation.validRows
      : previewTab.value === 'invalid'
      ? validation.invalidRows
      : validation.duplicateRows
  if (!previewSearch.value) return rows
  const needle = previewSearch.value.toLowerCase()
  return rows.filter(r => r.text.toLowerCase().includes(needle))
})

function difficultyClass(level) {
  const map = { Easy: 'badge-easy', Medium: 'badge-medium', Hard: 'badge-hard' }
  return map[level] || 'badge-default'
}

let timers = []
function schedule(fn, delay) {
  const id = setTimeout(fn, delay)
  timers.push(id)
  return id
}
function clearTimers() {
  timers.forEach(clearTimeout)
  timers = []
}
onBeforeUnmount(clearTimers)

async function startValidation() {
  // Guard: the mock test must exist on the backend (i.e. have a real
  // mockexamId) before we can validate a bulk-upload file against it.
  // Without this check, mockexamId ends up as the literal string "null"
  // in the request URL (/mockexams/null/bulk-upload/validate/), which
  // the Django <int:mockexam_id> route can never match, and always 404s.
  if (!props.mockexamId) {
    validationError.value =
      'This mock test hasn\'t been saved yet, so questions can\'t be uploaded to it. ' +
      'Please complete the Basic Details and Select Exam steps first, then try again.'
    return
  }

  stepIndex.value = 2
  validationDone.value = false
  validationTaskIndex.value = 0
  validationError.value = ''

  emit('upload', { file: selectedFile.value, mockexamId: props.mockexamId })

  // Animate the checklist while the real request is in flight. The stages
  // here are cosmetic — they don't reflect true backend progress unless you
  // wire up fetchBulkUploadValidationStatus() polling for large files.
  schedule(() => (validationTaskIndex.value = 1), 400)
  schedule(() => (validationTaskIndex.value = 2), 900)
  schedule(() => (validationTaskIndex.value = 3), 1400)

  try {
    const result = await validateBulkUploadFile(props.mockexamId, selectedFile.value)
    uploadId.value = result.upload_id
    validationTaskIndex.value = 4 // marks all as completed
    applyValidationResult(result)
    validationDone.value = true
  } catch (err) {
    validationError.value = 'Could not validate the file. Please check the format and try again.'
    stepIndex.value = 1
  }
}

function applyValidationResult(result) {
  validation.totalRows = result.totalRows
  validation.validRows = result.validRows
  validation.invalidRows = result.invalidRows
  validation.duplicateRows = result.duplicateRows
  validation.validCount = result.validRows.length
  validation.invalidCount = result.invalidRows.length
  validation.duplicateCount = result.duplicateRows.length
}

// ── Step 3: import ────────────────────────────────────────────
const importTasks = [
  { key: 'import', label: 'Importing valid questions' },
  { key: 'save', label: 'Saving to database' },
  { key: 'finalize', label: 'Finalizing' }
]
const importTaskIndex = ref(0)
const importProgress = ref(0)
const importDone = ref(false)

function importTaskStatus(idx) {
  if (idx < importTaskIndex.value) return 'completed'
  if (idx === importTaskIndex.value) return 'active'
  return 'pending'
}
function importTaskStatusLabel(idx) {
  const s = importTaskStatus(idx)
  if (s === 'completed') return 'Completed'
  if (s === 'active') return 'In progress'
  return 'Pending'
}

async function startImport() {
  stepIndex.value = 3
  importDone.value = false
  importTaskIndex.value = 0
  importProgress.value = 0
  importError.value = ''

  // Cosmetic progress animation while the real import request runs —
  // wire fetchBulkUploadValidationStatus-style polling in if your backend
  // reports true per-row import progress for very large files.
  let progress = 0
  const progressTimer = setInterval(() => {
    progress = Math.min(progress + 6, 92)
    importProgress.value = progress
    if (progress >= 33 && importTaskIndex.value === 0) importTaskIndex.value = 1
    if (progress >= 70 && importTaskIndex.value === 1) importTaskIndex.value = 2
  }, 180)
  timers.push(progressTimer)

  try {
    const result = await importBulkUploadQuestions(props.mockexamId, uploadId.value)
    clearInterval(progressTimer)
    importProgress.value = 100
    importTaskIndex.value = 3
    importedResult.imported = result.imported
    schedule(() => {
      importDone.value = true
    }, 300)
  } catch (err) {
    clearInterval(progressTimer)
    importError.value = 'Could not import the questions. Please try again.'
    stepIndex.value = 2
  }
}

const importedResult = reactive({ imported: 0 })
</script>

<style scoped>
.bulk-upload {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #1f2430;
}

/* Flow header */
.flow-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.flow-step {
  display: flex;
  align-items: center;
  gap: 8px;
}
.flow-step-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #eceef4;
  color: #8a8fa3;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.flow-step.active .flow-step-badge { background: #6c4bf4; color: #fff; }
.flow-step.done .flow-step-badge { background: #22c55e; color: #fff; }
.flow-step-label { font-size: 13px; font-weight: 700; color: #b0b3c2; }
.flow-step.active .flow-step-label,
.flow-step.done .flow-step-label { color: #1f2430; }
.flow-sep { color: #d7d9e4; }

/* Panel */
.panel {
  background: #fff;
  border: 1px solid #eceef4;
  border-radius: 12px;
  padding: 24px;
}
.panel-sub {
  font-size: 13px;
  color: #8a8fa3;
  margin: 0 0 20px;
}
.error-banner {
  background: #fde8e8;
  color: #c0322f;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin: -8px 0 18px;
}
.panel-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
}

/* Step 1: upload */
.upload-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}
.dropzone {
  border: 2px dashed #d7ccff;
  border-radius: 12px;
  background: #fbfaff;
  text-align: center;
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: border-color 0.15s, background 0.15s;
}
.dropzone.dragging { border-color: #6c4bf4; background: #f3efff; }
.dropzone-icon { color: #6c4bf4; margin-bottom: 12px; }
.dropzone-title { font-size: 15px; font-weight: 700; margin: 0 0 4px; color: #1f2430; }
.dropzone-or { font-size: 12px; color: #b0b3c2; margin: 0 0 14px; }
.dropzone-meta { font-size: 12px; color: #8a8fa3; margin: 12px 0 0; }
.hidden-input { display: none; }

.selected-file {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e4e6ef;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12.5px;
  color: #4a4f61;
}
.file-remove {
  border: none;
  background: none;
  color: #b0b3c2;
  cursor: pointer;
  font-size: 12px;
}
.file-remove:hover { color: #e0433f; }

.guidelines {
  border: 1px solid #eceef4;
  border-radius: 12px;
  padding: 20px;
  background: #fbfbfd;
}
.guidelines h4 { font-size: 14px; margin: 0 0 12px; color: #1f2430; }
.guidelines ul { margin: 0 0 18px; padding-left: 18px; }
.guidelines li { font-size: 13px; color: #4a4f61; margin-bottom: 8px; }
.template-btn { width: 100%; justify-content: center; display: flex; align-items: center; gap: 6px; text-decoration: none; box-sizing: border-box; }

/* Step 2a: validating */
.validate-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: center;
}
.check-list { list-style: none; margin: 0; padding: 0; }
.check-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f2f3f8;
}
.check-item:last-child { border-bottom: none; }
.check-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #eceef4;
  color: #8a8fa3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}
.check-item.completed .check-icon { background: #22c55e; color: #fff; }
.check-item.active .check-icon { background: #ede9fe; }
.check-label { flex: 1; font-size: 13.5px; color: #1f2430; font-weight: 500; }
.check-status { font-size: 12px; color: #b0b3c2; }
.check-item.completed .check-status { color: #22c55e; }
.check-item.active .check-status { color: #6c4bf4; }

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c7cadb;
}
.spinner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #d7ccff;
  border-top-color: #6c4bf4;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.validate-illustration {
  text-align: center;
  padding: 20px;
}
.illustration-circle {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: #f3efff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  margin: 0 auto 16px;
}
.illustration-title { font-size: 14px; font-weight: 700; margin: 0 0 4px; color: #1f2430; }
.illustration-sub { font-size: 12.5px; color: #8a8fa3; margin: 0; max-width: 260px; margin-inline: auto; }

/* Step 2b: results */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-label { font-size: 12px; font-weight: 600; }
.stat-value { font-size: 20px; font-weight: 700; }
.stat-neutral { background: #f3f4f9; }
.stat-neutral .stat-label { color: #6b7086; }
.stat-neutral .stat-value { color: #1f2430; }
.stat-success { background: #e6f9ee; }
.stat-success .stat-label { color: #1fa863; }
.stat-success .stat-value { color: #14803f; }
.stat-danger { background: #fde8e8; }
.stat-danger .stat-label { color: #e0433f; }
.stat-danger .stat-value { color: #c0322f; }
.stat-warning { background: #fff4e0; }
.stat-warning .stat-label { color: #d98a1a; }
.stat-warning .stat-value { color: #a86710; }
.stat-primary { background: #ede9fe; }
.stat-primary .stat-label { color: #6c4bf4; }
.stat-primary .stat-value { color: #5433c9; }

.info-banner {
  background: #e6f9ee;
  color: #1fa863;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid #eceef4;
  margin-bottom: 14px;
}
.preview-tab {
  border: none;
  background: none;
  padding: 10px 4px;
  margin-right: 20px;
  font-size: 13px;
  font-weight: 600;
  color: #8a8fa3;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.preview-tab.active {
  color: #6c4bf4;
  border-bottom-color: #6c4bf4;
}

.preview-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}
.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e4e6ef;
  border-radius: 8px;
  padding: 8px 12px;
  background: #fbfbfd;
}
.search-box input { border: none; outline: none; background: transparent; font-size: 13px; width: 100%; }
.filters-btn { white-space: nowrap; }

.table-wrap {
  overflow-x: auto;
  border: 1px solid #eceef4;
  border-radius: 10px;
  scrollbar-width: thin;
  scrollbar-color: #c7cadb #f2f3f8;
}
.table-wrap::-webkit-scrollbar { height: 8px; }
.table-wrap::-webkit-scrollbar-track { background: #f2f3f8; }
.table-wrap::-webkit-scrollbar-thumb { background: #c7cadb; border-radius: 4px; }

table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  font-size: 13px;
}
thead th {
  text-align: left;
  padding: 10px 10px;
  color: #8a8fa3;
  font-weight: 600;
  font-size: 12px;
  background: #fbfbfd;
  border-bottom: 1px solid #eceef4;
  white-space: nowrap;
}
tbody td {
  padding: 11px 10px;
  border-bottom: 1px solid #f2f3f8;
  color: #333846;
}
tbody tr:last-child td { border-bottom: none; }
.col-num { width: 28px; color: #b0b3c2; }
.question-text { min-width: 220px; }
.col-subject { width: 120px; white-space: nowrap; }
.col-chapter { width: 130px; white-space: nowrap; }
.col-type { width: 64px; white-space: nowrap; }
.col-difficulty { width: 84px; white-space: nowrap; }
.col-marks { width: 55px; white-space: nowrap; }
.col-reason { width: 200px; color: #e0433f; font-size: 12.5px; }
.empty-row { text-align: center; color: #8a8fa3; padding: 24px; }

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}
.badge-type { background: #ede9fe; color: #6c4bf4; }
.badge-easy { background: #e6f9ee; color: #1fa863; }
.badge-medium { background: #fff4e0; color: #d98a1a; }
.badge-hard { background: #fde8e8; color: #e0433f; }
.badge-default { background: #eceef4; color: #6b7086; }

/* Step 3a: import progress */
.import-progress-card {
  border: 1px solid #eceef4;
  border-radius: 12px;
  padding: 24px;
  background: #fbfbfd;
}
.import-progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13.5px;
}
.import-progress-head strong { color: #1f2430; }
.import-progress-head span { color: #6c4bf4; font-weight: 700; }
.progress-bar-track {
  height: 8px;
  border-radius: 999px;
  background: #eceef4;
  overflow: hidden;
  margin-bottom: 20px;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b6bf7, #6c4bf4);
  border-radius: 999px;
  transition: width 0.2s ease;
}

/* Step 3b: success */
.success-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: stretch;
}
.success-card {
  border: 1px solid #eceef4;
  border-radius: 12px;
  padding: 32px 20px;
  text-align: center;
  background: #fbfbfd;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.success-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #22c55e;
  color: #fff;
  font-size: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}
.success-title { font-size: 16px; font-weight: 700; margin: 0 0 6px; color: #1f2430; }
.success-sub { font-size: 13px; color: #8a8fa3; margin: 0; max-width: 260px; }

.success-stats {
  border: 1px solid #eceef4;
  border-radius: 12px;
  padding: 20px;
}
.success-stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 13.5px;
  padding: 10px 0;
  border-bottom: 1px solid #f2f3f8;
  color: #4a4f61;
}
.success-stat-row:last-child { border-bottom: none; }
.success-stat-row strong { color: #1f2430; }

/* Buttons */
.btn {
  border-radius: 8px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn-outline { background: #fff; border-color: #e4e6ef; color: #4a4f61; }
.btn-outline:hover { background: #f6f7fb; }
.btn-primary { background: #6c4bf4; color: #fff; }
.btn-primary:hover { background: #5c3ce0; }
.btn-primary:disabled { background: #cabff8; cursor: not-allowed; }

@media (max-width: 860px) {
  .upload-grid,
  .validate-grid,
  .success-grid {
    grid-template-columns: 1fr;
  }
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>