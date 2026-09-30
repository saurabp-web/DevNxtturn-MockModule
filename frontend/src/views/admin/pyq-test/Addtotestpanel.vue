<!-- AddToTestPanel.vue -->
<!--
  Side drawer opened from "Review Extracted Questions" -> Add to Test.

  It is NOT a wizard step, and there is no Practice-vs-Custom choice to make
  here anymore: it shows the selected questions grouped by Subject -> Chapter
  (auto-mapped at upload time, editable here) and, on submit, calls
      POST /pyq-import/<uploadId>/add-to-test/
  which writes each question to the bank ONCE and makes it available
  everywhere in one shot — Practice (chapter-driven, automatic), Custom (this
  exam's single running "Imported Questions" test), and Mock, which is picked
  up independently whenever the wizard's own step 4 "Create Test" runs.
  Afterwards the drawer closes and the admin is back on the review list with
  the wizard state untouched, so "Next: Create Test" (PYQ test) stays available.
-->
<script setup>
import { ref, reactive, computed, watch } from 'vue'
import api from '@/api'
import { pyqImport } from '@/services/pyqImportStore'
import MathRenderer from './MathRenderer.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  indexes: { type: Array, default: () => [] }, // selected question indexes
})
const emit = defineEmits(['close', 'added'])

// ── State ────────────────────────────────────────────────────────────
const loading = ref(false)
const submitting = ref(false)
const errorMsg = ref('')

const rows = ref([]) // valid questions only
const skippedNotValid = ref(0)

// ── Load selected questions each time the drawer opens ─────────────────
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) load()
  },
)

async function load() {
  loading.value = true
  errorMsg.value = ''
  rows.value = []
  skippedNotValid.value = 0
  try {
    const id = pyqImport.uploadId
    const { data } = await api.get(`/pyq-import/${id}/questions/`, {
      params: { indexes: props.indexes.join(','), page_size: 500 },
    })
    // Deduplicate by index — the paginated endpoint can occasionally return
    // the same question twice when the indexes param straddles a page boundary.
    const seen = new Set()
    const all = (data.results || []).filter((q) => {
      if (seen.has(q.index)) return false
      seen.add(q.index)
      return true
    })
    rows.value = all.filter((q) => q.status === 'valid')
    skippedNotValid.value = all.length - rows.value.length

    preloadChapters()
  } catch (e) {
    errorMsg.value = e?.response?.data?.error || 'Could not load the selected questions.'
  } finally {
    loading.value = false
  }
}

// ── Group: Subject -> Chapter ─────────────────────────────────────────
const groups = computed(() => {
  const bySubject = new Map()
  for (const q of rows.value) {
    const subject = q.subject || 'No subject'
    if (!bySubject.has(subject)) bySubject.set(subject, new Map())
    const chapters = bySubject.get(subject)
    const key = q.chapter_id || 0
    if (!chapters.has(key)) {
      chapters.set(key, {
        chapterId: q.chapter_id || null,
        chapterName: q.chapter_name || 'Not mapped to a chapter',
        items: [],
      })
    }
    chapters.get(key).items.push(q)
  }
  return [...bySubject.entries()].map(([subject, chapters]) => {
    const list = [...chapters.values()].sort(
      // unmapped first so they can't be missed
      (a, b) => Number(!!a.chapterId) - Number(!!b.chapterId) || a.chapterName.localeCompare(b.chapterName),
    )
    return { subject, count: list.reduce((n, c) => n + c.items.length, 0), chapters: list }
  })
})

const unmappedCount = computed(() => rows.value.filter((q) => !q.chapter_id).length)
// "Already added" now means already added everywhere (practice+custom) —
// there's only one add action, so a question is either fully new or a
// full duplicate of a previous import.
const alreadyAddedCount = computed(
  () => rows.value.filter((q) => (q.added_to || []).includes('practice') && (q.added_to || []).includes('custom'))
    .length,
)

// ── Chapter dropdown data ──────────────────────────────────────────────
// Pulled straight from the Chapter model via a dedicated endpoint that
// resolves the subject the SAME way the backend auto-mapper does
// (_find_subject, incl. the maths/math synonym handling) — so this never
// drifts out of sync with whatever chapters the classifier itself sees,
// and no client-side subject-name normalisation/matching is needed here.
const chaptersBySubject = reactive({})
const chaptersLoading = reactive({})

function subjectKey(name) {
  return String(name || '').trim().toLowerCase()
}

async function ensureChaptersLoaded(q) {
  if (!q?.subject) return
  const key = subjectKey(q.subject)
  if (chaptersBySubject[key] || chaptersLoading[key]) return
  chaptersLoading[key] = true
  try {
    const { data } = await api.get(
      `/pyq-import/${pyqImport.uploadId}/chapters-for-subject/`,
      { params: { subject: q.subject } },
    )
    chaptersBySubject[key] = data.chapters || []
  } catch (e) {
    console.error('Could not load chapters for', q.subject, e)
    // leave it unset so a later retry (e.g. re-opening the select) tries again
  } finally {
    delete chaptersLoading[key]
  }
}

async function preloadChapters() {
  const seen = new Set()
  for (const q of rows.value) {
    const k = subjectKey(q.subject)
    if (q.subject && !seen.has(k)) {
      seen.add(k)
      await ensureChaptersLoaded(q)
    }
  }
}

function chapterOptions(q) {
  const list = chaptersBySubject[subjectKey(q.subject)] || []
  if (q.chapter_id && !list.some((c) => Number(c.chapter_id) === Number(q.chapter_id))) {
    return [{ chapter_id: q.chapter_id, chapter_name: q.chapter_name || `Chapter ${q.chapter_id}` }, ...list]
  }
  return list
}

async function changeChapter(q, event) {
  const chapterId = Number(event.target.value)
  if (!chapterId) return
  errorMsg.value = ''
  try {
    const { data } = await api.patch(
      `/pyq-import/${pyqImport.uploadId}/questions/${q.index}/chapter/`,
      { chapter_id: chapterId },
    )
    q.chapter_id = data.chapter_id
    q.chapter_name = data.chapter_name
    q.mapping_status = data.mapping_status || 'mapped'
  } catch (e) {
    errorMsg.value = e?.response?.data?.error || 'Could not update the chapter.'
  }
}

// ── Preview text (list preview is cut at 120 chars, so strip delimiters) ─
function preview(q) {
  const t = String(q.preview || '').replace(/\\\(|\\\)|\\\[|\\\]/g, '')
  return t.length > 90 ? t.slice(0, 90) + '…' : t
}

// ── Submit ────────────────────────────────────────────────────────────
// All valid questions can be added to the test. Questions mapped to a chapter
// will be assigned to that chapter; questions without a chapter are automatically
// assigned to the "Imported (Ungrouped)" chapter.
const canSubmit = computed(() => {
  if (submitting.value || loading.value) return false
  return rows.value.length > 0
})

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.post(`/pyq-import/${pyqImport.uploadId}/add-to-test/`, {
      question_indexes: rows.value.map((q) => q.index),
    })
    data.skipped_not_valid = (data.skipped_not_valid || 0) + skippedNotValid.value
    data.skipped_unmapped = 0
    emit('added', data)
    emit('close')
  } catch (e) {
    errorMsg.value = e?.response?.data?.error || 'Could not add the questions.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex justify-end bg-black/30" @click.self="emit('close')">
    <div class="flex h-screen w-full max-w-2xl flex-col bg-white shadow-xl overflow-hidden">
      <!-- Header -->
      <div class="flex shrink-0 items-center justify-between border-b border-gray-100 px-6 py-4">
        <div>
          <h4 class="text-sm font-semibold text-gray-900">Add to Test</h4>
          <p class="mt-0.5 text-[11px] text-gray-400">
            Questions are auto-mapped to Subject &amp; Chapter. Fix anything that looks wrong, then add —
            they'll be available for Practice, Custom and Mock tests right away.
          </p>
        </div>
        <button class="text-gray-400 hover:text-gray-700" @click="emit('close')">✕</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto px-6 py-5">
        <div v-if="loading" class="py-10 text-center text-xs text-gray-400">Loading selected questions…</div>

        <template v-else>
          <!-- Notices -->
          <div v-if="skippedNotValid > 0" class="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-[11px] text-amber-700">
            {{ skippedNotValid }} selected question{{ skippedNotValid === 1 ? '' : 's' }} skipped — only
            <b>Valid</b> questions can be added. Review them first.
          </div>
          <div v-if="unmappedCount > 0" class="mb-3 rounded-lg bg-indigo-50 px-3 py-2 text-[11px] text-indigo-700">
            {{ unmappedCount }} question{{ unmappedCount === 1 ? ' has' : 's have' }} no specific chapter mapped yet.
            {{ unmappedCount === 1 ? 'It' : 'They' }} will be automatically grouped under "Imported (Ungrouped)", or you can choose a chapter below.
          </div>
          <div v-if="alreadyAddedCount > 0" class="mb-3 rounded-lg bg-blue-50 px-3 py-2 text-[11px] text-blue-600">
            {{ alreadyAddedCount }} question{{ alreadyAddedCount === 1 ? ' was' : 's were' }} already added
            previously and will be skipped as duplicates.
          </div>

          <p v-if="!rows.length" class="py-10 text-center text-xs text-gray-400">
            None of the selected questions are valid, so there is nothing to add.
          </p>

          <!-- Subject -> Chapter groups -->
          <div v-for="g in groups" :key="g.subject" class="mb-5">
            <div class="mb-2 flex items-center gap-2">
              <span class="rounded-lg bg-blue-50 px-2 py-1 text-[11px] font-semibold text-blue-600">{{ g.subject }}</span>
              <span class="text-[11px] text-gray-400">{{ g.count }} question{{ g.count === 1 ? '' : 's' }}</span>
            </div>

            <div
              v-for="c in g.chapters"
              :key="c.chapterId || 'none'"
              class="mb-2 rounded-xl border"
              :class="c.chapterId ? 'border-gray-100' : 'border-amber-200 bg-amber-50/30'"
            >
              <p class="border-b border-gray-100 px-3 py-1.5 text-[11px] font-medium"
                 :class="c.chapterId ? 'text-[#6C4CF1]' : 'text-amber-700'">
                {{ c.chapterName }}
                <span class="font-normal text-gray-400">· {{ c.items.length }}</span>
              </p>

              <div
                v-for="q in c.items"
                :key="q.index"
                class="flex items-center gap-3 border-b border-gray-50 px-3 py-2 last:border-0"
              >
                <span class="w-8 shrink-0 text-[11px] text-gray-400">Q{{ q.questionNumber ?? q.index }}</span>
                <div class="min-w-0 flex-1 max-h-12 overflow-hidden text-xs leading-5 text-gray-700">
                  <div class="flex items-center gap-1.5 mb-0.5" v-if="q.mapping_source">
                    <span
                      v-if="q.mapping_source === 'ai'"
                      class="inline-flex items-center gap-0.5 rounded px-1.5 py-0.2 bg-purple-50 text-purple-700 text-[9px] font-medium border border-purple-200"
                      title="AI Auto-Mapped"
                    >
                      🤖 AI ({{ q.mapping_confidence || 75 }}%)
                    </span>
                    <span
                      v-else-if="q.mapping_source === 'rules'"
                      class="inline-flex items-center gap-0.5 rounded px-1.5 py-0.2 bg-blue-50 text-blue-700 text-[9px] font-medium"
                      title="Rule Match"
                    >
                      ⚡ Rules
                    </span>
                  </div>
                  <MathRenderer :content="preview(q)" />
                </div>
                <select
                  class="w-40 shrink-0 truncate rounded-lg border bg-white px-2 py-1 text-[11px] outline-none focus:border-[#6C4CF1]"
                  :class="q.chapter_id ? 'border-gray-200 text-gray-700' : 'border-amber-300 text-amber-700'"
                  :value="q.chapter_id || ''"
                  @focus="ensureChaptersLoaded(q)"
                  @change="changeChapter(q, $event)"
                >
                  <option value="" disabled>Select chapter</option>
                  <option v-for="ch in chapterOptions(q)" :key="ch.chapter_id" :value="ch.chapter_id">
                    {{ ch.chapter_name }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <p v-if="rows.length" class="mt-2 rounded-lg bg-gray-50 px-3 py-2 text-[11px] text-gray-500">
            Adding files each question under its mapped chapter (ready for Practice), links it into this
            exam's "Imported Questions" custom test, and leaves it ready to pull into a Mock test in the
            next step — all from this one action.
          </p>

          <p v-if="errorMsg" class="mt-3 text-xs text-red-500">{{ errorMsg }}</p>
        </template>
      </div>

      <!-- Footer -->
      <div class="flex shrink-0 items-center justify-between border-t border-gray-100 px-6 py-4">
        <p class="text-[11px] text-gray-400">
          {{ rows.length }} question{{ rows.length === 1 ? '' : 's' }} ready to add
          <span v-if="unmappedCount > 0" class="text-amber-600">· {{ unmappedCount }} will use Ungrouped chapter</span>
        </p>
        <div class="flex gap-2">
          <button
            class="rounded-lg border border-gray-200 px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50"
            @click="emit('close')"
          >
            Cancel
          </button>
          <button
            class="rounded-lg px-4 py-2 text-xs font-semibold text-white shadow-sm"
            :class="canSubmit ? 'bg-[#6C4CF1] hover:bg-[#5B3EE0]' : 'cursor-not-allowed bg-gray-300'"
            :disabled="!canSubmit"
            @click="submit"
          >
            {{ submitting ? 'Adding…' : 'Add to Test' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>