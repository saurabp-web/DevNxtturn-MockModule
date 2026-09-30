<!-- ReviewCreateTest.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PYWizardStepper from './PYWizardStepper.vue'
import api from '@/api'
import { pyqImport, resetPyqImport } from '@/services/pyqImportStore'
import MathRenderer from './MathRenderer.vue'

const router = useRouter()
const creating = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  if (!pyqImport.uploadId) {
    router.replace({ name: 'admin-tests-previous-upload' })
    return
  }
  // The store copy of the summary/details can be stale (bulk-validate, edits,
  // Add-to-Test all happen after upload) — always show what the server has now.
  try {
    const [{ data: list }, { data: details }] = await Promise.all([
      api.get(`/pyq-import/${pyqImport.uploadId}/questions/`, { params: { page: 1, page_size: 1 } }),
      api.get(`/pyq-import/${pyqImport.uploadId}/paper-details/`),
    ])
    if (list.summary) pyqImport.summary = { ...(pyqImport.summary || {}), ...list.summary }
    if (details) pyqImport.paperDetails = details
  } catch (e) {
    console.error('Could not refresh summary', e)
  }
  // Math rendering is handled per-element by <MathRenderer> — do NOT call
  // renderMathInElement(document.body, ...) here; it mutates the DOM outside
  // Vue's control and corrupts vnode tracking on the next patch/unmount.
})

const details = computed(() => {
  const d = pyqImport.paperDetails
  const subjectLabel = (d.subject_names && d.subject_names.length)
    ? d.subject_names.join(', ')
    : '—'
  return [
    { label: 'Exam', value: d.exam_name || '—' },
    { label: 'Conducting Body', value: d.conducting_body || '—' },
    { label: 'Exam Year', value: d.exam_year || '—' },
    { label: 'Session / Shift', value: d.pyq_session || '—' },
    { label: 'Subject(s)', value: subjectLabel },
    { label: 'Difficulty Level', value: d.difficulty || '—' },
    { label: 'Valid Questions', value: pyqImport.summary.valid ?? '—' },
    { label: 'Already added to Practice Test', value: `${pyqImport.summary.addedPractice ?? 0} questions` },
    { label: 'Already added to Custom Test', value: `${pyqImport.summary.addedCustom ?? 0} questions` },
  ]
})

async function goNext() {
  if (!pyqImport.summary.valid) {
    errorMsg.value = 'There are no valid questions to create a test from. Go back and review the questions.'
    return
  }
  creating.value = true
  errorMsg.value = ''
  try {
    const testName = `${pyqImport.paperDetails.exam_name || ''} ${pyqImport.paperDetails.exam_year || ''}${pyqImport.paperDetails.pyq_session ? ` (${pyqImport.paperDetails.pyq_session})` : ''}`.trim()
    const { data } = await api.post(`/pyq-import/${pyqImport.uploadId}/create-test/`, {
      test_name: testName || 'Previous Year Test',
    })
    resetPyqImport()
    router.push({ name: 'admin-tests-previous', query: { created: data.mockExamId } })
  } catch (e) {
    errorMsg.value = e?.response?.data?.error || 'Could not create the test. Please try again.'
  } finally {
    creating.value = false
  }
}

function goBack() {
  router.push({ name: 'admin-tests-previous-review-questions' })
}
</script>

<template>
  <div class="p-6">
    <PYWizardStepper :current-step="4" />

    <div class="mx-auto max-w-4xl">
      <h3 class="text-base font-semibold text-gray-900">Review &amp; Confirm</h3>
      <p class="mt-1 text-xs text-gray-500">Please review the details before creating the test.</p>

      <div class="mt-5 rounded-xl border border-gray-200 bg-white p-6">
        <div class="grid grid-cols-2 gap-x-10 gap-y-5">
          <div v-for="d in details" :key="d.label" class="flex items-center gap-3">
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-50 text-[#6C4CF1]">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="7" r="4"/><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/></svg>
            </span>
            <div>
              <p class="text-[11px] text-gray-400">{{ d.label }}</p>
              <p class="text-xs font-semibold text-gray-800"><MathRenderer :content="d.value" /></p>
            </div>
          </div>
        </div>

        <div class="mt-6 border-t border-gray-100 pt-5">
          <p class="mb-2 text-[11px] text-gray-400">Source File</p>
          <div class="flex w-fit items-center gap-3 rounded-lg border border-gray-100 px-3 py-2.5">
            <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50 text-red-400">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </span>
            <div>
              <p class="text-xs font-medium text-gray-800">{{ pyqImport.fileName || '—' }}</p>
              <p class="text-[11px] text-gray-400">{{ pyqImport.fileSize || '' }}</p>
            </div>
          </div>
        </div>
        
        <!-- Sample question preview -->
        <div v-if="pyqImport.questions && pyqImport.questions.length" class="mt-5 border-t border-gray-100 pt-4">
          <p class="text-[11px] text-gray-400 mb-2">Sample Question:</p>
          <div class="rounded-lg bg-gray-50 p-3 text-xs">
            <MathRenderer :content="pyqImport.questions[0]?.question_text || ''" />
            <div class="mt-2 grid grid-cols-2 gap-1">
              <span class="text-gray-500">A. <MathRenderer :content="pyqImport.questions[0]?.options?.A || ''" /></span>
              <span class="text-gray-500">B. <MathRenderer :content="pyqImport.questions[0]?.options?.B || ''" /></span>
              <span class="text-gray-500">C. <MathRenderer :content="pyqImport.questions[0]?.options?.C || ''" /></span>
              <span class="text-gray-500">D. <MathRenderer :content="pyqImport.questions[0]?.options?.D || ''" /></span>
            </div>
          </div>
        </div>
      </div>

      <p class="mt-3 text-[11px] text-gray-400">
        Questions already added to a Practice or Custom test are reused, not duplicated.
      </p>
      <p v-if="errorMsg" class="mt-3 text-xs text-red-500">{{ errorMsg }}</p>

      <div class="mt-6 flex justify-end gap-3">
        <button class="rounded-lg border border-gray-200 px-4 py-2.5 text-xs font-medium text-gray-600 hover:bg-gray-50" @click="goBack">
          ← Back
        </button>
        <button
          class="flex items-center gap-2 rounded-lg bg-[#6C4CF1] px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-[#5B3EE0] disabled:opacity-60"
          :disabled="creating"
          @click="goNext"
        >
          <svg v-if="creating" class="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" /></svg>
          <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
          {{ creating ? 'Creating…' : 'Create Test' }}
        </button>
      </div>
    </div>
  </div>
</template>