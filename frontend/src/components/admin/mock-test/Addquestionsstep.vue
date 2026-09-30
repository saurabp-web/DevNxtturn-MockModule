<template>
  <div class="page">
    <!-- Breadcrumb -->
    <div class="breadcrumb">Mock Test / Create Mock Test</div>

    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Create Mock Test</h1>
        <p class="page-subtitle">Add questions to your mock test manually or in bulk.</p>
      </div>
      <button class="btn btn-outline" @click="$emit('back')">
        <span class="arrow">←</span> Back to Mock Tests
      </button>
    </div>

    <!-- Stepper -->
    <div class="stepper">
      <template v-for="(step, idx) in steps" :key="step.key">
        <div class="step" :class="stepStatus(idx)">
          <div class="step-circle">
            <span v-if="idx < currentStep">✓</span>
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <div class="step-text">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-desc">{{ step.desc }}</div>
          </div>
        </div>
        <div v-if="idx < steps.length - 1" class="step-connector" :class="{ done: idx < currentStep }"></div>
      </template>
    </div>

    <!-- Main card -->
    <div class="card">
      <div class="card-header">
        <h2>Add Questions to Mock Test</h2>
        <p>Add questions manually from question bank or upload in bulk. These questions will be exclusive to this mock test.</p>
      </div>

      <!-- Mode tabs -->
      <div class="mode-tabs">
        <button
          class="mode-tab"
          :class="{ active: mode === 'bank' }"
          @click="mode = 'bank'"
        >
          <span class="mode-icon">🔍</span>
          <span class="mode-text">
            <strong>Add from Question Bank</strong>
            <small>Search and add questions one by one or in bulk</small>
          </span>
        </button>
        <button
          class="mode-tab"
          :class="{ active: mode === 'upload' }"
          @click="mode = 'upload'"
        >
          <span class="mode-icon">⬆</span>
          <span class="mode-text">
            <strong>Bulk Upload Questions</strong>
            <small>Upload questions in bulk using Excel file</small>
          </span>
        </button>
      </div>

      <div v-if="mode === 'bank'" class="bank-mode">
        <!-- Search + filters -->
        <div class="toolbar">
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input v-model="searchQuery" type="text" placeholder="Search questions by keyword, question ID..." />
          </div>

          <select v-model="filters.subject" class="filter-select">
            <option value="">All Subjects</option>
            <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
          </select>

          <select v-model="filters.chapter" class="filter-select">
            <option value="">All Chapters</option>
            <option v-for="c in chapterOptions" :key="c" :value="c">{{ c }}</option>
          </select>

          <select v-model="filters.type" class="filter-select">
            <option value="">All Types</option>
            <option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
          </select>

          <select v-model="filters.difficulty" class="filter-select">
            <option value="">All Difficulty</option>
            <option v-for="d in difficultyOptions" :key="d" :value="d">{{ d }}</option>
          </select>

          <button class="btn btn-outline filters-btn">
            <span>▤</span> Filters
          </button>
        </div>

        <div class="content-grid">
          <!-- Question table -->
          <div class="table-panel">
            <div class="table-panel-header">
              <div>
                <strong>Question Bank ({{ totalQuestionsFound }} questions found)</strong>
                <p>Select questions to add to this mock test</p>
              </div>
            </div>

            <p v-if="loadError" class="error-banner">{{ loadError }}</p>

            <div v-if="loadingQuestions" class="loading-row">Loading question bank…</div>
            <div v-else class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th class="col-check">
                      <input type="checkbox" :checked="allVisibleSelected" @change="toggleSelectAllVisible" />
                    </th>
                    <th class="col-num">#</th>
                    <th class="col-question">Question</th>
                    <th class="col-subject">Subject</th>
                    <th class="col-chapter">Chapter</th>
                    <th class="col-type">Type</th>
                    <th class="col-difficulty">Difficulty</th>
                    <th class="col-marks">Marks</th>
                    <th class="col-actions">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(q, idx) in filteredQuestions" :key="q.id">
                    <td class="col-check">
                      <input type="checkbox" v-model="q.selected" @change="onToggleQuestion(q)" />
                    </td>
                    <td class="col-num">{{ idx + 1 }}</td>
                    <td class="col-question">
                      <div class="question-text">{{ q.text }}</div>
                      <div class="question-id">ID: {{ q.questionId }}</div>
                    </td>
                    <td class="col-subject">{{ q.subject }}</td>
                    <td class="col-chapter">{{ q.chapter }}</td>
                    <td class="col-type"><span class="badge badge-type">{{ q.type }}</span></td>
                    <td class="col-difficulty">
                      <span class="badge" :class="difficultyClass(q.difficulty)">{{ q.difficulty }}</span>
                    </td>
                    <td class="col-marks">{{ q.marks }}</td>
                    <td class="col-actions">
                      <button class="btn-add" :class="{ added: q.selected }" @click="toggleQuestion(q)">
                        <span>{{ q.selected ? '✓' : '+' }}</span> {{ q.selected ? 'Added' : 'Add' }}
                      </button>
                    </td>
                  </tr>
                  <tr v-if="filteredQuestions.length === 0">
                    <td colspan="9" class="empty-row">No questions match the current filters.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Selected summary sidebar -->
          <aside class="summary-panel">
            <h3>Selected Questions Summary</h3>

            <div class="summary-row">
              <span>Total Questions</span>
              <strong>{{ selectedQuestions.length }}</strong>
            </div>
            <div class="summary-row">
              <span>Total Marks</span>
              <strong>{{ totalMarks }}</strong>
            </div>
            <div class="summary-row">
              <span>Subjects</span>
              <strong>{{ subjectBreakdown.length }}</strong>
            </div>
            <div class="summary-row">
              <span>Chapters</span>
              <strong>{{ chapterCount }}</strong>
            </div>

            <h4>Subject Wise Breakup</h4>
            <div v-if="subjectBreakdown.length" class="breakdown-list">
              <div class="breakdown-row" v-for="s in subjectBreakdown" :key="s.name">
                <span>{{ s.name }}</span>
                <strong>{{ s.count }}</strong>
              </div>
            </div>
            <p v-else class="empty-hint">No questions selected yet.</p>

            <button class="btn btn-danger-outline" :disabled="!selectedQuestions.length" @click="clearAll">
              Clear All
            </button>
          </aside>
        </div>
      </div>

      <!-- Bulk upload mode -->
      <div v-else class="upload-mode-wrap">
        <p v-if="!mockexamId" class="draft-warning">
          ⚠ This mock test hasn't been saved yet. Bulk upload needs a saved mock test to attach
          questions to — please make sure Basic Details and Select Exam are completed before
          uploading a file.
        </p>
        <BulkUploadCompleted
          v-if="bulkStage === 'completed'"
          :imported-count="bulkImportedCount"
          @review-questions="onReviewImportedQuestions"
          @next-step="$emit('next-step', selectedQuestions)"
        />
        <BulkUploadQuestions
          v-else
          :mockexam-id="mockexamId"
          @cancel="mode = 'bank'"
          @download-template="$emit('download-template')"
          @back-to-add-questions="mode = 'bank'"
          @done="onBulkUploadDone"
        />
      </div>
    </div>

    <!-- Footer nav (hidden while the bulk-upload sub-flow has its own footer) -->
    <div class="footer-nav" v-if="mode === 'bank' || bulkStage === 'completed'">
      <button class="btn btn-outline" @click="$emit('previous-step')">← Previous Step</button>
      <div class="footer-actions">
        <button class="btn btn-outline" @click="$emit('save-exit')">Save & Exit</button>
        <button class="btn btn-primary" :disabled="!selectedQuestions.length" @click="$emit('next-step', selectedQuestions)">
          Next Step →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import BulkUploadQuestions from './BulkUploadQuestions.vue'
import BulkUploadCompleted from './BulkUploadCompleted.vue'
import { fetchQuestionBank, addQuestionsToMockExam, fetchMockExamQuestions } from '@/services/mockTestApi'

const props = defineProps({
  questionBank: {
    type: Array,
    default: () => []
  },
  mockexamId: {
    type: [Number, String],
    default: null
  },
  examId: {
    type: [Number, String],
    default: null
  }
})

defineEmits(['back', 'previous-step', 'save-exit', 'next-step', 'download-template'])

const bulkStage = ref('form') // 'form' | 'completed'
const bulkImportedCount = ref(0)

function onBulkUploadDone({ imported }) {
  bulkImportedCount.value = imported
  bulkStage.value = 'completed'
  // Refresh the question bank / selection so newly-imported questions show
  // up immediately if the user switches back to "Add from Question Bank".
  loadQuestionBank()
}

function onReviewImportedQuestions() {
  mode.value = 'bank'
  bulkStage.value = 'form'
}

const currentStep = 3 // 0-indexed: "Add Questions" is step 4

const steps = [
  { key: 'basic', title: 'Basic Details', desc: 'Add mock test basic information' },
  { key: 'exam', title: 'Select Exam', desc: 'Choose exam and year' },
  { key: 'pattern', title: 'Set Pattern', desc: 'Configure pattern & subjects' },
  { key: 'questions', title: 'Add Questions', desc: 'Add or upload questions' },
  { key: 'review', title: 'Review & Confirm', desc: 'Review and create mock test' }
]

function stepStatus(idx) {
  if (idx < currentStep) return 'done'
  if (idx === currentStep) return 'active'
  return 'upcoming'
}

const mode = ref('bank')
const searchQuery = ref('')
const filters = reactive({
  subject: '',
  chapter: '',
  type: '',
  difficulty: ''
})

const defaultQuestions = [
  { id: 1, questionId: 'Q12345', text: 'If a = 2 + √3 and b = 2 − √3, then the value of a² + b² is:', subject: 'Mathematics', chapter: 'Quadratic Equations', type: 'MCQ', difficulty: 'Medium', marks: 4, selected: true },
  { id: 2, questionId: 'Q12346', text: 'The unit of electric potential is:', subject: 'Physics', chapter: 'Electrostatics', type: 'MCQ', difficulty: 'Easy', marks: 4, selected: false },
  { id: 3, questionId: 'Q12347', text: 'Photosynthesis in plants mainly occurs in:', subject: 'Biology', chapter: 'Plant Physiology', type: 'MCQ', difficulty: 'Easy', marks: 4, selected: false },
  { id: 4, questionId: 'Q12348', text: 'The capital of France is:', subject: 'General Knowledge', chapter: 'World Geography', type: 'MCQ', difficulty: 'Easy', marks: 2, selected: true },
  { id: 5, questionId: 'Q12349', text: 'Who wrote the National Anthem of India?', subject: 'General Knowledge', chapter: 'Indian Polity', type: 'MCQ', difficulty: 'Medium', marks: 2, selected: false },
  { id: 6, questionId: 'Q12350', text: 'The chemical formula of water is:', subject: 'Chemistry', chapter: 'Basic Chemistry', type: 'MCQ', difficulty: 'Easy', marks: 4, selected: false }
]

const questions = reactive(
  (props.questionBank.length ? props.questionBank : defaultQuestions).map(q => ({ ...q }))
)

const totalQuestionsFound = ref(questions.length)
const loadingQuestions = ref(false)
const loadError = ref('')

/**
 * Pulls the live question bank scoped to the selected exam. Runs on mount
 * and again whenever examId changes (e.g. user goes back and picks a
 * different exam in SelectExamStep). If no examId is available yet, keeps
 * whatever was passed in via the questionBank prop / sample fallback.
 */
async function loadQuestionBank() {
  if (!props.examId) return
  loadingQuestions.value = true
  loadError.value = ''
  try {
    const items = await fetchQuestionBank({ exam_id: props.examId, page_size: 200 })
    questions.splice(0, questions.length, ...items)
    totalQuestionsFound.value = items.length
    applyExistingSelection()
  } catch (err) {
    loadError.value = 'Could not load the question bank. Please try again.'
  } finally {
    loadingQuestions.value = false
  }
}

onMounted(loadQuestionBank)
watch(() => props.examId, loadQuestionBank)

// ── Edit mode: pre-select questions already attached to this mock test ──
// Editing a mock test loads this step with mockexamId already set, but
// the question bank fetch above always starts every row as
// selected:false. Without this, previously-added questions silently
// look unselected and would be dropped from the mock test on save.
const existingSelectedIds = ref(new Set())

function applyExistingSelection() {
  if (!existingSelectedIds.value.size) return
  questions.forEach((q) => {
    if (existingSelectedIds.value.has(q.id)) q.selected = true
  })
}

async function loadExistingSelection() {
  if (!props.mockexamId) return
  try {
    const { results } = await fetchMockExamQuestions(props.mockexamId)
    existingSelectedIds.value = new Set(results.map((q) => q.id))
    applyExistingSelection()
  } catch {
    // Non-fatal — selection just starts empty if this fails.
  }
}

onMounted(loadExistingSelection)
watch(() => props.mockexamId, loadExistingSelection)

const subjectOptions = computed(() => [...new Set(questions.map(q => q.subject))])
const chapterOptions = computed(() => [...new Set(questions.map(q => q.chapter))])
const typeOptions = computed(() => [...new Set(questions.map(q => q.type))])
const difficultyOptions = computed(() => [...new Set(questions.map(q => q.difficulty))])

const filteredQuestions = computed(() => {
  return questions.filter(q => {
    if (filters.subject && q.subject !== filters.subject) return false
    if (filters.chapter && q.chapter !== filters.chapter) return false
    if (filters.type && q.type !== filters.type) return false
    if (filters.difficulty && q.difficulty !== filters.difficulty) return false
    if (searchQuery.value) {
      const needle = searchQuery.value.toLowerCase()
      const haystack = `${q.text} ${q.questionId}`.toLowerCase()
      if (!haystack.includes(needle)) return false
    }
    return true
  })
})

const selectedQuestions = computed(() => questions.filter(q => q.selected))
const totalMarks = computed(() => selectedQuestions.value.reduce((sum, q) => sum + Number(q.marks || 0), 0))

const subjectBreakdown = computed(() => {
  const map = new Map()
  selectedQuestions.value.forEach(q => {
    map.set(q.subject, (map.get(q.subject) || 0) + 1)
  })
  return [...map.entries()].map(([name, count]) => ({ name, count }))
})

const chapterCount = computed(() => new Set(selectedQuestions.value.map(q => q.chapter)).size)

const allVisibleSelected = computed(() =>
  filteredQuestions.value.length > 0 && filteredQuestions.value.every(q => q.selected)
)

function toggleSelectAllVisible() {
  const shouldSelect = !allVisibleSelected.value
  filteredQuestions.value.forEach(q => {
    q.selected = shouldSelect
  })
}

function toggleQuestion(q) {
  q.selected = !q.selected
}

function onToggleQuestion() {
  // hook for future side-effects (e.g. analytics) when a row checkbox changes
}

function clearAll() {
  questions.forEach(q => (q.selected = false))
}

function difficultyClass(level) {
  const map = {
    Easy: 'badge-easy',
    Medium: 'badge-medium',
    Hard: 'badge-hard'
  }
  return map[level] || 'badge-default'
}

const fileInput = ref(null)
</script>

<style scoped>
.page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: #f6f7fb;
  padding: 24px 32px;
  color: #1f2430;
}

.breadcrumb {
  font-size: 13px;
  color: #8a8fa3;
  margin-bottom: 8px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  color: #14161f;
}

.page-subtitle {
  font-size: 14px;
  color: #7a7f92;
  margin: 0;
}

.arrow {
  margin-right: 4px;
}

/* Stepper */
.stepper {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  border: 1px solid #eceef4;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.step-circle {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  background: #eceef4;
  color: #8a8fa3;
}

.step.done .step-circle {
  background: #22c55e;
  color: #fff;
}

.step.active .step-circle {
  background: #6c4bf4;
  color: #fff;
}

.step-title {
  font-size: 13px;
  font-weight: 700;
  color: #b0b3c2;
  white-space: nowrap;
}

.step.done .step-title,
.step.active .step-title {
  color: #1f2430;
}

.step-desc {
  font-size: 11px;
  color: #b0b3c2;
  white-space: nowrap;
}

.step-connector {
  flex: 1;
  height: 2px;
  background: #eceef4;
  margin: 0 16px;
  min-width: 24px;
}

.step-connector.done {
  background: #22c55e;
}

/* Card */
.card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #eceef4;
  padding: 24px;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 17px;
  margin: 0 0 4px;
  color: #14161f;
}

.card-header p {
  font-size: 13px;
  color: #8a8fa3;
  margin: 0 0 20px;
}

/* Mode tabs */
.mode-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1.5px solid #eceef4;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}

.mode-tab.active {
  border-color: #6c4bf4;
  background: #f5f2ff;
}

.mode-icon {
  font-size: 18px;
  color: #6c4bf4;
}

.mode-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mode-text strong {
  font-size: 14px;
  color: #1f2430;
}

.mode-text small {
  font-size: 12px;
  color: #8a8fa3;
}

/* Toolbar */
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 220px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e4e6ef;
  border-radius: 8px;
  padding: 8px 12px;
  background: #fbfbfd;
}

.search-box input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  width: 100%;
}

.filter-select {
  border: 1px solid #e4e6ef;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  background: #fff;
  color: #4a4f61;
  min-width: 120px;
}

.filters-btn {
  white-space: nowrap;
}

/* Layout grid */
.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

.table-panel {
  border: 1px solid #eceef4;
  border-radius: 10px;
  overflow: hidden;
  min-width: 0;
}

.table-panel-header {
  padding: 14px 16px;
  border-bottom: 1px solid #eceef4;
}

.table-panel-header strong {
  font-size: 14px;
  color: #1f2430;
}

.table-panel-header p {
  margin: 2px 0 0;
  font-size: 12px;
  color: #8a8fa3;
}

.table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #c7cadb #f2f3f8;
}

.table-wrap::-webkit-scrollbar {
  height: 8px;
}

.table-wrap::-webkit-scrollbar-track {
  background: #f2f3f8;
}

.table-wrap::-webkit-scrollbar-thumb {
  background: #c7cadb;
  border-radius: 4px;
}

.table-wrap::-webkit-scrollbar-thumb:hover {
  background: #a9adc4;
}

table {
  width: 100%;
  min-width: 700px;
  border-collapse: collapse;
  font-size: 13px;
  table-layout: auto;
}

thead th {
  text-align: left;
  padding: 10px 8px;
  color: #8a8fa3;
  font-weight: 600;
  font-size: 12px;
  border-bottom: 1px solid #eceef4;
  white-space: nowrap;
}

tbody td {
  padding: 12px 8px;
  border-bottom: 1px solid #f2f3f8;
  vertical-align: middle;
  color: #333846;
}

tbody tr:last-child td {
  border-bottom: none;
}

.col-check {
  width: 32px;
}

.col-num {
  width: 28px;
  color: #b0b3c2;
}

.col-question {
  width: auto;
}

.question-text {
  font-weight: 500;
  color: #1f2430;
  white-space: normal;
  word-break: break-word;
}

.question-id {
  font-size: 11px;
  color: #b0b3c2;
  margin-top: 2px;
}

.col-subject,
.col-chapter,
.col-type,
.col-difficulty,
.col-marks,
.col-actions {
  white-space: nowrap;
}

.col-subject {
  width: 100px;
}

.col-chapter {
  width: 110px;
}

.col-type {
  width: 64px;
}

.col-difficulty {
  width: 80px;
}

.col-marks {
  width: 55px;
}

.col-actions {
  width: 80px;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.badge-type {
  background: #ede9fe;
  color: #6c4bf4;
}

.badge-easy {
  background: #e6f9ee;
  color: #1fa863;
}

.badge-medium {
  background: #fff4e0;
  color: #d98a1a;
}

.badge-hard {
  background: #fde8e8;
  color: #e0433f;
}

.badge-default {
  background: #eceef4;
  color: #6b7086;
}

.btn-add {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid #d7ccff;
  color: #6c4bf4;
  background: #fff;
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-add.added {
  background: #6c4bf4;
  color: #fff;
  border-color: #6c4bf4;
}

.empty-row {
  text-align: center;
  color: #8a8fa3;
  padding: 24px;
}

.loading-row {
  text-align: center;
  color: #8a8fa3;
  padding: 40px;
  font-size: 13px;
}

.error-banner {
  background: #fde8e8;
  color: #c0322f;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin: 0 16px 12px;
}

/* Summary panel */
.summary-panel {
  border: 1px solid #eceef4;
  border-radius: 10px;
  padding: 18px;
  background: #fbfbfd;
  min-width: 0;
}

.summary-panel h3 {
  font-size: 14px;
  margin: 0 0 12px;
  color: #1f2430;
}

.summary-panel h4 {
  font-size: 12px;
  color: #8a8fa3;
  margin: 16px 0 8px;
  text-transform: none;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 6px 0;
  color: #4a4f61;
}

.summary-row strong {
  color: #1f2430;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
  color: #6b7086;
  padding: 4px 0;
}

.empty-hint {
  font-size: 12px;
  color: #b0b3c2;
}

.btn-danger-outline {
  width: 100%;
  margin-top: 16px;
  padding: 9px 0;
  border-radius: 8px;
  border: 1px solid #f3c6c6;
  background: #fff;
  color: #e0433f;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-danger-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Bulk upload sub-flow wrapper */
.upload-mode-wrap {
  padding: 4px 0 0;
}

.draft-warning {
  background: #fff4e0;
  color: #a86710;
  border: 1px solid #f3dfb0;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin: 0 0 16px;
}

/* Buttons */
.btn {
  border-radius: 8px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-outline {
  background: #fff;
  border-color: #e4e6ef;
  color: #4a4f61;
}

.btn-outline:hover {
  background: #f6f7fb;
}

.btn-primary {
  background: #6c4bf4;
  color: #fff;
}

.btn-primary:hover {
  background: #5c3ce0;
}

.btn-primary:disabled {
  background: #cabff8;
  cursor: not-allowed;
}

/* Footer */
.footer-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .summary-panel {
    order: 2;
  }
}
</style>