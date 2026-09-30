<template>
  <div class="wizard-page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Add New Subject</h1>
        <p class="page-sub">{{ step === 1 ? 'Create a new subject and associate it with an exam.' : 'Review the subject details before creating.' }}</p>
      </div>
      <div class="breadcrumb">
        <span>Home</span>
        <span class="crumb-sep">›</span>
        <span>Subjects</span>
        <span class="crumb-sep">›</span>
        <span :class="{ 'crumb-current': step === 1 }">Add Subject</span>
        <template v-if="step === 2">
          <span class="crumb-sep">›</span>
          <span class="crumb-current">Review & Confirm</span>
        </template>
      </div>
    </div>

    <!-- Stepper -->
    <div class="stepper-card">
      <div class="stepper">
        <div class="step" :class="{ active: step === 1, done: step > 1 }">
          <span class="step-badge">
            <Check v-if="step > 1" :size="14" />
            <template v-else>1</template>
          </span>
          <span class="step-label">Subject Details</span>
        </div>
        <div class="step-line" :class="{ filled: step > 1 }" />
        <div class="step" :class="{ active: step === 2 }">
          <span class="step-badge">2</span>
          <span class="step-label">Review & Confirm</span>
        </div>
      </div>
    </div>

    <!-- Toast notifications -->
    <transition name="toast">
      <div v-if="successMsg" class="toast toast-success">✓ {{ successMsg }}</div>
    </transition>
    <transition name="toast">
      <div v-if="saveError" class="toast toast-error">⚠ {{ saveError }}</div>
    </transition>

    <!-- Step content -->
    <p v-if="loadingExams" class="exam-load-status">Loading exams…</p>
    <p v-else-if="examLoadError" class="exam-load-status error">⚠ {{ examLoadError }}</p>
    <StepSubjectDetails
      v-if="step === 1"
      v-model="form"
      :exam-options="resolvedExamOptions"
      @cancel="$emit('cancel')"
      @continue="goToReview"
      @save-and-add-another="saveAndAddAnother"
    />
    <StepReviewConfirm
      v-else-if="step === 2"
      :form="form"
      :exam-options="resolvedExamOptions"
      :saving="saving"
      @back="step = 1"
      @save-draft="save('draft')"
      @save="save('active')"
    />
    <!-- Inline error shown below review panel as fallback -->
    <p v-if="saveError && step === 2" class="exam-load-status error" style="margin-top:12px">⚠ {{ saveError }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { Check } from 'lucide-vue-next'
import StepSubjectDetails from './StepSubjectDetails.vue'
import StepReviewConfirm from './StepReviewConfirm.vue'

export interface SubjectForm {
  examId: string | number | null
  subjectName: string
  subjectCode: string
  active: boolean
}

export interface ExamOption {
  id: string | number
  name: string
  code: string
}

// CHANGED: withDefaults(defineProps<{...}>(), {...}) was compiling in
// this project such that examOptions still resolved to `undefined` at
// runtime instead of `[]` — same root cause found in
// SubjectsListView.vue ("Missing required prop" + crash on `.length`).
// Runtime prop declarations with an explicit `default` always apply
// regardless of that macro/compiler quirk.
const props = defineProps({
  examOptions: {
    type: Array as PropType<ExamOption[]>,
    default: () => [],
  },
})

const router = useRouter()

const fetchedExamOptions = ref<ExamOption[]>([])
const loadingExams = ref(false)
const examLoadError = ref('')
const saving = ref(false)
const saveError = ref('')
const successMsg = ref('')

function showSuccess(msg: string) {
  successMsg.value = msg
  setTimeout(() => { successMsg.value = '' }, 3500)
}
function showError(msg: string) {
  saveError.value = msg
  setTimeout(() => { saveError.value = '' }, 4000)
}

// Use whatever the parent passed in if it did; otherwise fall back to
// what this component fetched for itself from /api/exams/.
const resolvedExamOptions = computed(() => {
  const passed = props.examOptions ?? []
  return passed.length ? passed : fetchedExamOptions.value
})

async function loadExamsIfNeeded() {
  if ((props.examOptions ?? []).length) return   // parent already supplied them
  loadingExams.value = true
  try {
    const res = await fetch('/api/exams/')
    if (!res.ok) throw new Error(`Failed to load exams (${res.status})`)
    const json = await res.json()
    const list = Array.isArray(json) ? json : (json.results ?? json.exams ?? [])
    fetchedExamOptions.value = list.map((e: any) => ({
      id: e.exam_id,
      name: e.exam_name,
      code: e.exam_code ?? '',
    }))
  } catch (err: any) {
    examLoadError.value = err.message || 'Could not load exams.'
  } finally {
    loadingExams.value = false
  }
}

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'save', payload: { form: SubjectForm; status: 'draft' | 'active' }): void
  (e: 'save-and-add-another', payload: { form: SubjectForm }): void
}>()

const step = ref<1 | 2>(1)

const form = ref<SubjectForm>({
  examId: null,
  subjectName: '',
  subjectCode: '',
  active: true,
})

function goToReview() {
  step.value = 2
}

async function save(status: 'draft' | 'active') {
  saving.value = true
  saveError.value = ''
  try {
    const payload = {
      exam_id: form.value.examId,
      subject_name: form.value.subjectName,
    }
    const res = await fetch('/api/subjects/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || `Server error ${res.status}`)
    }
    const data = await res.json()
    emit('save', { form: form.value, status, result: data })
    showSuccess(`Subject "${data.subject_name}" saved successfully!`)
    setTimeout(() => router.push('/syllabus/subjects'), 1500)
  } catch (e: any) {
    showError(e.message || 'Failed to save subject. Please try again.')
  } finally {
    saving.value = false
  }
}

async function saveAndAddAnother() {
  saving.value = true
  saveError.value = ''
  try {
    const res = await fetch('/api/subjects/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exam_id: form.value.examId,
        subject_name: form.value.subjectName,
      }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.error || `Server error ${res.status}`)
    }
    const data = await res.json()
    emit('save-and-add-another', { form: form.value, result: data })
    showSuccess(`Subject "${data.subject_name}" saved! Add another below.`)
    form.value = { examId: form.value.examId, subjectName: '', subjectCode: '', active: true }
    step.value = 1
  } catch (e: any) {
    showError(e.message || 'Failed to save subject. Please try again.')
  } finally {
    saving.value = false
  }
}

onMounted(loadExamsIfNeeded)
</script>

<style scoped>
.wizard-page {
  padding: 28px 32px;
  background: #F9FAFB;
  min-height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #111827;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 22px;
}
.page-title { font-size: 26px; font-weight: 800; margin: 0; }
.page-sub { font-size: 13px; color: #6B7280; margin: 4px 0 0; }
.breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #9CA3AF; margin-top: 6px; }
.crumb-sep { color: #D1D5DB; }
.crumb-current { color: #7C3AED; font-weight: 600; }

.stepper-card {
  background: #fff;
  border: 1px solid #F0F0F2;
  border-radius: 14px;
  padding: 20px 28px;
  margin-bottom: 20px;
}
.stepper { display: flex; align-items: center; justify-content: center; }
.step { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.step-badge {
  width: 28px; height: 28px; border-radius: 50%;
  background: #F3F4F6; color: #9CA3AF;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.step.active .step-badge { background: #7C3AED; color: #fff; }
.step.done .step-badge { background: #7C3AED; color: #fff; }
.step-label { font-size: 13.5px; font-weight: 600; color: #9CA3AF; white-space: nowrap; }
.step.active .step-label, .step.done .step-label { color: #111827; }
.step-line { flex: 0 1 220px; height: 2px; background: #E5E7EB; margin: 0 16px; }
.step-line.filled { background: #7C3AED; }

.toast {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  padding: 14px 20px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  max-width: 360px;
}
.toast-success { background: #ECFDF5; color: #065F46; border: 1px solid #6EE7B7; }
.toast-error   { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(40px); }

.exam-load-status {
  font-size: 12.5px; color: #6B7280; margin: 0 0 14px;
  background: #fff; border: 1px solid #F0F0F2; border-radius: 10px;
  padding: 10px 14px;
}
.exam-load-status.error { color: #DC2626; background: #FEF2F2; border-color: #FECACA; }
</style>