<template>
  <div class="page-wrapper">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Add New Question</h1>
        <p class="page-desc">{{ stepDescriptions[currentStep - 1] }}</p>
      </div>
      <button class="back-btn" @click="router.push({ name: 'question-bank' })" type="button">
        ← Back to Question Bank
      </button>
    </div>

    <!-- Step Indicator -->
    <div class="stepper">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="stepper-item"
        :class="{
          'stepper-item--active': currentStep === step.id,
          'stepper-item--completed': currentStep > step.id
        }"
      >
        <div class="stepper-circle">
          <span v-if="currentStep > step.id" class="check-icon">✓</span>
          <span v-else>{{ step.id }}</span>
        </div>
        <span class="stepper-label">{{ step.label }}</span>
        <div v-if="index < steps.length - 1" class="stepper-connector" />
      </div>
    </div>

    <!-- Step Content Card -->
    <div class="card">
      <QuestionClassification
        v-if="currentStep === 1"
        v-model="formData.step1"
        @next="goNext"
      />
      <QuestionEditor
        v-else-if="currentStep === 2"
        v-model="formData.step2"
        :chapter-id="formData.step1?.chapter"
        @next="goNext"
        @prev="goPrev"
      />
      <OptionsAnswer
        v-else-if="currentStep === 3"
        v-model="formData.step3"
        @next="goNext"
        @prev="goPrev"
      />
      <MarksEvaluation
        v-else-if="currentStep === 4"
        v-model="formData.step4"
        :question-summary="questionSummary"
        :submitting="isSubmitting"
        @next="handleSubmit"
        @prev="goPrev"
      />
    </div>

    <!-- Success Toast -->
    <Transition name="toast">
      <div v-if="showSuccess" class="toast">
        ✓ Question saved successfully!
      </div>
    </Transition>

    <!-- Error Toast -->
    <Transition name="toast">
      <div v-if="errorMessage" class="toast toast--error">
        ✕ {{ errorMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import QuestionClassification from '@/components/admin/question/QuestionClassification.vue'
import QuestionEditor from '@/components/admin/question/QuestionEditor.vue'
import OptionsAnswer from '@/components/admin/question/OptionsAnswer.vue'
import MarksEvaluation from '@/components/admin/question/MarksEvaluation.vue'
import { createQuestion, buildQuestionPayload, isQuestionValidationError } from '@/services/questionAdminApi'

const router = useRouter()

const currentStep = ref(1)
const showSuccess = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

const steps = [
  { id: 1, label: 'Question Details' },
  { id: 2, label: 'Options & Answer' },
  { id: 3, label: 'Marks & Evaluation' },
  { id: 4, label: 'Review & Save' }
]

const stepDescriptions = [
  'Create a new question manually by selecting classification details.',
  'Enter the question text and add any required images.',
  'Add options for the question and select the correct answer.',
  'Set marks, negative marks and add explanation (optional).'
]

const formData = reactive({
  step1: {},
  step2: {},
  step3: {},
  step4: {}
})

// Human-readable labels (examLabel/subjectLabel/chapterLabel) are set by
// QuestionClassification.vue alongside the raw ids, since the summary
// card and Review step want names, not database ids.
const questionSummary = computed(() => ({
  exam: formData.step1?.examLabel || '',
  subject: formData.step1?.subjectLabel || '',
  chapter: formData.step1?.chapterLabel || '',
  topic: formData.step1?.topic || '',
  type: formData.step1?.questionType || '',
  difficulty: formData.step1?.difficulty || '',
  totalOptions: formData.step3?.options?.length || 0,
  isPyq: formData.step1?.isPyq || false,
  pyqExam: formData.step1?.pyqExam || '',
  pyqYear: formData.step1?.pyqYear || '',
  pyqSession: formData.step1?.pyqSession || ''
}))

function goNext() {
  if (currentStep.value < 4) currentStep.value++
}

function goPrev() {
  if (currentStep.value > 1) currentStep.value--
}

async function handleSubmit() {
  errorMessage.value = ''

  const payload = buildQuestionPayload(formData.step1, formData.step2, formData.step3, formData.step4)

  isSubmitting.value = true
  try {
    await createQuestion(payload)
    showSuccess.value = true
    setTimeout(() => { showSuccess.value = false }, 3000)
    router.push({ name: 'question-bank' })
  } catch (err) {
    console.error('Failed to save question:', err)
    errorMessage.value = isQuestionValidationError(err)
      ? Object.values(err.response.data.errors).join(' ')
      : (err?.response?.data?.error || 'Failed to save the question. Please try again.')
    setTimeout(() => { errorMessage.value = '' }, 5000)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.page-wrapper {
  min-height: 100vh;
  background: #f5f6fa;
  padding: 28px 32px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Page Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
}

.page-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  color: #4f46e5;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.back-btn:hover {
  background: #f5f3ff;
  border-color: #4f46e5;
}

/* Stepper */
.stepper {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 20px;
  position: relative;
}

.stepper-item {
  display: flex;
  align-items: center;
  flex: 1;
  position: relative;
}

.stepper-item:last-child {
  flex: 0;
}

.stepper-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
  border: 2px solid #d1d5db;
  background: #fff;
  color: #9ca3af;
  transition: all 0.2s;
  z-index: 1;
}

.stepper-item--active .stepper-circle {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #fff;
}

.stepper-item--completed .stepper-circle {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #fff;
}

.check-icon {
  font-size: 14px;
}

.stepper-label {
  font-size: 13px;
  font-weight: 500;
  color: #9ca3af;
  margin-left: 10px;
  white-space: nowrap;
  transition: color 0.2s;
}

.stepper-item--active .stepper-label,
.stepper-item--completed .stepper-label {
  color: #374151;
}

.stepper-connector {
  flex: 1;
  height: 2px;
  background: #e5e7eb;
  margin: 0 12px;
  transition: background 0.2s;
}

.stepper-item--completed + .stepper-item .stepper-connector,
.stepper-item--completed .stepper-connector {
  background: #4f46e5;
}

/* Card */
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 28px 32px;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  background: #4f46e5;
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(79,70,229,0.3);
  z-index: 1000;
}

.toast--error {
  background: #dc2626;
  box-shadow: 0 4px 16px rgba(220,38,38,0.3);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(16px);
}
</style>