<template>
  <div class="step-content">
    <h2 class="step-title">1. Select Classification</h2>
    <p class="step-subtitle">Select the appropriate classification for this question.</p>

    <div class="classification-grid">
      <div class="form-group">
        <label class="form-label">Exam <span class="required">*</span></label>
        <select v-model="form.exam" class="form-select" :disabled="loading.exams" @change="onExamChange">
          <option value="" disabled>{{ loading.exams ? 'Loading exams...' : 'Select exam' }}</option>
          <option v-for="exam in examOptions" :key="exam.value" :value="exam.value">
            {{ exam.label }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Subject <span class="required">*</span></label>
        <select
          v-model="form.subject"
          class="form-select"
          :disabled="!form.exam || loading.subjects"
          @change="onSubjectChange"
        >
          <option value="" disabled>{{ loading.subjects ? 'Loading subjects...' : 'Select subject' }}</option>
          <option v-for="subject in subjectOptions" :key="subject.value" :value="subject.value">
            {{ subject.label }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Chapter <span class="required">*</span></label>
        <select
          v-model="form.chapter"
          class="form-select"
          :disabled="!form.subject || loading.chapters"
          @change="emitUpdate"
        >
          <option value="" disabled>{{ loading.chapters ? 'Loading chapters...' : 'Select chapter' }}</option>
          <option v-for="chapter in chapterOptions" :key="chapter.value" :value="chapter.value">
            {{ chapter.label }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Topic <span class="optional">(Optional)</span></label>
        <select v-model="form.topic" class="form-select" @change="emitUpdate">
          <option value="" disabled>Select topic</option>
          <option v-for="topic in topicOptions" :key="topic.value" :value="topic.value">
            {{ topic.label }}
          </option>
        </select>
      </div>
    </div>

    <div class="classification-grid classification-grid--row2">
      <div class="form-group">
        <label class="form-label">Question Type <span class="required">*</span></label>
        <select v-model="form.questionType" class="form-select" @change="emitUpdate">
          <option value="" disabled>Select question type</option>
          <option value="single_correct">Single Correct</option>
          <option value="multiple_correct">Multiple Correct</option>
          <option value="integer">Integer Type</option>
          <option value="subjective">Subjective</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Difficulty Level <span class="required">*</span></label>
        <div class="difficulty-buttons">
          <button
            v-for="level in difficultyLevels"
            :key="level.value"
            :class="['difficulty-btn', `difficulty-btn--${level.value}`, { active: form.difficulty === level.value }]"
            @click="form.difficulty = level.value; emitUpdate()"
            type="button"
          >
            {{ level.label }}
          </button>
        </div>
        <p class="hint-text">Select the difficulty level of this question.</p>
      </div>
    </div>

    <p v-if="loadError" class="error-text">{{ loadError }}</p>

    <!-- PYQ Toggle -->
    <div class="pyq-toggle-row">
      <div>
        <label class="form-label">Is this a Previous Year Question (PYQ)?</label>
        <p class="hint-text">Enable if this question is from any previous year exam.</p>
      </div>
      <div class="toggle-switch">
        <button
          type="button"
          class="toggle-track"
          :class="{ 'toggle-track--on': form.isPyq }"
          @click="form.isPyq = !form.isPyq; emitUpdate()"
          role="switch"
          :aria-checked="form.isPyq"
        >
          <span class="toggle-thumb" :class="{ 'toggle-thumb--on': form.isPyq }" />
        </button>
        <span class="toggle-label" :class="{ 'toggle-label--active': form.isPyq }">Yes</span>
        <span class="toggle-label" :class="{ 'toggle-label--active': !form.isPyq }">No</span>
      </div>
    </div>

    <!-- PYQ Details Panel -->
    <div v-if="form.isPyq" class="pyq-panel">
      <h3 class="pyq-panel-title">Question Source (PYQ Details)</h3>

      <div class="pyq-grid">
        <div class="form-group">
          <label class="form-label">PYQ Exam <span class="required">*</span></label>
          <select v-model="form.pyqExam" class="form-select" @change="emitUpdate">
            <option value="" disabled>Select exam</option>
            <option v-for="exam in examOptions" :key="exam.value" :value="exam.value">
              {{ exam.label }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">PYQ Year <span class="required">*</span></label>
          <select v-model="form.pyqYear" class="form-select" @change="emitUpdate">
            <option value="" disabled>Select year</option>
            <option v-for="year in pyqYearOptions" :key="year" :value="year">{{ year }}</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Session / Shift <span class="optional">(Optional)</span></label>
          <select v-model="form.pyqSession" class="form-select" @change="emitUpdate">
            <option value="" disabled>Select session/shift</option>
            <option value="shift_1">Shift 1</option>
            <option value="shift_2">Shift 2</option>
          </select>
        </div>
      </div>

      <div class="pyq-info-note">
        <span class="pyq-info-icon">ⓘ</span>
        This metadata helps in identifying where this question originally appeared.
      </div>
    </div>

    <div class="step-footer">
      <button class="btn btn--primary" @click="handleNext" :disabled="!isValid">
        Next Step <span class="arrow">→</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { fetchExams, fetchSubjects, fetchChapters } from '@/services/questionAdminApi'

const emit = defineEmits(['next', 'update:modelValue'])

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const form = reactive({
  exam: '',
  subject: '',
  chapter: '',
  topic: '',
  questionType: 'single_correct',
  difficulty: '',
  // Human-readable labels are carried alongside the ids so later steps
  // (Quick Summary on step 4) don't need to re-fetch anything just to
  // show "JEE Main / Physics / Current Electricity".
  examLabel: '',
  subjectLabel: '',
  chapterLabel: '',
  // PYQ (Previous Year Question) source metadata
  isPyq: false,
  pyqExam: '',
  pyqYear: '',
  pyqSession: '',
  ...props.modelValue
})

const examOptions = ref([])
const subjectOptions = ref([])
const chapterOptions = ref([])

// NOTE: no Topic model/endpoint exists on the backend yet, so this stays
// static and is never sent to the server (see AddQuestion.vue's payload).
const topicOptions = [
  { value: 'ohms_law', label: "Ohm's Law" },
  { value: 'kirchhoffs_laws', label: "Kirchhoff's Laws" },
  { value: 'capacitors', label: 'Capacitors' }
]

const currentYear = new Date().getFullYear()
const pyqYearOptions = Array.from({ length: currentYear - 1999 }, (_, i) => currentYear - i)

const difficultyLevels = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' }
]

const loading = reactive({ exams: false, subjects: false, chapters: false })
const loadError = ref('')

const isValid = computed(() => {
  const baseValid = form.exam && form.subject && form.chapter && form.questionType && form.difficulty
  if (!form.isPyq) return baseValid
  return baseValid && form.pyqExam && form.pyqYear
})

function emitUpdate() {
  emit('update:modelValue', { ...form })
}

function handleNext() {
  emitUpdate()
  emit('next')
}

async function loadExams() {
  loading.exams = true
  loadError.value = ''
  try {
    const exams = await fetchExams()
    examOptions.value = exams.map(e => ({ value: e.exam_id, label: e.exam_name }))
  } catch (err) {
    loadError.value = 'Could not load exams. Check your connection and try again.'
    console.error('fetchExams failed:', err)
  } finally {
    loading.exams = false
  }
}

async function loadSubjects(examId, { preserveSelection = false } = {}) {
  if (!preserveSelection) {
    form.subject = ''
    form.chapter = ''
    subjectOptions.value = []
    chapterOptions.value = []
  }
  if (!examId) return

  loading.subjects = true
  loadError.value = ''
  try {
    const subjects = await fetchSubjects(examId)
    subjectOptions.value = subjects.map(s => ({ value: s.subject_id, label: s.subject_name }))
  } catch (err) {
    loadError.value = 'Could not load subjects for this exam.'
    console.error('fetchSubjects failed:', err)
  } finally {
    loading.subjects = false
  }
}

async function loadChapters(subjectId, { preserveSelection = false } = {}) {
  if (!preserveSelection) {
    form.chapter = ''
    chapterOptions.value = []
  }
  if (!subjectId) return

  loading.chapters = true
  loadError.value = ''
  try {
    const chapters = await fetchChapters(subjectId)
    chapterOptions.value = chapters.map(c => ({ value: c.chapter_id, label: c.chapter_name }))
  } catch (err) {
    loadError.value = 'Could not load chapters for this subject.'
    console.error('fetchChapters failed:', err)
  } finally {
    loading.chapters = false
  }
}

function onExamChange() {
  form.examLabel = examOptions.value.find(e => e.value === form.exam)?.label || ''
  loadSubjects(form.exam)
  emitUpdate()
}

function onSubjectChange() {
  form.subjectLabel = subjectOptions.value.find(s => s.value === form.subject)?.label || ''
  loadChapters(form.subject)
  emitUpdate()
}

onMounted(async () => {
  await loadExams()
  // Re-hydrate cascading dropdowns when coming back to step 1 with
  // values already picked (e.g. user clicked "Previous Step").
  if (form.exam) await loadSubjects(form.exam, { preserveSelection: true })
  if (form.subject) await loadChapters(form.subject, { preserveSelection: true })
})
</script>

<style scoped>
.step-content {
  padding: 0;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  color: #4f46e5;
  margin: 0 0 4px;
}

.step-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 28px;
}

.classification-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px 24px;
  margin-bottom: 22px;
}

.classification-grid--row2 {
  grid-template-columns: 1fr 1fr;
  margin-bottom: 0;
}

@media (max-width: 900px) {
  .classification-grid,
  .classification-grid--row2,
  .pyq-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 560px) {
  .classification-grid,
  .classification-grid--row2,
  .pyq-grid {
    grid-template-columns: 1fr;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #ef4444;
}

.optional {
  color: #9ca3af;
  font-weight: 400;
}

.form-select {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E") no-repeat right 12px center;
  appearance: none;
  cursor: pointer;
  transition: border-color 0.15s;
}

.form-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.form-select:disabled {
  background-color: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.difficulty-buttons {
  display: flex;
  gap: 10px;
}

.difficulty-btn {
  flex: 1;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  border: 1.5px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.difficulty-btn--easy {
  color: #16a34a;
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.difficulty-btn--easy.active {
  background: #dcfce7;
  border-color: #16a34a;
}

.difficulty-btn--medium {
  color: #d97706;
  background: #fffbeb;
  border-color: #fde68a;
}
.difficulty-btn--medium.active {
  background: #fef3c7;
  border-color: #d97706;
}

.difficulty-btn--hard {
  color: #dc2626;
  background: #fef2f2;
  border-color: #fecaca;
}
.difficulty-btn--hard.active {
  background: #fee2e2;
  border-color: #dc2626;
}

.hint-text {
  font-size: 12px;
  color: #9ca3af;
  margin: 4px 0 0;
}

.hint-text--muted {
  font-style: italic;
}

.error-text {
  font-size: 13px;
  color: #dc2626;
  margin: 4px 0 0;
}

/* PYQ Toggle Row */
.pyq-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.toggle-track {
  position: relative;
  width: 44px;
  height: 24px;
  border-radius: 999px;
  border: none;
  background: #d1d5db;
  cursor: pointer;
  padding: 0;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-track--on {
  background: #4f46e5;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s;
}

.toggle-thumb--on {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 13px;
  font-weight: 500;
  color: #9ca3af;
}

.toggle-label--active {
  color: #4f46e5;
}

/* PYQ Details Panel */
.pyq-panel {
  margin-top: 16px;
  padding: 20px 24px;
  background: #f5f3ff;
  border: 1px solid #e0e7ff;
  border-radius: 10px;
}

.pyq-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #4f46e5;
  margin: 0 0 18px;
}

.pyq-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px 24px;
}

.pyq-panel .form-select {
  background-color: #fff;
}

.pyq-info-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 18px;
  padding: 10px 14px;
  background: #eef2ff;
  border-radius: 8px;
  font-size: 12.5px;
  color: #4338ca;
}

.pyq-info-icon {
  font-size: 14px;
  line-height: 1.4;
  flex-shrink: 0;
}

.step-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 32px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--primary {
  background: #4f46e5;
  color: #fff;
}

.btn--primary:hover:not(:disabled) {
  background: #4338ca;
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.arrow {
  font-size: 16px;
}
</style>