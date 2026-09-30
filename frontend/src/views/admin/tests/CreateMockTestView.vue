<template>
  <div class="page">
    <header class="page-head">
      <button class="back-link" @click="goBack">← Back to Mock Tests</button>
      <h1>Create Mock Test</h1>
      <p>Set up a new mock test in a few guided steps</p>
    </header>

    <!-- Step indicator -->
    <ol class="stepper">
      <li
        v-for="(s, i) in steps"
        :key="s.key"
        class="step"
        :class="{ active: i === currentStep, done: i < currentStep }"
      >
        <span class="step-dot">
          <span v-if="i < currentStep">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </span>
        <span class="step-label">{{ s.label }}</span>
        <span v-if="i < steps.length - 1" class="step-line"></span>
      </li>
    </ol>

    <p v-if="editLoading" class="draft-error draft-loading">Loading mock test details…</p>
    <p v-if="draftError" class="draft-error">{{ draftError }}</p>

    <!-- Step content -->
    <!-- AddQuestionsStep (step index 3) emits different events than the
         other steps: 'next-step' carries the selected questions array,
         'previous-step' goes back, and 'save-exit' saves & navigates away.
         All other steps use plain @next / @back. -->
    <template v-if="currentStep === 3">
      <AddQuestionsStep
        v-bind="steps[currentStep].props()"
        @next-step="onQuestionsNext"
        @previous-step="prevStep"
        @save-exit="onQuestionsSaveExit"
        @back="goBack"
      />
    </template>
    <template v-else>
      <component
        :is="steps[currentStep].component"
        v-bind="steps[currentStep].props()"
        @update:modelValue="steps[currentStep].onUpdate"
        @back="prevStep"
        @next="handleNext"
        @created="onCreated"
      />
    </template>

    <!-- Success notification, shown briefly before redirecting -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="showToast" class="success-toast" role="status" aria-live="polite">
          <span class="toast-icon">✓</span>
          <div class="toast-text">
            <strong>Mock test created successfully</strong>
            <span>{{ createdName }} is ready. Redirecting to Mock Tests…</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BasicDetailsStep from '@/components/admin/mock-test/BasicDetailsStep.vue'
import SelectExamStep from '@/components/admin/mock-test/SelectExamStep.vue'
import SetPatternStep from '@/components/admin/mock-test/SetPatternStep.vue'
import ReviewConfirmStep from '@/components/admin/mock-test/ReviewConfirmStep.vue'
import AddQuestionsStep from '@/components/admin/mock-test/AddQuestionsStep.vue'
import type { MockExam, QuestionBankItem } from '@/services/mocktestapi'
import {
  fetchQuestionBank,
  fetchMockExam,
  fetchExamDetail,
  createDraftMockExam,
  updateMockExam,
  buildMockExamPayload,
} from '@/services/mocktestapi'

const router = useRouter()
const route = useRoute()

const currentStep = ref(0)
const showToast = ref(false)
const createdName = ref('')

// Question bank data — loaded once when AddQuestionsStep mounts.
const questionBank = ref<QuestionBankItem[]>([])
const questionBankLoading = ref(false)
const questionBankError = ref<string | null>(null)

async function loadQuestionBank() {
  if (questionBank.value.length || questionBankLoading.value) return
  questionBankLoading.value = true
  questionBankError.value = null
  try {
    questionBank.value = await fetchQuestionBank({ exam_id: wizard.exam?.examId })
  } catch (e: any) {
    questionBankError.value = e?.message || 'Failed to load question bank'
  } finally {
    questionBankLoading.value = false
  }
}

// Single source of truth for all wizard data — each step reads/writes its
// own slice via v-model, and ReviewConfirmStep reads all of them.
const wizard = reactive({
  basic: {} as Record<string, any>,
  exam: {} as Record<string, any>,
  pattern: { subjects: [] } as Record<string, any>,
  // selectedQuestions holds the array of QuestionBankItem chosen in step 4.
  selectedQuestions: [] as QuestionBankItem[],
})

// mockexamId of the DRAFT mock test, created as soon as Basic Details +
// Select Exam are done (see handleNext, currentStep === 1 branch below).
// Fixes: AddQuestionsStep's Bulk Upload sub-flow needs a real
// mockexamId to call /api/mockexams/<id>/bulk-upload/validate/ — before
// this fix, that id was still null at step 4 because the mock test
// record wasn't created until Review & Confirm (the final step), which
// produced /api/mockexams/null/bulk-upload/validate/ -> 404.
const mockexamId = ref<number | string | null>(null)
const draftError = ref<string | null>(null)
const isNavigating = ref(false)

// ── Edit mode: GET /mockexams/<id>/ when the URL has ?edit=<id> ──────
// Previously this component never read the `edit` query param at all —
// mockexamId only got set later via createDraftMockExam() inside
// handleNext(), so visiting .../mock/create?edit=5 rendered a
// completely empty wizard (Basic Details, Select Exam, Set Pattern all
// blank) instead of the existing mock test's data. This is the actual
// fix — the per-step hydration watchers added earlier only work once
// something here actually fetches the record and assigns it into
// wizard.basic / wizard.exam / wizard.pattern.
const editLoading = ref(false)

onMounted(async () => {
  const editId = route.query.edit as string | undefined
  if (!editId) return

  editLoading.value = true
  draftError.value = null
  try {
    const mockExam = await fetchMockExam(editId)
    mockexamId.value = mockExam.mockexam_id

    wizard.basic = {
      name: mockExam.mockexam_name || '',
      year: mockExam.year || '',
      description: mockExam.description || '',
      totalMarks: mockExam.total_marks || '',
      duration: mockExam.duration_minutes || '',
      active: mockExam.is_active,
    }

    // MockExamSerializer only exposes exam_id/exam_code/exam_type_name/
    // category_name (read-only display fields) — SelectExamStep's form
    // needs the actual examTypeId/categoryId to restore its dropdowns
    // and re-run its category-list bootstrap, so fetch the full Exam
    // record separately.
    let examTypeId: number | string = ''
    let categoryId: number | string = ''
    let examName = mockExam.exam_code || ''
    try {
      const examDetail = await fetchExamDetail(mockExam.exam_id)
      examTypeId = examDetail.exam_type ?? ''
      categoryId = examDetail.category_id ?? ''
      examName = examDetail.exam_name || examName
    } catch {
      // Non-fatal — exam name/id still populate below, just without the
      // type/category dropdowns pre-selected.
    }

    wizard.exam = {
      examTypeId,
      categoryId,
      examId: mockExam.exam_id,
      examSearch: examName,
      examYear: mockExam.year || '',
    }

    wizard.pattern = {
      ...(mockExam.pattern || {}),
      subjects: (mockExam.pattern as any)?.subjects || [],
    }
  } catch (err: any) {
    draftError.value =
      err?.response?.data?.error ||
      `Could not load mock test #${editId} for editing. Please try again.`
  } finally {
    editLoading.value = false
  }
})

const examTypeName = computed(() => wizard.exam?.examTypeName || '')
const examCategoryName = computed(() => wizard.exam?.categoryName || '')

const steps = [
  {
    key: 'basic',
    label: 'Basic Details',
    component: BasicDetailsStep,
    props: () => ({ modelValue: wizard.basic }),
    onUpdate: (val: Record<string, any>) => (wizard.basic = val),
  },
  {
    key: 'exam',
    label: 'Select Exam',
    component: SelectExamStep,
    props: () => ({ modelValue: wizard.exam }),
    onUpdate: (val: Record<string, any>) => (wizard.exam = val),
  },
  {
    key: 'pattern',
    label: 'Set Pattern',
    component: SetPatternStep,
    props: () => ({ modelValue: wizard.pattern, examId: wizard.exam?.examId }),
    onUpdate: (val: Record<string, any>) => (wizard.pattern = val),
  },
  {
    key: 'questions',
    label: 'Add Questions',
    component: AddQuestionsStep,
    props: () => ({
      questionBank: questionBank.value,
      loading: questionBankLoading.value,
      error: questionBankError.value,
      mockexamId: mockexamId.value,
      examId: wizard.exam?.examId,
    }),
    onUpdate: () => {},
  },
  {
    key: 'review',
    label: 'Review & Confirm',
    component: ReviewConfirmStep,
    props: () => ({
      basic: wizard.basic,
      exam: wizard.exam,
      pattern: wizard.pattern,
      selectedQuestions: wizard.selectedQuestions,
      examTypeName: examTypeName.value,
      examCategoryName: examCategoryName.value,
      mockexamId: mockexamId.value,
    }),
    onUpdate: () => {},
  },
]

// AddQuestionsStep emits 'next-step' with the chosen questions array.
// All other steps emit plain 'next'. The component tag handles both via
// @next and @next-step listeners below.
function onQuestionsNext(selected: QuestionBankItem[]) {
  wizard.selectedQuestions = selected
  nextStep()
}

function onQuestionsSaveExit(selected: QuestionBankItem[]) {
  wizard.selectedQuestions = selected
  router.push({ name: 'admin-tests-mock' })
}

function nextStep() {
  if (currentStep.value < steps.length - 1) currentStep.value++
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function prevStep() {
  if (currentStep.value > 0) currentStep.value--
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// When navigating forward INTO step 3 (Add Questions), trigger the bank load.
// Also: when leaving Select Exam (step 1) or Set Pattern (step 2), create
// or sync the draft mock exam so a real mockexamId exists before the user
// ever reaches Add Questions / Bulk Upload.
async function handleNext() {
  if (isNavigating.value) return
  isNavigating.value = true
  draftError.value = null

  try {
    if (currentStep.value === 1) {
      // Leaving "Select Exam" — first point where both Basic Details and
      // an Exam are available, so create the draft mock exam now.
      if (!mockexamId.value) {
        const draft = await createDraftMockExam(wizard.exam.examId, wizard.basic, wizard.pattern)
        mockexamId.value = draft.mockexam_id
      } else {
        // User went back and re-picked details after a draft already
        // existed — update the same record instead of creating another.
        const payload = buildMockExamPayload(wizard.exam.examId, wizard.basic, wizard.pattern)
        await updateMockExam(mockexamId.value, payload)
      }
    } else if (currentStep.value === 2 && mockexamId.value) {
      // Leaving "Set Pattern" — keep the draft's pattern/subjects current.
      const payload = buildMockExamPayload(wizard.exam.examId, wizard.basic, wizard.pattern)
      await updateMockExam(mockexamId.value, payload)
    }
  } catch (err: any) {
    draftError.value =
      err?.response?.data?.error ||
      err?.response?.data?.mockexam_name?.[0] ||
      'Could not save this mock test yet. Please check the details above and try again.'
    isNavigating.value = false
    return // don't advance the step if saving the draft failed
  }

  nextStep()
  if (currentStep.value === 3) {
    loadQuestionBank()
  }
  isNavigating.value = false
}

function goBack() {
  router.push({ name: 'admin-tests-mock' })
}

// Fired by ReviewConfirmStep once the mock test has actually been created
// (POST succeeded). Show a brief success toast, then redirect straight to
// the Mock Tests table so the new row is visible in the list.
function onCreated(mockExam: MockExam) {
  createdName.value = mockExam?.mockexam_name || wizard.basic?.name || 'Your mock test'
  showToast.value = true

  setTimeout(() => {
    router.push({
      name: 'admin-tests-mock',
      query: { created: '1', name: createdName.value },
    })
  }, 1200)
}
</script>

<style scoped>
.page { max-width: 1390px; margin: 0 auto; padding: 28px 32px 60px; }
.page-head { margin-bottom: 22px; }
.back-link {
  background: none; border: none; color: #6d28d9; font-size: 12.5px; font-weight: 600;
  cursor: pointer; padding: 0; margin-bottom: 10px;
}
.back-link:hover { text-decoration: underline; }
.page-head h1 { font-size: 22px; margin: 0 0 4px; color: #1f2333; }
.page-head p { font-size: 13px; color: #8a8fa3; margin: 0; }

.draft-error {
  background: #fde8e8;
  color: #c0322f;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin: 0 0 18px;
}
.draft-loading {
  background: #f2effe;
  color: #4b3b93;
}

.stepper { list-style: none; display: flex; margin: 0 0 26px; padding: 0; }
.step { flex: 1; display: flex; align-items: center; gap: 10px; position: relative; }
.step-dot {
  width: 28px; height: 28px; border-radius: 50%; background: #ecedf3; color: #8a8fa3;
  display: flex; align-items: center; justify-content: center; font-size: 12.5px; font-weight: 700;
  flex-shrink: 0; z-index: 1;
}
.step.active .step-dot { background: #6d28d9; color: #fff; }
.step.done .step-dot { background: #dcfce7; color: #16a34a; }
.step-label { font-size: 12.5px; font-weight: 600; color: #8a8fa3; white-space: nowrap; }
.step.active .step-label, .step.done .step-label { color: #1f2333; }
.step-line { flex: 1; height: 2px; background: #ecedf3; margin: 0 4px; }
.step.done .step-line { background: #a78bfa; }

.success-toast {
  position: fixed; bottom: 28px; right: 28px; z-index: 1000;
  display: flex; align-items: flex-start; gap: 12px;
  background: #16a34a; color: #fff; padding: 14px 18px; border-radius: 10px;
  box-shadow: 0 12px 32px rgba(22, 163, 74, 0.28); max-width: 340px;
}
.toast-icon {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
  background: rgba(255, 255, 255, 0.22); display: flex; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700;
}
.toast-text { display: flex; flex-direction: column; gap: 2px; }
.toast-text strong { font-size: 13px; font-weight: 700; }
.toast-text span { font-size: 12px; opacity: 0.92; }

.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateY(8px); }
</style>