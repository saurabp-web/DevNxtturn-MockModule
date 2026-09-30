<!-- ConfigureTestPublish.vue -->
<script setup>
import { reactive, ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { pyqImport } from '@/services/pyqImportStore'
import MathRenderer from './MathRenderer.vue'

const router = useRouter()

const form = reactive({
  testName: pyqImport.paperDetails?.exam_name ? 
    `${pyqImport.paperDetails.exam_name} ${pyqImport.paperDetails.exam_year || ''}${pyqImport.paperDetails.pyq_session ? ` (${pyqImport.paperDetails.pyq_session})` : ''}`.trim() 
    : 'JEE Main 2024 (Paper 1)',
  duration: '180',
  durationUnit: 'minutes',
  negativeMarking: '-1',
  shuffleQuestions: true,
  shuffleOptions: true,
  showSolutions: false,
})

const summary = reactive({
  totalQuestions: 0,
  totalMarks: 0,
  mcqQuestions: 0,
  nonMcqQuestions: 0,
})

onMounted(() => {
  // Calculate summary from imported questions
  if (pyqImport.summary) {
    summary.totalQuestions = pyqImport.summary.totalExtracted || 0
    summary.totalMarks = (pyqImport.summary.valid || 0) * 4
  }
  
  // If we have questions data, count MCQ vs Non-MCQ
  if (pyqImport.questions && pyqImport.questions.length) {
    const mcq = pyqImport.questions.filter(q => q.question_type === 'MCQ').length
    summary.mcqQuestions = mcq
    summary.nonMcqQuestions = pyqImport.questions.length - mcq
  }
})

function goNext() {
  router.push({ name: 'admin-tests-previous-published' })
}

function goBack() {
  router.push({ name: 'admin-tests-previous-review-questions' })
}
</script>

<template>
  <div class="p-6 max-w-4xl">
    <div class="flex items-center gap-2 text-xs text-gray-400 mb-5">
      <span class="flex items-center gap-1 text-emerald-500 font-medium">
        <span class="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 text-[10px] text-white">✓</span>
        Extract Questions
      </span>
      <span>&rarr;</span>
      <span class="flex items-center gap-1 text-emerald-500 font-medium">
        <span class="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 text-[10px] text-white">✓</span>
        Map Questions
      </span>
      <span>&rarr;</span>
      <span class="flex items-center gap-1 font-medium text-[#6C4CF1]">
        <span class="flex h-4 w-4 items-center justify-center rounded-full bg-[#6C4CF1] text-[10px] text-white">3</span>
        Configure Test
      </span>
      <span>&rarr;</span>
      <span class="flex items-center gap-1 text-gray-400">
        <span class="flex h-4 w-4 items-center justify-center rounded-full bg-gray-200 text-[10px] text-gray-500">4</span>
        Publish
      </span>
    </div>

    <div class="grid grid-cols-3 gap-5">
      <div class="col-span-2 rounded-xl border border-gray-200 bg-white p-6">
        <h3 class="mb-4 text-sm font-semibold text-gray-700">Test Configuration</h3>

        <div class="mb-4">
          <label class="mb-1 block text-xs font-medium text-gray-500">Test Name *</label>
          <input v-model="form.testName" type="text" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-xs outline-none focus:border-[#6C4CF1]" />
        </div>

        <div class="mb-4 grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">Time Duration *</label>
            <input v-model="form.duration" type="text" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-xs outline-none focus:border-[#6C4CF1]" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500 opacity-0">Unit</label>
            <select v-model="form.durationUnit" class="w-full rounded-lg border border-gray-200 px-3 py-2 text-xs outline-none focus:border-[#6C4CF1]">
              <option>minutes</option>
              <option>hours</option>
            </select>
          </div>
        </div>

        <div class="mb-5">
          <label class="mb-1 block text-xs font-medium text-gray-500">Negative Marking</label>
          <div class="flex items-center gap-2">
            <input v-model="form.negativeMarking" type="text" class="w-24 rounded-lg border border-gray-200 px-3 py-2 text-xs outline-none focus:border-[#6C4CF1]" />
            <span class="text-xs text-gray-400">marks</span>
          </div>
        </div>

        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-600">Shuffle Questions</span>
            <button
              @click="form.shuffleQuestions = !form.shuffleQuestions"
              class="h-5 w-9 rounded-full transition-colors"
              :class="form.shuffleQuestions ? 'bg-[#6C4CF1]' : 'bg-gray-200'"
            >
              <span class="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform" :class="form.shuffleQuestions ? 'translate-x-4' : ''" />
            </button>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-600">Shuffle Options</span>
            <button
              @click="form.shuffleOptions = !form.shuffleOptions"
              class="h-5 w-9 rounded-full transition-colors"
              :class="form.shuffleOptions ? 'bg-[#6C4CF1]' : 'bg-gray-200'"
            >
              <span class="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform" :class="form.shuffleOptions ? 'translate-x-4' : ''" />
            </button>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-600">Show Solutions After Test</span>
            <button
              @click="form.showSolutions = !form.showSolutions"
              class="h-5 w-9 rounded-full transition-colors"
              :class="form.showSolutions ? 'bg-[#6C4CF1]' : 'bg-gray-200'"
            >
              <span class="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform" :class="form.showSolutions ? 'translate-x-4' : ''" />
            </button>
          </div>
        </div>
        
        <!-- Preview of first question with math -->
        <div v-if="pyqImport.questions && pyqImport.questions.length" class="mt-5 border-t border-gray-100 pt-4">
          <p class="text-[11px] font-medium text-gray-500 mb-2">Sample Question Preview:</p>
          <div class="rounded-lg bg-gray-50 p-3">
            <MathRenderer :content="pyqImport.questions[0]?.question_text || ''" />
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-gray-200 bg-white p-5 h-fit">
        <h3 class="mb-3 text-sm font-semibold text-gray-700">Question Summary</h3>
        <div class="space-y-2.5 text-xs">
          <div class="flex justify-between">
            <span class="text-gray-400">Total Questions</span>
            <span class="font-medium text-gray-700">{{ summary.totalQuestions }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Total Marks</span>
            <span class="font-medium text-gray-700">{{ summary.totalMarks }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">MCQ Questions</span>
            <span class="font-medium text-gray-700">{{ summary.mcqQuestions }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Non-MCQ Questions</span>
            <span class="font-medium text-gray-700">{{ summary.nonMcqQuestions }}</span>
          </div>
          <div class="flex justify-between border-t border-gray-100 pt-2 mt-2">
            <span class="text-gray-400">Valid Questions</span>
            <span class="font-medium text-emerald-600">{{ pyqImport.summary?.valid || 0 }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Needs Review</span>
            <span class="font-medium text-amber-600">{{ pyqImport.summary?.needsReview || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-6 flex justify-end gap-3">
      <button @click="goBack" class="rounded-lg border border-gray-200 px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50">
        ← Back
      </button>
      <button @click="goNext" class="rounded-lg bg-[#6C4CF1] px-4 py-2 text-xs font-semibold text-white hover:bg-[#5B3EE0]">
        Next: Review →
      </button>
    </div>
  </div>
</template>