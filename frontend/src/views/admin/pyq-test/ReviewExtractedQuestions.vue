<!-- ReviewExtractedQuestions.vue -->
<!--
  Complete ReviewExtractedQuestions.vue with fixes for:
  - Diagram display in questions and options
  - Proper option extraction and storage
  - Auto-fill missing options
  - Bulk validation
  - Lightbox for diagram viewing
-->

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PYWizardStepper from './PYWizardStepper.vue'
import api from '@/api'
import { pyqImport } from '@/services/pyqImportStore'
import MathRenderer from './MathRenderer.vue'
import AddToTestPanel from './AddToTestPanel.vue'

const router = useRouter()

// ── Tabs / pagination ─────────────────────────────────────────────────────────
const activeTab = ref('all')
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = ref(10)

// ── Loading / error ───────────────────────────────────────────────────────────
const loading = ref(true)
const errorMsg = ref('')
const bulkValidating = ref(false)

// ── Add to Test ────────────────────────────────────────────────────────────────
const selectedQuestions = ref([])
const selectingAll = ref(false) // used by both toggleSelectAll (header checkbox) and selectAllValid (link)

// Selection is a list of question indexes that is NOT tied to the visible page,
// so it survives pagination and tab switches.
const allOnPageSelected = computed(
  () => questions.value.length > 0 && questions.value.every((q) => selectedQuestions.value.includes(q.index)),
)

// Header checkbox = every question matching the CURRENT TAB's filter, across
// all pages (not just the 10 rows currently visible). Fetches the full index
// list from the server (same pattern selectAllValid already used for the
// "valid only" link) rather than just toggling questions.value, which only
// ever holds one page's worth of rows.
async function fetchAllIndexesForCurrentTab() {
  const tab = tabs.find((t) => t.key === activeTab.value)
  const { data } = await api.get(`/pyq-import/${pyqImport.uploadId}/questions/`, {
    params: { status: tab.statusParam, page: 1, page_size: 500 },
  })
  return (data.results || []).map((q) => q.index)
}

async function toggleSelectAll(event) {
  const checked = event.target.checked
  selectingAll.value = true
  try {
    const allIdx = await fetchAllIndexesForCurrentTab()
    if (checked) {
      selectedQuestions.value = [...new Set([...selectedQuestions.value, ...allIdx])]
    } else {
      selectedQuestions.value = selectedQuestions.value.filter((i) => !allIdx.includes(i))
    }
  } catch (e) {
    errorMsg.value = 'Could not select all questions.'
  } finally {
    selectingAll.value = false
  }
}

function toggleSelectQuestion(index) {
  const i = selectedQuestions.value.indexOf(index)
  if (i === -1) selectedQuestions.value.push(index)
  else selectedQuestions.value.splice(i, 1)
}

function clearSelection() {
  selectedQuestions.value = []
}

// Select every VALID question across all pages in one click.
async function selectAllValid() {
  selectingAll.value = true
  try {
    const { data } = await api.get(`/pyq-import/${pyqImport.uploadId}/questions/`, {
      params: { status: 'valid', page: 1, page_size: 500 },
    })
    const idx = (data.results || []).map((q) => q.index)
    selectedQuestions.value = [...new Set([...selectedQuestions.value, ...idx])]
  } catch (e) {
    errorMsg.value = 'Could not select all valid questions.'
  } finally {
    selectingAll.value = false
  }
}

// ── Add to Test (side action — does NOT leave this step) ───────────────────────
// Opens a drawer that shows the selected questions grouped by Subject/Chapter
// and calls POST /pyq-import/<id>/add-to-test/, which saves each question to the
// bank once and makes it available for Practice + Custom (and, later, Mock) in
// that same call — no more picking Practice vs Custom first. The wizard state is
// untouched, so "Next: Create Test" (the PYQ test) stays available before or after.
const panelOpen = ref(false)

function openAddToTest() {
  if (selectedQuestions.value.length === 0) {
    errorMsg.value = 'Select at least one question first.'
    return
  }
  panelOpen.value = true
}

const toast = ref('')
let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 8000)
}

async function onAddedToTest(result) {
  const parts = [`✅ ${result.practice_added} question${result.practice_added === 1 ? '' : 's'} added`]
  if (result.practice_duplicates) parts.push(`${result.practice_duplicates} already added previously`)
  if (result.skipped_not_valid) parts.push(`${result.skipped_not_valid} skipped (need review)`)
  if (result.skipped_unmapped) parts.push(`${result.skipped_unmapped} skipped (no chapter)`)
  showToast(parts.join(' · '))
  selectedQuestions.value = []
  await loadQuestions() // refresh the Added ✓ badges
}

// ── Question data ─────────────────────────────────────────────────────────────
const questions = ref([])

// ── Summary stats ─────────────────────────────────────────────────────────────
const stats = reactive({ totalExtracted: 0, valid: 0, needsReview: 0, failed: 0, addedPractice: 0, addedCustom: 0 })

// ── Lightbox ──────────────────────────────────────────────────────────────────
const lightboxSrc = ref('')
const lightboxOpen = ref(false)

function openLightbox(src) {
  lightboxSrc.value = src
  lightboxOpen.value = true
}

function closeLightbox() {
  lightboxOpen.value = false
}

// ── Tabs meta ─────────────────────────────────────────────────────────────────
const tabs = [
  { key: 'all', label: 'All Questions', statusParam: 'all' },
  { key: 'valid', label: 'Valid', statusParam: 'valid' },
  { key: 'review', label: 'Needs Review', statusParam: 'needs_review' },
  { key: 'failed', label: 'Failed', statusParam: 'failed' },
]

function tabCount(key) {
  if (key === 'all') return stats.totalExtracted
  if (key === 'valid') return stats.valid
  if (key === 'review') return stats.needsReview
  return stats.failed
}

const statusLabels = { valid: 'Valid', needs_review: 'Needs Review', failed: 'Failed' }
const statusStyles = {
  valid: 'bg-emerald-50 text-emerald-600',
  needs_review: 'bg-amber-50 text-amber-600',
  failed: 'bg-red-50 text-red-500',
}

// ── Image URL resolution ──────────────────────────────────────────────────────
// CHANGED: VITE_API_BASE_URL commonly includes a path segment for the API
// itself (e.g. "https://backend:8000/api"). Media files are served from
// the site root ("/media/..."), NOT under that API path — concatenating
// the full base URL onto a relative image path produced
// ".../api/media/..." and 404'd. Use only the origin (scheme + host +
// port) for image URLs, which strips any trailing path automatically
// regardless of how VITE_API_BASE_URL is configured.
const API_BASE_RAW = (import.meta.env.VITE_API_BASE_URL || '').trim()

function getBackendOrigin() {
  if (!API_BASE_RAW) return ''
  try {
    return new URL(API_BASE_RAW, window.location.origin).origin
  } catch {
    // Fallback for a malformed/relative value — best effort, strip any path.
    return API_BASE_RAW.replace(/\/$/, '').split('/').slice(0, 3).join('/')
  }
}

const BACKEND_ORIGIN = getBackendOrigin()

function resolveImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return BACKEND_ORIGIN + (url.startsWith('/') ? url : '/' + url)
}

// ── Math strip helper (list preview) ─────────────────────────────────────────
function stripLatexDelimiters(text) {
  if (!text) return ''
  let clean = text
    .replace(/\\\(/g, '')
    .replace(/\\\)/g, '')
    .replace(/\\\[/g, '')
    .replace(/\\\]/g, '')
  if (clean.length > 80) clean = clean.substring(0, 80) + '…'
  return clean
}

function getPlainPreview(q) {
  if (q.preview) return stripLatexDelimiters(q.preview)
  if (q.question_text) return stripLatexDelimiters(q.question_text)
  return 'No preview available'
}

// ── Load list ─────────────────────────────────────────────────────────────────
async function loadQuestions() {
  if (!pyqImport.uploadId) return
  loading.value = true
  errorMsg.value = ''
  try {
    const tab = tabs.find((t) => t.key === activeTab.value)
    const { data } = await api.get(`/pyq-import/${pyqImport.uploadId}/questions/`, {
      params: {
        status: tab.statusParam,
        page: currentPage.value,
        page_size: pageSize.value,
      },
    })

    questions.value = (data.results || []).map((q) => ({
      ...q,
      option_a: q.option_a || q.options?.A || '',
      option_b: q.option_b || q.options?.B || '',
      option_c: q.option_c || q.options?.C || '',
      option_d: q.option_d || q.options?.D || '',
      option_e: q.option_e || q.options?.E || '',
      images: q.images || [],
      option_images: q.option_images || { A: null, B: null, C: null, D: null },
      hasImages: !!(q.images && q.images.length) || 
                  Object.values(q.option_images || {}).some(v => v),
    }))

    totalPages.value = data.totalPages || 1
    if (data.summary) {
      Object.assign(stats, data.summary)
      // keep the store fresh so the final "Review & Confirm" step shows real counts
      pyqImport.summary = { ...(pyqImport.summary || {}), ...data.summary }
    }
  } catch (e) {
    errorMsg.value = 'Could not load extracted questions.'
    console.error('Load questions error:', e)
  } finally {
    loading.value = false
  }
}

// NOTE: Math rendering is handled per-item by the <MathRenderer> component
// (used in the list preview, modal question text, and modal option previews).
// A previous version of this function called KaTeX's global
// `renderMathInElement(document.body, ...)` after every list/modal load.
// That mutates the DOM outside of Vue's control across the *entire* page,
// which corrupts Vue's internal vnode tracking on elements it still owns and
// throws "Cannot set properties of null (setting '__vnode')" /
// "Cannot read properties of null (reading 'type')" the next time Vue
// patches or unmounts those nodes (e.g. on tab switch). Do not reintroduce
// a document-wide renderMathInElement call here — if something needs KaTeX
// rendering outside <MathRenderer>, scope it to that element's own ref,
// never to document.body.

onMounted(() => {
  if (!pyqImport.uploadId) {
    router.replace({ name: 'admin-tests-previous-upload' })
    return
  }
  loadQuestions()
})

watch(activeTab, () => {
  currentPage.value = 1
  loadQuestions()
})
watch(currentPage, loadQuestions)

// ── Modal state ───────────────────────────────────────────────────────────────
const modalOpen = ref(false)
const modalLoading = ref(false)
const modalSaving = ref(false)
const modalError = ref('')

const editing = reactive({
  index: null,
  question_number: null,
  question_text: '',
  question_type: 'MCQ',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  option_e: '',
  correct_answer: '',
  status: '',
  status_reason: '',
  images: [],
  option_images: { a: null, b: null, c: null, d: null },
})

// ── Open / save modal ─────────────────────────────────────────────────────────
async function openQuestion(index) {
  modalOpen.value = true
  modalLoading.value = true
  modalError.value = ''
  try {
    const { data } = await api.get(`/pyq-import/${pyqImport.uploadId}/questions/${index}/`)
    console.log('Question data:', data) // Debug log

    editing.index = data.index
    editing.question_number = data.questionNumber ?? data.question_number
    editing.question_text = data.question_text || ''
    editing.question_type = data.question_type || 'MCQ'

    // Options – accept both flat and nested formats
    editing.option_a = data.option_a ?? data.options?.A ?? ''
    editing.option_b = data.option_b ?? data.options?.B ?? ''
    editing.option_c = data.option_c ?? data.options?.C ?? ''
    editing.option_d = data.option_d ?? data.options?.D ?? ''
    editing.option_e = data.option_e ?? data.options?.E ?? ''

    editing.correct_answer = data.correct_answer || ''
    editing.status = data.status || 'needs_review'
    editing.status_reason = data.status_reason || ''

    // Images
    editing.images = (data.images || []).map(resolveImageUrl)

    const rawOptImgs = data.option_images || {}
    editing.option_images = {
      a: resolveImageUrl(rawOptImgs.a || rawOptImgs.A || null),
      b: resolveImageUrl(rawOptImgs.b || rawOptImgs.B || null),
      c: resolveImageUrl(rawOptImgs.c || rawOptImgs.C || null),
      d: resolveImageUrl(rawOptImgs.d || rawOptImgs.D || null),
    }
  } catch (e) {
    modalError.value = 'Could not load this question.'
    console.error('Load question error:', e)
  } finally {
    modalLoading.value = false
  }
}

async function saveQuestion() {
  modalSaving.value = true
  modalError.value = ''
  try {
    const payload = {
      question_text: editing.question_text,
      option_a: editing.option_a,
      option_b: editing.option_b,
      option_c: editing.option_c,
      option_d: editing.option_d,
      option_e: editing.option_e || '',
      correct_answer: editing.correct_answer.toUpperCase().trim(),
    }

    console.log('Saving payload:', payload) // Debug log

    await api.patch(`/pyq-import/${pyqImport.uploadId}/questions/${editing.index}/`, payload)
    modalOpen.value = false
    await loadQuestions()
  } catch (e) {
    modalError.value = e?.response?.data?.error || 'Could not save this question.'
    console.error('Save question error:', e)
  } finally {
    modalSaving.value = false
  }
}

// ── Auto-fill missing options ────────────────────────────────────────────────
function autoFillOptions() {
  const optionLetters = ['a', 'b', 'c', 'd']
  let filled = 0

  for (const letter of optionLetters) {
    if (!editing[`option_${letter}`]) {
      // Try to find the option in the question text or raw content
      // Look for patterns like "A. text", "A) text", "(A) text"
      const patterns = [
        new RegExp(`${letter.toUpperCase()}\\.\\s*([^\\n]+)`, 'i'),
        new RegExp(`${letter.toUpperCase()}\\)\\s*([^\\n]+)`, 'i'),
        new RegExp(`\\(${letter.toUpperCase()}\\)\\s*([^\\n]+)`, 'i'),
      ]
      
      for (const pattern of patterns) {
        const match = editing.question_text.match(pattern)
        if (match) {
          editing[`option_${letter}`] = match[1].trim()
          filled++
          break
        }
      }
    }
  }

  // Re-check if all options are now filled
  const allFilled = optionLetters.every((letter) => editing[`option_${letter}`])
  if (allFilled && !editing.correct_answer) {
    // If all options filled but no answer, try to infer from common patterns
    // Look for "Answer: X" or "Ans: X" in the text
    const ansPatterns = [
      /(?:Answer|Ans|Correct)\s*[:]\s*\(?([A-D])\)?/i,
      /(?:Answer|Ans|Correct)\s*[:]\s*([A-D])/i,
    ]
    for (const pattern of ansPatterns) {
      const match = editing.question_text.match(pattern)
      if (match) {
        editing.correct_answer = match[1].toUpperCase()
        break
      }
    }
  }

  modalError.value = filled > 0 ? `Auto-filled ${filled} option(s). Please verify.` : 'No options could be auto-filled.'
}

// ── Bulk validate ─────────────────────────────────────────────────────────────
async function bulkValidate() {
  if (!confirm('This will mark all questions with at least one option as valid. Continue?')) {
    return
  }

  bulkValidating.value = true
  errorMsg.value = ''
  
  try {
    // Get all question indices that need review
    const reviewQuestions = questions.value.filter(
      (q) => q.status === 'needs_review' || q.status === 'failed'
    )
    
    const questionIds = reviewQuestions.map((q) => q.index)
    
    if (questionIds.length === 0) {
      errorMsg.value = 'No questions to validate.'
      bulkValidating.value = false
      return
    }

    const { data } = await api.post(`/pyq-import/${pyqImport.uploadId}/bulk-validate/`, {
      question_ids: questionIds,
    })

    await loadQuestions()
    showToast(`✅ ${data.validated_count} question${data.validated_count === 1 ? '' : 's'} validated successfully.`)
  } catch (e) {
    errorMsg.value = e?.response?.data?.error || 'Bulk validation failed. Please try again.'
    console.error('Bulk validate error:', e)
  } finally {
    bulkValidating.value = false
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────
function goNext() {
  if (stats.valid === 0) {
    errorMsg.value = 'Please review and validate at least one question before proceeding.'
    return
  }
  router.push({ name: 'admin-tests-previous-review-create' })
}

function goBack() {
  router.push({ name: 'admin-tests-previous-map-paper-details' })
}
</script>

<template>
  <div class="p-6">
    <PYWizardStepper :current-step="3" />

    <div class="mx-auto max-w-5xl">
      <h3 class="text-base font-semibold text-gray-900">Review Extracted Questions</h3>
      <p class="mt-1 text-xs text-gray-500">
        We extracted {{ stats.totalExtracted }} questions from your PDF.
        Questions with diagrams show a 📷 badge — open them to see the image.
      </p>

      <!-- Add-to-Test result -->
      <div
        v-if="toast"
        class="mt-3 flex items-start justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700"
      >
        <span>{{ toast }}</span>
        <button class="text-emerald-400 hover:text-emerald-700" @click="toast = ''">✕</button>
      </div>

      <!-- ── Stat cards ─────────────────────────────────────────────────── -->
      <div class="mt-5 grid grid-cols-4 gap-4">
        <!-- Total -->
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs text-gray-500">Total Extracted</p>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-50 text-[#6C4CF1]">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </span>
          </div>
          <p class="text-2xl font-semibold text-gray-900">{{ stats.totalExtracted }}</p>
        </div>
        <!-- Valid -->
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs text-gray-500">Valid Questions</p>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="8 12 11 15 16 9"/>
              </svg>
            </span>
          </div>
          <p class="text-2xl font-semibold text-gray-900">{{ stats.valid }}</p>
        </div>
        <!-- Needs Review -->
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs text-gray-500">Needs Review</p>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-500">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </span>
          </div>
          <p class="text-2xl font-semibold text-gray-900">{{ stats.needsReview }}</p>
        </div>
        <!-- Failed -->
        <div class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs text-gray-500">Failed</p>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 text-red-500">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            </span>
          </div>
          <p class="text-2xl font-semibold text-gray-900">{{ stats.failed }}</p>
        </div>
      </div>

      <!-- ── Question table ─────────────────────────────────────────────── -->
      <div class="mt-5 rounded-xl border border-gray-200 bg-white">
        <!-- Tab bar -->
        <div class="flex items-center justify-between border-b border-gray-100 px-5 py-3">
          <div class="flex items-center gap-1">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              class="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              :class="activeTab === tab.key ? 'bg-violet-50 text-[#6C4CF1]' : 'text-gray-500 hover:bg-gray-50'"
            >
              {{ tab.label }} <span class="ml-0.5">({{ tabCount(tab.key) }})</span>
            </button>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="stats.needsReview > 0 || stats.failed > 0"
              @click="bulkValidate"
              :disabled="bulkValidating"
              class="rounded-lg bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-600 hover:bg-amber-100 disabled:opacity-50"
            >
              {{ bulkValidating ? 'Validating...' : '⚡ Bulk Validate' }}
            </button>

            <!-- Add to Test — one click, no Practice/Custom choice: saves to the
                 bank once and makes the selection available for Practice + Custom
                 (and Mock, once the test is created) in that same call. -->
            <button
              @click="openAddToTest"
              :disabled="selectedQuestions.length === 0"
              class="flex items-center gap-1.5 rounded-lg border border-[#6C4CF1] px-3 py-1.5 text-xs font-medium text-[#6C4CF1] hover:bg-violet-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="16"/>
                <line x1="8" y1="12" x2="16" y2="12"/>
              </svg>
              Add to Test
            </button>
          </div>
        </div>

        <!-- States -->
        <div v-if="loading" class="px-5 py-8 text-center text-xs text-gray-400">Loading questions…</div>
        <p v-else-if="errorMsg" class="px-5 py-8 text-center text-xs text-red-500">
          {{ errorMsg }}
        </p>

        <!-- Selection bar -->
        <div
          v-if="selectedQuestions.length > 0 && !loading"
          class="flex items-center gap-3 border-b border-violet-100 bg-violet-50 px-5 py-2.5"
        >
          <span class="text-xs font-medium text-[#6C4CF1]">{{ selectedQuestions.length }} questions selected</span>
          <button @click="clearSelection" class="text-xs text-gray-400 underline underline-offset-2 hover:text-gray-600">
            Clear Selection
          </button>
          <button
            v-if="selectedQuestions.length < stats.valid"
            @click="selectAllValid"
            :disabled="selectingAll"
            class="text-xs text-[#6C4CF1] underline underline-offset-2 hover:text-[#5B3EE0] disabled:opacity-50"
          >
            {{ selectingAll ? 'Selecting…' : `Select all ${stats.valid} valid` }}
          </button>
        </div>

        <!-- Table -->
        <table v-if="!loading" class="w-full text-left text-xs">
          <thead>
            <tr class="border-b border-gray-100 text-gray-400">
              <th class="px-5 py-2.5 font-medium w-10">
                <input
                  ref="selectAllCheckbox"
                  type="checkbox"
                  class="h-4 w-4 rounded accent-[#6C4CF1]"
                  :checked="allOnPageSelected"
                  :disabled="selectingAll"
                  @change="toggleSelectAll"
                />
              </th>
              <th class="px-3 py-2.5 font-medium w-16">Q. No.</th>
              <th class="px-5 py-2.5 font-medium">Preview</th>
              <th class="px-5 py-2.5 font-medium w-28">Status</th>
              <th class="px-5 py-2.5 font-medium text-right w-28">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="q in questions"
              :key="q.index"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50"
              :class="selectedQuestions.includes(q.index) ? 'bg-violet-50/40' : ''"
            >
              <td class="px-5 py-3.5">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded accent-[#6C4CF1]"
                  :checked="selectedQuestions.includes(q.index)"
                  @change="toggleSelectQuestion(q.index)"
                />
              </td>
              <td class="px-3 py-3.5 text-gray-500">{{ q.questionNumber ?? q.index }}</td>

              <!-- Preview cell: text + optional diagram badge -->
              <td class="px-5 py-3.5 text-gray-700">
                <div class="flex items-start gap-2">
                  <span class="flex-1">
                    <MathRenderer :content="getPlainPreview(q)" />
                  </span>
                  <span
                    v-if="q.hasImages"
                    class="shrink-0 rounded-full bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-500"
                    title="This question has diagram(s)"
                  >📷</span>
                </div>
                <span class="mt-0.5 inline-block rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-medium text-[#6C4CF1]">
                  {{ q.question_type || 'MCQ' }}
                </span>
                <span
                  v-if="q.chapter_name"
                  class="ml-1 mt-0.5 inline-block rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="q.mapping_source === 'ai' ? 'bg-purple-50 text-purple-700 border border-purple-200' : 'bg-blue-50 text-blue-700'"
                  :title="q.mapping_source === 'ai' ? `AI Auto-Mapped (${q.mapping_confidence || 75}%)` : (q.mapping_source === 'rules' ? 'Rule Match' : 'Chapter')"
                >
                  <span v-if="q.mapping_source === 'ai'">🤖 </span>
                  <span v-else-if="q.mapping_source === 'rules'">⚡ </span>
                  <span v-else>📚 </span>
                  {{ q.chapter_name }}
                </span>
                <!-- where this question has already been added -->
                <span
                  v-if="(q.added_to || []).includes('practice')"
                  class="ml-1 mt-0.5 inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-600"
                >Practice ✓</span>
                <span
                  v-if="(q.added_to || []).includes('custom')"
                  class="ml-1 mt-0.5 inline-block rounded-full bg-sky-50 px-2 py-0.5 text-[10px] font-medium text-sky-600"
                >Custom ✓</span>
              </td>

              <td class="px-5 py-3.5">
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="statusStyles[q.status] || 'bg-gray-50 text-gray-500'"
                >
                  {{ statusLabels[q.status] || q.status }}
                </span>
              </td>
              <td class="px-5 py-3.5 text-right">
                <button
                  class="rounded-lg px-3 py-1 text-[11px] font-medium"
                  :class="q.status === 'valid'
                    ? 'text-[#6C4CF1] hover:underline'
                    : 'border border-amber-200 text-amber-600 hover:bg-amber-50'"
                  @click="openQuestion(q.index)"
                >
                  {{ q.status === 'valid' ? 'View' : 'Review' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="flex items-center justify-between border-t border-gray-100 px-5 py-3">
          <p class="text-[11px] text-gray-400">Page {{ currentPage }} of {{ totalPages }}</p>
          <div class="flex items-center gap-1 text-xs">
            <button
              class="rounded px-2 py-1 text-gray-400 disabled:opacity-30"
              :disabled="currentPage <= 1"
              @click="currentPage--"
            >&lt;</button>
            <button
              class="rounded px-2 py-1 text-gray-400 disabled:opacity-30"
              :disabled="currentPage >= totalPages"
              @click="currentPage++"
            >&gt;</button>
          </div>
        </div>
      </div>

      <!-- Navigation buttons -->
      <div class="mt-6 flex items-center justify-between">
        <p v-if="selectedQuestions.length > 0" class="text-[11px] text-gray-500">
          Selected: <span class="font-semibold text-[#6C4CF1]">{{ selectedQuestions.length }} questions</span>
          <button @click="clearSelection" class="ml-2 text-gray-400 underline underline-offset-2 hover:text-gray-600">Clear</button>
        </p>
        <p v-else class="text-[11px] text-gray-400">
          Adding to Practice / Custom is optional — you can create the PYQ test at any time.
        </p>
        <div class="flex gap-3">
          <button
            class="rounded-lg border border-gray-200 px-4 py-2.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
            @click="goBack"
          >
            ← Back
          </button>
          <button
            class="rounded-lg px-4 py-2.5 text-xs font-semibold text-white shadow-sm"
            :class="stats.valid > 0 ? 'bg-[#6C4CF1] hover:bg-[#5B3EE0]' : 'bg-gray-300 cursor-not-allowed'"
            :disabled="stats.valid === 0"
            @click="goNext"
          >
            Next: Create Test →
          </button>
        </div>
      </div>
      <p v-if="stats.valid === 0 && !loading" class="mt-2 text-[11px] text-amber-500 text-right">
        ⚠️ Please review and validate at least one question to continue
      </p>
    </div>

    <!-- Add to Test drawer -->
    <AddToTestPanel
      :open="panelOpen"
      :indexes="selectedQuestions"
      @close="panelOpen = false"
      @added="onAddedToTest"
    />

    <!-- ═══════════════════════════════════════════════════════════════════
         MODAL — view / edit a single question
         ════════════════════════════════════════════════════════════════ -->
    <div
      v-if="modalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      @click.self="modalOpen = false"
    >
      <div class="relative w-full max-w-3xl rounded-xl bg-white shadow-xl max-h-[92vh] flex flex-col">
        <!-- Sticky header -->
        <div class="flex items-center justify-between border-b border-gray-100 px-6 py-4 shrink-0">
          <div class="flex items-center gap-3">
            <h4 class="text-sm font-semibold text-gray-900">
              Question {{ editing.question_number ?? editing.index }}
            </h4>
            <span
              class="rounded-full px-2 py-0.5 text-[10px] font-medium"
              :class="statusStyles[editing.status] || 'bg-gray-50 text-gray-500'"
            >
              {{ statusLabels[editing.status] || editing.status }}
            </span>
          </div>
          <button @click="modalOpen = false" class="text-gray-400 hover:text-gray-700">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Scrollable body -->
        <div class="overflow-y-auto flex-1 px-6 py-5">
          <div v-if="modalLoading" class="py-10 text-center text-xs text-gray-400">Loading…</div>

          <template v-else>
            <div class="space-y-5">
              <!-- ── 1. QUESTION TEXT ──────────────────────────────────── -->
              <div>
                <label class="mb-1 block text-[11px] font-medium text-gray-500">Question Text</label>
                <textarea
                  v-model="editing.question_text"
                  rows="4"
                  class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-[#6C4CF1]"
                  style="font-family: 'Times New Roman', serif;"
                />
                <div class="mt-1 text-[11px] text-gray-400 leading-relaxed">
                  Preview: <MathRenderer :content="editing.question_text" />
                </div>
              </div>

              <!-- ── 2. QUESTION DIAGRAM(S) ─────────────────────────────── -->
              <div v-if="editing.images && editing.images.length" class="space-y-2">
                <p class="text-[11px] font-semibold text-gray-500 uppercase tracking-wide">
                  Question Diagram{{ editing.images.length > 1 ? 's' : '' }}
                </p>
                <div class="flex flex-wrap gap-3">
                  <div
                    v-for="(imgUrl, idx) in editing.images"
                    :key="idx"
                    class="group relative cursor-zoom-in overflow-hidden rounded-lg border border-gray-200 bg-gray-50 transition hover:border-[#6C4CF1]"
                    @click="openLightbox(imgUrl)"
                  >
                    <img
                      :src="imgUrl"
                      :alt="`Question diagram ${idx + 1}`"
                      class="max-h-52 max-w-xs object-contain p-1"
                      loading="lazy"
                      @error="$event.target.closest('div').style.display='none'"
                    />
                    <div class="absolute inset-0 hidden items-center justify-center bg-black/10 group-hover:flex">
                      <span class="rounded bg-black/40 px-2 py-0.5 text-[10px] text-white">
                        Click to enlarge
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- ── OPTIONS (A–D) with per-option diagram ─────────────── -->
              <div class="grid grid-cols-2 gap-4">
                <div
                  v-for="opt in ['a', 'b', 'c', 'd']"
                  :key="opt"
                  class="rounded-lg border border-gray-100 bg-gray-50/50 p-3"
                >
                  <label class="mb-1 block text-[11px] font-medium text-gray-500">
                    Option {{ opt.toUpperCase() }}
                  </label>

                  <!-- Option diagram — shown when image exists -->
                  <div
                    v-if="editing.option_images[opt]"
                    class="mb-2 cursor-zoom-in overflow-hidden rounded-lg border border-gray-200 bg-white"
                    @click="openLightbox(editing.option_images[opt])"
                  >
                    <img
                      :src="editing.option_images[opt]"
                      :alt="`Option ${opt.toUpperCase()} diagram`"
                      class="max-h-36 w-full object-contain p-2"
                      loading="lazy"
                      @error="$event.target.closest('div').style.display='none'"
                    />
                    <p class="pb-1 text-center text-[9px] text-gray-400">Click to enlarge</p>
                  </div>

                  <!--
                    Option text input:
                    - Show ALWAYS when there is NO image (pure-text option)
                    - Show ONLY when text is already present alongside an image
                    - Hide (show "+ Add text" link instead) when image exists but text is empty
                  -->
                  <template v-if="!editing.option_images[opt] || editing[`option_${opt}`]">
                    <input
                      v-model="editing[`option_${opt}`]"
                      type="text"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-[#6C4CF1]"
                      style="font-family: 'Times New Roman', serif;"
                      :placeholder="`Enter option ${opt.toUpperCase()}`"
                    />
                    <div v-if="editing[`option_${opt}`]" class="mt-0.5 text-[11px] text-gray-400 leading-relaxed">
                      Preview: <MathRenderer :content="editing[`option_${opt}`]" />
                    </div>
                  </template>

                  <!-- Image-only option: offer a link to add a text label if needed -->
                  <button
                    v-else
                    type="button"
                    class="mt-1 text-[10px] text-gray-400 hover:text-[#6C4CF1] underline underline-offset-2"
                    @click="editing[`option_${opt}`] = ''"
                  >
                    + Add text label
                  </button>
                </div>
              </div>

              <!-- ── CORRECT ANSWER ───────────────────────────────────── -->
              <div>
                <label class="mb-1 block text-[11px] font-medium text-gray-500">Correct Answer</label>
                <input
                  v-model="editing.correct_answer"
                  type="text"
                  maxlength="1"
                  class="w-16 rounded-lg border border-gray-200 px-3 py-2 text-sm uppercase text-center outline-none focus:border-[#6C4CF1]"
                  placeholder="?"
                  @input="editing.correct_answer = editing.correct_answer.toUpperCase()"
                />
                <p class="mt-1 text-[10px] text-gray-400">Enter A, B, C or D</p>
              </div>
            </div><!-- /space-y-5 -->

            <p v-if="modalError" class="mt-3 text-xs" :class="modalError.includes('Auto-filled') ? 'text-blue-500' : 'text-red-500'">
              {{ modalError }}
            </p>
          </template>
        </div>

        <!-- Sticky footer -->
        <div class="flex justify-end gap-2 border-t border-gray-100 px-6 py-4 shrink-0">
          <button
            class="rounded-lg border border-gray-200 px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50"
            @click="modalOpen = false"
          >
            Cancel
          </button>
          <button
            class="rounded-lg bg-[#6C4CF1] px-4 py-2 text-xs font-semibold text-white hover:bg-[#5B3EE0] disabled:opacity-60"
            :disabled="modalSaving || modalLoading"
            @click="saveQuestion"
          >
            {{ modalSaving ? 'Saving…' : 'Save Changes' }}
          </button>
        </div>
      </div><!-- /modal card -->
    </div><!-- /modal backdrop -->

    <!-- ── Lightbox ─────────────────────────────────────────────────────── -->
    <div
      v-if="lightboxOpen"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4"
      @click.self="closeLightbox"
    >
      <div class="relative max-w-4xl max-h-[90vh] overflow-auto">
        <button
          class="absolute -right-3 -top-3 flex h-8 w-8 items-center justify-center rounded-full bg-white text-gray-700 shadow hover:bg-gray-100"
          @click="closeLightbox"
        >
          ✕
        </button>
        <img :src="lightboxSrc" alt="Diagram" class="rounded-lg object-contain max-h-[85vh]" />
      </div>
    </div>
  </div><!-- /p-6 -->
</template>

<style scoped>
/* Fix font issues */
textarea,
input[type="text"] {
  font-family: 'Times New Roman', 'Computer Modern', serif !important;
  font-style: normal !important;
}

/* Math rendering container */
.math-content .katex .mathnormal {
  font-style: italic !important;
}

.math-content:not(:has(.katex)) {
  font-family: 'Times New Roman', serif !important;
  font-style: normal !important;
}

/* Modal image hover */
.group:hover .group-hover\:flex {
  display: flex !important;
}

/* Scrollable modal body */
.flex-1.overflow-y-auto {
  scroll-behavior: smooth;
}

/* Custom scrollbar */
.flex-1.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.flex-1.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.flex-1.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.flex-1.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>