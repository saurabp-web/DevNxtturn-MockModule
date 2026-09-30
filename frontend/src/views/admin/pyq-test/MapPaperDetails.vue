<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PYWizardStepper from './PYWizardStepper.vue'
import api from '@/api'
import { pyqImport } from '@/services/pyqImportStore'

const router = useRouter()

const subjects = ref([])
const loading = ref(true)
const saving = ref(false)
const errorMsg = ref('')

const form = reactive({
  exam_year: '',
  conducting_body: '',
  pyq_session: '',
  subject_ids: [],
  difficulty: 'Medium',
  // total_marks isn't a paper-details field on the backend (it's derived
  // from question marks at Create Test time) — kept here read-only just
  // to preserve the original screen layout.
})

const subjectDropdownOpen = ref(false)

function toggleSubject(subjectId) {
  const i = form.subject_ids.indexOf(subjectId)
  if (i === -1) form.subject_ids.push(subjectId)
  else form.subject_ids.splice(i, 1)
}

function subjectLabel() {
  if (!form.subject_ids.length) return 'Select subject(s)'
  const names = (Array.isArray(subjects.value) ? subjects.value : [])
    .filter((s) => form.subject_ids.includes(s.subject_id))
    .map((s) => s.subject_name)
  if (names.length) return names.join(', ')
  // subjects.value hasn't loaded/matched yet but IDs are already
  // selected (e.g. right after the paper-details fetch resolves but
  // before the subjects fetch does) — show a count instead of a
  // blank button so this never looks broken mid-load.
  return `${form.subject_ids.length} subject${form.subject_ids.length > 1 ? 's' : ''} selected`
}

onMounted(async () => {
  if (!pyqImport.uploadId) {
    // Wizard was entered directly without an upload — send them back to step 1.
    router.replace({ name: 'admin-tests-previous-upload' })
    return
  }

  try {
    const { data: details } = await api.get(`/pyq-import/${pyqImport.uploadId}/paper-details/`)
    pyqImport.paperDetails = details

    // Use details.exam_id (returned by the server from the cached
    // upload session) rather than pyqImport.examId here — examId
    // lives in a separate store field that isn't guaranteed to still
    // be set by the time this screen mounts (e.g. axios silently
    // drops an undefined query param, so `/subjects/?exam_id=` with
    // no value quietly turns into `/subjects/` with none at all,
    // which is exactly what was leaving this dropdown empty).
    const examId = details.exam_id ?? pyqImport.examId
    const { data: subjectData } = await api.get('/subjects/', { params: { exam_id: examId } })

    // /subjects/?exam_id= returns { exam_id, count, subjects: [...] } —
    // not a plain array or { results: [...] }. Support all three shapes
    // defensively so this doesn't silently break again if the endpoint
    // changes shape later.
    const rawSubjects = subjectData?.subjects ?? subjectData?.results ?? subjectData
    const rawList = Array.isArray(rawSubjects) ? rawSubjects : []
    // Normalize field names too — the API has been inconsistent about
    // subject_id/subject_name vs id/name in this project, and a
    // mismatch here renders as blank, unchecked checkbox rows (the
    // list length is right, but neither the label nor the checked
    // state can resolve) rather than an obvious error.
    subjects.value = rawList.map((s) => ({
      subject_id: s.subject_id ?? s.id ?? s.subjectId ?? s.value,
      subject_name: s.subject_name ?? s.name ?? s.subjectName ?? s.label ?? '',
    }))

    form.exam_year = details.exam_year ?? ''
    form.conducting_body = details.conducting_body ?? ''
    form.pyq_session = details.pyq_session ?? ''
    // Backend auto-detects subject(s) from the PDF text; if none are
    // mentioned in the header it falls back to every subject mapped to
    // the exam, so this is rarely empty — the admin can still adjust it.
    form.subject_ids = details.subject_ids ?? []
    form.difficulty = details.difficulty ?? 'Medium'
  } catch (e) {
    errorMsg.value = 'Could not load paper details for this upload.'
  } finally {
    loading.value = false
  }
})

async function goNext() {
  errorMsg.value = ''
  if (!String(form.exam_year ?? '').trim()) {
    errorMsg.value = 'Exam Year is required.'
    return
  }
  if (!form.subject_ids.length) {
    errorMsg.value = 'Select at least one subject.'
    return
  }
  saving.value = true
  try {
    const { data } = await api.post(`/pyq-import/${pyqImport.uploadId}/paper-details/`, {
      exam_year: form.exam_year,
      conducting_body: form.conducting_body,
      pyq_session: form.pyq_session,
      subject_ids: form.subject_ids,
      difficulty: form.difficulty,
    })
    pyqImport.paperDetails = data
    router.push({ name: 'admin-tests-previous-review-questions' })
  } catch (e) {
    // Log the real failure so it shows up in devtools instead of just the
    // generic banner — makes the next "Next button doesn't work" report
    // actionable without needing another screen-share.
    console.error('paper-details save failed:', e?.response?.status, e?.response?.data || e)
    errorMsg.value = e?.response?.data?.error || 'Could not save paper details. Please try again.'
  } finally {
    saving.value = false
  }
}
function goBack() {
  router.push({ name: 'admin-tests-previous-upload' })
}
</script>

<template>
  <div class="p-6">
    <PYWizardStepper :current-step="2" />

    <div class="mx-auto max-w-4xl">
      <h3 class="text-base font-semibold text-gray-900">Map Paper Details</h3>
      <p class="mt-1 text-xs text-gray-500">Please provide the details about this question paper.</p>

      <div v-if="loading" class="mt-5 rounded-xl border border-gray-200 bg-white p-6 text-xs text-gray-400">
        Loading paper details…
      </div>

      <div v-else class="mt-5 rounded-xl border border-gray-200 bg-white p-6">
        <div class="grid grid-cols-2 gap-x-8 gap-y-5">
          <div>
            <label class="mb-1.5 block text-xs font-medium text-gray-600">Exam</label>
            <input
              :value="pyqImport.paperDetails.exam_name"
              disabled
              class="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-xs text-gray-500 outline-none"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-gray-600">Conducting Body <span class="text-red-500">*</span></label>
            <input
              v-model="form.conducting_body"
              type="text"
              class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-xs outline-none focus:border-[#6C4CF1]"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-gray-600">Exam Year <span class="text-red-500">*</span></label>
            <input
              v-model="form.exam_year"
              type="number"
              class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-xs outline-none focus:border-[#6C4CF1]"
            />
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-gray-600">Session / Shift</label>
            <input
              v-model="form.pyq_session"
              type="text"
              placeholder="e.g. Shift 1"
              class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-xs outline-none focus:border-[#6C4CF1]"
            />
          </div>
          <div class="relative">
            <label class="mb-1.5 block text-xs font-medium text-gray-600">Subject(s) <span class="text-red-500">*</span></label>
            <button
              type="button"
              class="flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-2.5 text-left text-xs outline-none focus:border-[#6C4CF1]"
              :class="!form.subject_ids.length ? 'text-gray-400' : 'text-gray-800'"
              @click="subjectDropdownOpen = !subjectDropdownOpen"
            >
              <span class="truncate">{{ subjectLabel() }}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0"><polyline points="6 9 12 15 18 9" /></svg>
            </button>
            <div
              v-if="subjectDropdownOpen"
              class="absolute z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white p-1.5 shadow-lg"
            >
              <label
                v-for="s in subjects"
                :key="s.subject_id"
                class="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  :checked="form.subject_ids.includes(s.subject_id)"
                  class="rounded border-gray-300 text-[#6C4CF1] focus:ring-[#6C4CF1]"
                  @change="toggleSubject(s.subject_id)"
                />
                {{ s.subject_name }}
              </label>
              <p v-if="!subjects.length" class="px-2 py-1.5 text-[11px] text-gray-400">No subjects mapped to this exam.</p>
            </div>
          </div>
          <div>
            <label class="mb-1.5 block text-xs font-medium text-gray-600">Difficulty Level (Overall) <span class="text-red-500">*</span></label>
            <select v-model="form.difficulty" class="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-xs outline-none focus:border-[#6C4CF1]">
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </select>
          </div>
        </div>
      </div>

      <p v-if="errorMsg" class="mt-3 text-xs text-red-500">{{ errorMsg }}</p>

      <div class="mt-6 flex justify-end gap-3">
        <button class="rounded-lg border border-gray-200 px-4 py-2.5 text-xs font-medium text-gray-600 hover:bg-gray-50" @click="goBack">
          ← Back
        </button>
        <button
          class="rounded-lg bg-[#6C4CF1] px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-[#5B3EE0] disabled:opacity-60"
          :disabled="saving || loading"
          @click="goNext"
        >
          {{ saving ? 'Saving…' : 'Next: Review & Create →' }}
        </button>
      </div>
    </div>
  </div>
</template>