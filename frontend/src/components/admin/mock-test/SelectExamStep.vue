<template>
  <section class="card">
    <header class="card-head">
      <span class="card-icon">🎯</span>
      <h3>Select Exam</h3>
    </header>

    <div class="grid-2">
      <div class="field">
        <label>Exam Type <span class="req">*</span></label>
        <select v-model="form.examTypeId" @change="onExamTypeChange">
          <option value="" disabled>Select exam type</option>
          <option v-for="t in examTypes" :key="t.exam_type_id" :value="t.exam_type_id">
            {{ t.type_name }}
          </option>
        </select>
      </div>
      <div class="field">
        <label>Exam Category <span class="req">*</span></label>
        <select v-model="form.categoryId" :disabled="!form.examTypeId || loadingCategories">
          <option value="" disabled>{{ loadingCategories ? 'Loading...' : 'Select category' }}</option>
          <option v-for="c in examCategories" :key="c.category_id" :value="c.category_id">
            {{ c.category_name }}
          </option>
        </select>
      </div>
    </div>

    <div class="grid-2">
      <div class="field exam-search-field">
        <label>Exam <span class="req">*</span></label>
        <div class="search-input">
          <input
            v-model="examSearchText"
            type="text"
            placeholder="Search and select exam"
            @input="onSearchInput"
            @focus="showResults = true"
          />
          <span class="search-icon">🔍</span>
        </div>

        <ul v-if="showResults && searchResults.length" class="results-dropdown">
          <li v-for="e in searchResults" :key="e.exam_id" @click="selectExam(e)">
            <span class="result-name">{{ e.exam_name }}</span>
            <span class="result-code">{{ e.exam_code }}</span>
          </li>
        </ul>
        <p v-else-if="showResults && searching" class="search-status">Searching...</p>
        <p v-else-if="showResults && examSearchText && !searching" class="search-status">No exams found.</p>
      </div>
      <div class="field">
        <label>Exam Year (Optional)</label>
        <select v-model="form.examYear">
          <option value="" disabled>Select year</option>
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>

    <div class="preview-box" :class="{ filled: !!selectedExam }">
      <span class="preview-icon">ⓘ</span>
      <div v-if="!selectedExam">
        <strong>Selected Exam Preview</strong>
        <p>Please select an exam to see its details.</p>
      </div>
      <div v-else class="preview-details">
        <strong>{{ selectedExam.exam_name }} ({{ selectedExam.exam_code }})</strong>
        <p>
          {{ selectedExam.exam_type_name || '—' }}
          <span v-if="selectedExam.category_name"> · {{ selectedExam.category_name }}</span>
          <span v-if="selectedExam.question_count !== undefined"> · {{ selectedExam.question_count }} questions</span>
        </p>
      </div>
    </div>

    <p v-if="loadError" class="error-text">{{ loadError }}</p>

    <div class="actions actions-between">
      <button class="btn-secondary" @click="$emit('back')">← Previous Step</button>
      <button class="btn-primary" :disabled="!canProceed" @click="$emit('next')">Next Step →</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch, onMounted, computed } from 'vue'
import {
  fetchExamTypes,
  fetchExamCategories,
  searchExams,
  fetchExamDetail,
  type ExamType,
  type ExamCategory,
  type ExamSummary,
} from '@/services/mockTestApi'

const props = defineProps<{ modelValue?: Record<string, any> }>()
const emit = defineEmits(['update:modelValue', 'back', 'next'])

// form holds everything ReviewConfirmStep / the final payload needs.
// examId is the resolved Exam PK — this is what actually gets sent to
// POST /api/mockexams/ as `exam`, NOT examSearch (display text only).
const form = reactive({
  examTypeId: '' as number | string,
  categoryId: '' as number | string,
  examId: '' as number | string,
  examSearch: '', // kept for ReviewConfirmStep display
  examYear: '',
  ...props.modelValue,
})

watch(form, (val) => emit('update:modelValue', { ...val }), { deep: true })

const examTypes = ref<ExamType[]>([])
const examCategories = ref<ExamCategory[]>([])
const loadingCategories = ref(false)
const loadError = ref('')

const examSearchText = ref(form.examSearch || '')
const searchResults = ref<ExamSummary[]>([])
const searching = ref(false)
const showResults = ref(false)
const selectedExam = ref<ExamSummary | null>(null)

const years = Array.from({ length: 6 }, (_, i) => 2026 - i)

const canProceed = computed(() => !!form.examTypeId && !!form.categoryId && !!form.examId)

let searchDebounce: ReturnType<typeof setTimeout> | null = null

/** Loads categories for the current examTypeId and the exam preview for
 * the current examId — used both on initial mount and again once the
 * form is hydrated from an async parent fetch (edit mode). */
async function bootstrapFromForm() {
  if (form.examTypeId) {
    // FIX: loadCategories() resets categoryId to '' as a side effect
    // (needed for the "user manually changes exam type" flow), but this
    // function never restored it afterward. That's fine on the watch()
    // path below, which does its own restore — but in edit mode the
    // parent (CreateMockTestView) usually finishes its fetch *before*
    // this component ever mounts, so props.modelValue.examId is already
    // truthy at setup time, hydratedFromParent starts true, and the
    // watch() below never fires. bootstrapFromForm() (called directly
    // from onMounted) was the only thing that ran, and it left
    // categoryId empty — which is exactly why Exam Category showed
    // "Select category" and Next Step stayed disabled. Restoring it
    // here fixes both call paths.
    const restoredCategoryId = form.categoryId
    await loadCategories(form.examTypeId)
    if (restoredCategoryId) form.categoryId = restoredCategoryId
  }
  if (form.examId) {
    try {
      selectedExam.value = await fetchExamDetail(form.examId)
    } catch {
      /* non-fatal — preview just stays empty */
    }
  }
}

onMounted(async () => {
  try {
    examTypes.value = await fetchExamTypes()
  } catch (e: any) {
    loadError.value = 'Could not load exam types. Please try again.'
  }

  // If re-opening the wizard on an existing draft, restore category list
  // and the previously selected exam's preview.
  await bootstrapFromForm()
})

// Edit mode: CreateMockTestView fetches the existing mock test
// asynchronously and only THEN fills in modelValue — but `form` above
// was already built from an empty modelValue at mount time. This
// watcher re-hydrates the form (and re-runs the category/exam-preview
// bootstrap) the moment real data arrives, exactly once, so it never
// overwrites the admin's own selections afterward.
let hydratedFromParent = !!(props.modelValue && props.modelValue.examId)
watch(
  () => props.modelValue,
  async (val) => {
    if (hydratedFromParent || !val) return
    if (val.examId || val.examTypeId) {
      Object.assign(form, val)
      examSearchText.value = form.examSearch || examSearchText.value
      hydratedFromParent = true
      // bootstrapFromForm() now restores categoryId itself after
      // loadCategories() resets it — no need to duplicate that here.
      await bootstrapFromForm()
    }
  },
  { deep: true }
)

async function loadCategories(examTypeId: number | string) {
  loadingCategories.value = true
  form.categoryId = ''
  examCategories.value = []
  try {
    examCategories.value = await fetchExamCategories(examTypeId)
  } catch {
    loadError.value = 'Could not load exam categories. Please try again.'
  } finally {
    loadingCategories.value = false
  }
}

function onExamTypeChange() {
  if (form.examTypeId) loadCategories(form.examTypeId)
}

function onSearchInput() {
  form.examSearch = examSearchText.value
  showResults.value = true

  if (searchDebounce) clearTimeout(searchDebounce)
  if (!examSearchText.value.trim()) {
    searchResults.value = []
    return
  }

  searchDebounce = setTimeout(async () => {
    searching.value = true
    try {
      const { results } = await searchExams({
        search: examSearchText.value.trim(),
        exam_type: form.examTypeId || undefined,
        category_id: form.categoryId || undefined,
      })
      searchResults.value = results
    } catch {
      searchResults.value = []
    } finally {
      searching.value = false
    }
  }, 350)
}

function selectExam(exam: ExamSummary) {
  form.examId = exam.exam_id
  form.examSearch = exam.exam_name
  examSearchText.value = exam.exam_name
  selectedExam.value = exam
  showResults.value = false
  searchResults.value = []
}
</script>

<style scoped>
.card { background: #fff; border: 1px solid #ecedf3; border-radius: 12px; padding: 22px 24px 26px; }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
.card-icon { font-size: 15px; }
.card-head h3 { font-size: 14.5px; margin: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; position: relative; }
.field label { font-size: 12.5px; font-weight: 600; color: #4b4f66; }
.req { color: #ef4444; }
input, select { border: 1px solid #dfe1ea; border-radius: 8px; padding: 9px 12px; font-size: 13px; outline: none; font-family: inherit; width: 100%; background: #fff; }
input:focus, select:focus { border-color: #a78bfa; box-shadow: 0 0 0 3px #ede9fe; }
select:disabled { background: #f6f7fb; color: #a6abc0; cursor: not-allowed; }
.search-input { position: relative; }
.search-input .search-icon { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); font-size: 12px; opacity: 0.55; pointer-events: none; }
.exam-search-field { position: relative; }
.results-dropdown {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 20;
  background: #fff; border: 1px solid #dfe1ea; border-radius: 8px;
  margin-top: 4px; max-height: 220px; overflow-y: auto; list-style: none;
  padding: 4px; box-shadow: 0 8px 24px rgba(20, 18, 31, 0.08);
}
.results-dropdown li {
  display: flex; justify-content: space-between; gap: 10px;
  padding: 8px 10px; border-radius: 6px; cursor: pointer; font-size: 12.5px;
}
.results-dropdown li:hover { background: #f6f7fb; }
.result-name { color: #1f2333; font-weight: 500; }
.result-code { color: #a6abc0; font-size: 11.5px; }
.search-status { position: absolute; top: 100%; left: 0; margin-top: 4px; font-size: 12px; color: #a6abc0; }
.preview-box { display: flex; gap: 10px; background: #f2effe; border: 1px solid #e2dbfb; border-radius: 10px; padding: 14px 16px; margin: 6px 0 24px; }
.preview-box.filled { background: #f5f8ff; border-color: #dce6fb; }
.preview-icon { color: #6d28d9; font-size: 15px; }
.preview-box strong { display: block; font-size: 12.5px; color: #4b3b93; margin-bottom: 3px; }
.preview-box p { margin: 0; font-size: 12px; color: #786fae; }
.preview-details strong { color: #1f2333; }
.preview-details p { color: #6b7080; }
.error-text { color: #dc2626; font-size: 12.5px; margin: 0 0 12px; }
.actions { display: flex; margin-top: 8px; }
.actions-between { justify-content: space-between; }
.btn-primary { background: #6d28d9; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary:hover:not(:disabled) { background: #5b21b6; }
.btn-primary:disabled { background: #d8d5e8; cursor: not-allowed; }
.btn-secondary { background: #fff; color: #4b4f66; border: 1px solid #dfe1ea; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-secondary:hover { background: #f6f7fb; }
</style>