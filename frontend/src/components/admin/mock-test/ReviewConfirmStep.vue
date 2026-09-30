<template>
  <section class="card">
    <header class="card-head">
      <span class="card-icon">✔️</span>
      <h3>Review &amp; Confirm</h3>
    </header>

    <div class="review-grid">
      <div class="panel">
        <p class="sub-title">Review Information</p>

        <p class="block-title">Basic Details</p>
        <dl>
          <div><dt>Mock Test Name</dt><dd>{{ basic?.name || '—' }}</dd></div>
          <div><dt>Year</dt><dd>{{ basic?.year || '—' }}</dd></div>
          <div><dt>Description</dt><dd>{{ basic?.description || '—' }}</dd></div>
          <div><dt>Total Marks</dt><dd>{{ basic?.totalMarks || '—' }}</dd></div>
          <div><dt>Duration</dt><dd>{{ basic?.duration ? `${basic.duration} Minutes` : '—' }}</dd></div>
          <div><dt>Status</dt><dd><span class="status-pill" :class="{ inactive: !basic?.active }">{{ basic?.active ? 'Active' : 'Inactive' }}</span></dd></div>
        </dl>

        <p class="block-title">Selected Exam</p>
        <dl>
          <div><dt>Exam Type</dt><dd>{{ examTypeName || '—' }}</dd></div>
          <div><dt>Exam Category</dt><dd>{{ examCategoryName || '—' }}</dd></div>
          <div><dt>Exam</dt><dd>{{ exam?.examSearch || '—' }}</dd></div>
          <div><dt>Exam Year</dt><dd>{{ exam?.examYear || '—' }}</dd></div>
        </dl>
      </div>

      <div class="panel">
        <p class="sub-title">Pattern Summary</p>
        <dl>
          <div><dt>Total Questions</dt><dd>{{ pattern?.totalQuestions || totalQuestions }}</dd></div>
          <div><dt>Total Marks</dt><dd>{{ pattern?.totalMarks || totalSubjectMarks }}</dd></div>
          <div><dt>Marks Per Question</dt><dd>{{ pattern?.marksPerQuestion || '—' }}</dd></div>
          <div><dt>Negative Marking</dt><dd>{{ pattern?.negativeMarking || '—' }}</dd></div>
          <div><dt>Sectional Time</dt><dd>{{ pattern?.sectionalMinutes ? `${pattern.sectionalMinutes} Minutes` : 'Not enabled' }}</dd></div>
        </dl>

        <p class="block-title">Subjects Summary</p>
        <table>
          <thead>
            <tr><th>#</th><th>Subject</th><th>Questions</th><th>Marks</th></tr>
          </thead>
          <tbody>
            <tr v-for="(s, i) in subjectRows" :key="i">
              <td>{{ i + 1 }}</td>
              <td>{{ s.name }}</td>
              <td>{{ s.questions || 0 }}</td>
              <td>{{ s.marks || 0 }}</td>
            </tr>
            <tr class="total-row">
              <td colspan="2">Total</td>
              <td>{{ totalQuestions }}</td>
              <td>{{ totalSubjectMarks }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p v-if="submitError" class="error-text">{{ submitError }}</p>

    <div class="actions actions-between">
      <button class="btn-secondary" :disabled="submitting" @click="$emit('back')">← Previous Step</button>
      <button class="btn-primary" :disabled="submitting" @click="handleConfirm">
        {{ submitting ? 'Creating...' : '✓ Confirm & Create' }}
      </button>
    </div>

    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="showSuccessToast" class="success-toast" role="status" aria-live="polite">
          <span class="toast-icon">✓</span>
          <div class="toast-text">
            <strong>Mock test created successfully</strong>
            <span>{{ basic?.name || 'Your mock test' }} is ready.</span>
          </div>
          <button class="toast-close" aria-label="Dismiss" @click="showSuccessToast = false">✕</button>
        </div>
      </Transition>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  createMockExam,
  updateMockExam,
  buildMockExamPayload,
  type MockExam,
  type MockExamPattern,
} from '@/services/mockTestApi'

const props = defineProps<{
  basic?: Record<string, any>
  exam?: Record<string, any> // expects exam.examId (resolved PK from SelectExamStep)
  pattern?: MockExamPattern
  examTypeName?: string
  examCategoryName?: string
  /**
   * Set once the wizard has already created a draft mock exam earlier
   * (see CreateMockTestView.vue, step: Select Exam -> Set Pattern).
   * When present, Confirm & Create finalizes that draft via PUT instead
   * of POSTing a brand new mock exam. When absent (e.g. this component
   * is reused somewhere the draft-creation step was skipped), it falls
   * back to the old create-on-confirm behavior so nothing breaks.
   */
  mockexamId?: number | string | null
  /** Question objects selected in AddQuestionsStep (same shape it emits via next-step). */
  selectedQuestions?: import('@/services/mockTestApi').QuestionBankItem[]
}>()

// 'created' passes the saved MockExam back up so CreateMockTestView can
// redirect to a success screen / the mock tests list with the new id.
const emit = defineEmits<{
  back: []
  created: [mockExam: MockExam]
}>()

const submitting = ref(false)
const submitError = ref('')
const showSuccessToast = ref(false)
let toastTimer: ReturnType<typeof setTimeout> | null = null

const subjectRows = computed(() => props.pattern?.subjects || [])

const totalQuestions = computed<number>(() =>
  subjectRows.value.reduce(
    (sum: number, s: any) => sum + (Number(s.questions) || 0),
    0,
  )
)
const totalSubjectMarks = computed<number>(() =>
  subjectRows.value.reduce(
    (sum: number, s: any) => sum + (Number(s.marks) || 0),
    0,
  )
)

async function handleConfirm() {
  submitError.value = ''

  const examId = props.exam?.examId
  if (!examId) {
    submitError.value = 'No exam selected. Please go back to the Select Exam step.'
    return
  }
  if (!props.basic?.name) {
    submitError.value = 'Mock test name is required. Please go back to Basic Details.'
    return
  }

  submitting.value = true
  try {
    const payload = buildMockExamPayload(
      examId,
      props.basic || {},
      props.pattern || {},
      props.selectedQuestions || [],
    )
    // Publish the exam now that the wizard is done. If this component is
    // used somewhere the draft-creation step ran, is_active still comes
    // from Basic Details' toggle (props.basic.active) — buildMockExamPayload
    // already handles that; we don't force it true/false here.

    const created = props.mockexamId
      ? await updateMockExam(props.mockexamId, payload)
      : await createMockExam(payload) // fallback: no draft was created earlier

    showSuccessToast.value = true
    if (toastTimer) clearTimeout(toastTimer)
    toastTimer = setTimeout(() => {
      showSuccessToast.value = false
    }, 4000)

    emit('created', created)
  } catch (err: any) {
    submitError.value =
      err?.response?.data?.error ||
      err?.response?.data?.mockexam_name?.[0] ||
      'Something went wrong while creating the mock test. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.card { background: #fff; border: 1px solid #ecedf3; border-radius: 12px; padding: 22px 24px 26px; }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
.card-icon { font-size: 15px; }
.card-head h3 { font-size: 14.5px; margin: 0; }
.review-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel { border: 1px solid #ecedf3; border-radius: 10px; padding: 16px 18px; }
.sub-title { font-size: 12.5px; font-weight: 700; margin: 0 0 14px; }
.block-title { font-size: 11.5px; font-weight: 700; color: #8a8fa3; margin: 16px 0 8px; letter-spacing: 0.02em; }
dl { display: flex; flex-direction: column; gap: 8px; margin: 0; }
dl > div { display: flex; justify-content: space-between; font-size: 12.5px; }
dt { color: #8a8fa3; }
dd { margin: 0; color: #1f2333; font-weight: 500; text-align: right; max-width: 60%; }
.status-pill { background: #dcfce7; color: #16a34a; font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 999px; }
.status-pill.inactive { background: #fee2e2; color: #dc2626; }
table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 4px; }
th { text-align: left; color: #a6abc0; font-weight: 600; padding: 6px 4px; border-bottom: 1px solid #ecedf3; }
td { padding: 8px 4px; border-bottom: 1px solid #f3f3f8; }
.total-row td { font-weight: 700; border-bottom: none; padding-top: 10px; }
.error-text { color: #dc2626; font-size: 12.5px; margin: 0 0 12px; }
.actions { display: flex; margin-top: 22px; }
.actions-between { justify-content: space-between; }
.btn-primary { background: #6d28d9; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary:hover:not(:disabled) { background: #5b21b6; }
.btn-primary:disabled { background: #b8a4e8; cursor: not-allowed; }
.btn-secondary { background: #fff; color: #4b4f66; border: 1px solid #dfe1ea; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-secondary:hover:not(:disabled) { background: #f6f7fb; }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }

.success-toast {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #16a34a;
  color: #fff;
  padding: 14px 16px;
  border-radius: 10px;
  box-shadow: 0 12px 32px rgba(22, 163, 74, 0.28);
  max-width: 340px;
}
.toast-icon {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}
.toast-text { display: flex; flex-direction: column; gap: 2px; }
.toast-text strong { font-size: 13px; font-weight: 700; }
.toast-text span { font-size: 12px; opacity: 0.92; }
.toast-close {
  margin-left: auto;
  background: none;
  border: none;
  color: #fff;
  opacity: 0.75;
  cursor: pointer;
  font-size: 12px;
  padding: 2px;
  flex-shrink: 0;
}
.toast-close:hover { opacity: 1; }

.toast-fade-enter-active, .toast-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast-fade-enter-from, .toast-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>