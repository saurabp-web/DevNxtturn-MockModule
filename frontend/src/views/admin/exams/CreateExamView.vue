<template>
  <div class="wizard-page">
    <div class="wizard-header">
      <h1 class="wizard-title">Create New Exam</h1>
      <span class="wizard-step-label">Step {{ currentStep }} of {{ steps.length }}</span>
    </div>

    <div class="stepper">
      <template v-for="(step, i) in steps" :key="step.id">
        <div class="step" :class="{ active: currentStep === i + 1, done: currentStep > i + 1 }">
          <span class="step-circle">
            <svg v-if="currentStep > i + 1" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <template v-else>{{ i + 1 }}</template>
          </span>
          <span class="step-name">{{ step.label }}</span>
        </div>
        <div v-if="i < steps.length - 1" class="step-line" :class="{ done: currentStep > i + 1 }" />
      </template>
    </div>

    <p v-if="submitError" class="wizard-error">{{ submitError }}</p>

    <component
      :is="steps[currentStep - 1].component"
      :form="form"
      :submitting="submitting"
      @next="goNext"
      @back="goBack"
      @save-draft="saveDraft"
      @publish="publish"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { createExam, updateExam } from '@/services/examWizardApi'
import StepBasicInfo from '@/components/admin/exam-wizard/StepBasicInfo.vue'
import StepClassification from '@/components/admin/exam-wizard/StepClassification.vue'
import StepExamDetails from '@/components/admin/exam-wizard/StepExamDetails.vue'
import StepSyllabus from '@/components/admin/exam-wizard/StepSyllabus.vue'
import StepReviewPublish from '@/components/admin/exam-wizard/StepReviewPublish.vue'

// Shared form state across all 6 steps — each step component reads/writes
// directly into the relevant slice via props.form, so nothing needs to be
// re-collected on the review step.
const form = reactive({
  basicInfo: {
    examName: '',
    shortName: '',
    fullForm: '',
    description: '',
    examLogo: null as File | null,
    bannerImage: null as File | null,
  },
  classification: {
    examType: '',
    examCategory: '',
    examLevel: '',
    conductingBody: '',
  },
  academicMapping: {
    educationLevel: '',
    stream: '',
    field: '',
    subField: '',
  },
  examDetails: {
    // FIXED: `eligibility` freeform text removed from here — it duplicated
    // the structured `eligibility` object below (4D). That's now the
    // single source for eligibility data.
    ageLimit: '',
    applicationMode: '',
    examMode: '',
    examFrequency: '',
    duration: '',
    totalMarks: '',
    negativeMarking: '',
    officialWebsite: '',
    helplineContact: '',
  },
  examPattern: {
    sections: [
      { name: 'Physics', questions: 25, marks: 100, duration: '60 Min' },
      { name: 'Chemistry', questions: 25, marks: 100, duration: '60 Min' },
      { name: 'Mathematics', questions: 25, marks: 100, duration: '60 Min' },
    ],
    negativeMarking: '-1',
    markingScheme: '+4 / -1',
    unattempted: '0',
  },
  // FIXED: examBoards removed — 4B duplicated Step 2's conductingBody
  // field (one exam, one conducting body). If multiple recognizing
  // boards are genuinely needed later, model it as a multi-select on
  // `classification` rather than reviving a standalone screen/table.
  importantDates: {
    applicationStart: '',
    applicationEnd: '',
    admitCardRelease: '',
    examDate: '',
    resultDate: '',
  },
  eligibility: {
    educationalQualification: '',
    minimumMarks: '',
    ageCriteria: '',
    otherConditions: '',
  },
  syllabus: [
    {
      subject: 'Physics',
      chapters: [
        { name: 'Mechanics', topics: ['Kinematics', 'Laws of Motion', 'Work, Energy and Power'] },
        { name: 'Thermodynamics', topics: ['Thermal Properties of Matter', 'Thermodynamics', 'Kinetic Theory'] },
        { name: 'Modern Physics', topics: [] },
      ],
    },
    { subject: 'Chemistry', chapters: [] },
    { subject: 'Mathematics', chapters: [] },
  ],
})

const steps = [
  { id: 'basic', label: 'Basic Info', component: StepBasicInfo },
  { id: 'classification', label: 'Classification', component: StepClassification },
  { id: 'syllabus', label: 'Syllabus', component: StepSyllabus },
  { id: 'details', label: 'Exam Details', component: StepExamDetails },
  { id: 'review', label: 'Review & Publish', component: StepReviewPublish },
]

const currentStep = ref(1)
const toast = useToast()
const router = useRouter()

// Set once the exam has been saved as a draft at least once, so a
// subsequent Save/Publish click PUTs an update instead of creating a
// duplicate exam. Pass an existing examId in via route params to resume
// editing a draft (wire that up in the route/loader when you get there).
const examId = ref<number | null>(null)
const submitting = ref(false)
const submitError = ref('')

function goNext() {
  if (currentStep.value < steps.length) currentStep.value++
}
function goBack() {
  if (currentStep.value > 1) currentStep.value--
}

async function submit(publishFlag: boolean) {
  submitting.value = true
  submitError.value = ''
  try {
    const result = examId.value
      ? await updateExam(examId.value, form, publishFlag)
      : await createExam(form, publishFlag)
    examId.value = result.exam_id
    return result
  } catch (err: any) {
    submitError.value = err.message || 'Something went wrong saving this exam.'
    toast.error(submitError.value, { timeout: 5000 })
    throw err
  } finally {
    submitting.value = false
  }
}

async function saveDraft() {
  try {
    await submit(false)
    toast.success('Exam saved as draft successfully!', { timeout: 3000 })
    router.push('/exam-admin/exams/draft')
  } catch {
    /* error already surfaced via submitError */
  }
}

async function publish() {
  try {
    await submit(true)
    toast.success('Exam has been published successfully!', { timeout: 3000 })
    router.push('/exam-admin/exams/published')
  } catch {
    /* error already surfaced via submitError */
  }
}
</script>

<style scoped>
.wizard-page {
  max-width: 1100px;
}

.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.wizard-title { font-size: 20px; font-weight: 700; color: #111827; margin: 0; }
.wizard-step-label { font-size: 13px; color: #6B7280; }

.stepper {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
  overflow-x: auto;
}
.step {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.step-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #F3F4F6;
  color: #6B7280;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step.active .step-circle { background: #7C3AED; color: #fff; }
.step.done .step-circle { background: #7C3AED; }
.step-name { font-size: 13px; color: #6B7280; }
.step.active .step-name { color: #111827; font-weight: 600; }
.step.done .step-name { color: #374151; }
.step-line {
  flex: 1;
  min-width: 24px;
  height: 2px;
  background: #E5E7EB;
  margin: 0 10px;
}
.step-line.done { background: #7C3AED; }

.wizard-error {
  background: #FEF2F2;
  color: #DC2626;
  border: 1px solid #FECACA;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 16px;
}
</style>