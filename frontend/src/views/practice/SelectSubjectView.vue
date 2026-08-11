<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[{ label: 'Practice Test', to: { name: 'practice-start' } }, { label: 'Select Subject' }]"
      :active-index="1"
    />

    <h2 class="pt-title">Select Subject</h2>
    <p class="pt-subtitle">Choose a subject to start your practice test</p>

    <div v-if="loading" class="center-box">
      <div class="spinner"></div>
      <p>Loading subjects…</p>
    </div>

    <div v-else-if="loadError" class="center-box error-box">
      <p>{{ loadError }}</p>
      <button class="btn-primary" @click="loadSubjects">Retry</button>
    </div>

    <div v-else-if="subjects.length === 0" class="center-box">
      <p>No subjects found for this exam yet.</p>
    </div>

    <div v-else class="subject-grid">
      <div
        v-for="subject in subjects"
        :key="subject.id"
        class="subject-card"
        :class="{ selected: store.subject?.id === subject.id }"
        @click="store.setSubject(subject)"
      >
        <div class="subject-icon" :class="subject.colorClass">{{ subject.icon }}</div>
        <div class="subject-info">
          <h4>{{ subject.label }}</h4>
          <p>{{ subject.testCount }} {{ subject.testCount === 1 ? 'Chapter' : 'Chapters' }}</p>
        </div>
        <div v-if="store.subject?.id === subject.id" class="check-mark">&#10003;</div>
      </div>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'practice-start' })">&larr; Back</button>
      <button class="continue-btn" :disabled="!store.subject" @click="goNext">
        Continue &rarr;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import api from '@/services/axiosInstance'
import { usePracticeTestStore, type PracticeSubject } from '../../stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

type DisplaySubject = PracticeSubject & { icon: string; colorClass: string }

// Cosmetic-only — the backend has no icon/color data, so we map by name.
// Falls back to a generic icon for any subject name not listed here.
const ICON_MAP: Record<string, { icon: string; colorClass: string }> = {
  'physics':             { icon: '⚡', colorClass: 'c-blue' },
  'chemistry':           { icon: '🧪', colorClass: 'c-green' },
  'mathematics':         { icon: '📐', colorClass: 'c-purple' },
  'biology':             { icon: '🧬', colorClass: 'c-pink' },
  'botany':              { icon: '🌿', colorClass: 'c-teal' },
  'zoology':             { icon: '🦁', colorClass: 'c-amber' },
  'organic chemistry':   { icon: '⚗️', colorClass: 'c-orange' },
  'physical chemistry':  { icon: '🔬', colorClass: 'c-indigo' },
  'polity':              { icon: '🏛️', colorClass: 'c-blue' },
  'history':             { icon: '📜', colorClass: 'c-amber' },
  'geography':           { icon: '🌍', colorClass: 'c-teal' },
  'economy':             { icon: '📈', colorClass: 'c-green' },
  'environment':         { icon: '🌱', colorClass: 'c-teal' },
  'current affairs':     { icon: '📰', colorClass: 'c-pink' },
  'general studies':     { icon: '📘', colorClass: 'c-indigo' },
  'science & tech':      { icon: '🔬', colorClass: 'c-purple' },
}
const DEFAULT_ICON = { icon: '📘', colorClass: 'c-indigo' }

const subjects   = ref<DisplaySubject[]>([])
const loading    = ref(true)
const loadError  = ref('')

async function loadSubjects(): Promise<void> {
  loading.value = true
  loadError.value = ''

  // --- FIX: resolve exam params with fallback chain ---
  // Priority 1: numeric dbId set by SelectExamTypeView (ideal path)
  // Priority 2: store.exam.id (slug like 'jee-mains') sent as exam_code
  //             so the backend can look up the numeric PK itself
  // Priority 3: nothing found → show friendly error
  const params = subjectQueryParams()
  if (!params) {
    loadError.value = 'No exam selected. Please go back and pick an exam.'
    loading.value = false
    return
  }

  try {
    const res = await api.get('/subjects/', { params })

    // Support both response shapes:
    //   { subjects: [...] }  — current shape
    //   [...]                — flat array (some API versions)
    const raw: { id: number; label: string; test_count: number }[] =
      Array.isArray(res.data) ? res.data : (res.data.subjects ?? [])

    if (!raw || raw.length === 0) {
      // Got a valid response but no subjects — surface a clear message
      // instead of the generic "No subjects found" which could be confused
      // with the error state.
      subjects.value = []
      loading.value = false
      return
    }

    // De-dupe by subject name (case/whitespace-insensitive). The same
    // subject name (e.g. "Physics") legitimately exists as SEPARATE rows
    // for JEE and NEET, but within a single exam's subject list there
    // should never be two entries with the same name — if the backend
    // ever returns that (bad data, a join issue, etc.) we collapse it here
    // rather than showing duplicate cards. First occurrence wins.
    const seen = new Set<string>()
    const deduped = raw.filter((s) => {
      const key = s.label.trim().toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })

    subjects.value = deduped
      .map((s) => {
        const key = s.label.trim().toLowerCase()
        const style = ICON_MAP[key] ?? DEFAULT_ICON
        return {
          id: String(s.id),
          label: s.label,
          testCount: s.test_count,
          ...style,
        }
      })
      .sort((a, b) => a.label.localeCompare(b.label))

    // If dbId wasn't set yet but the API call succeeded via exam_code,
    // backfill dbId from the response so downstream views work correctly.
    if (store.examType && store.examType.dbId == null && res.data.exam_id) {
      store.setExamType({ ...store.examType, dbId: res.data.exam_id })
    }
  } catch (err: any) {
    // Give a more specific error if the server returned a 4xx/5xx
    const status = err?.response?.status
    if (status === 404) {
      loadError.value = 'Exam not found. Please go back and select a valid exam.'
    } else if (status === 401 || status === 403) {
      loadError.value = 'Session expired. Please log in again.'
    } else {
      loadError.value = 'Failed to load subjects. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

// Resolve query params for /subjects/ with a fallback chain so the view
// works even when SelectExamTypeView hasn't stored dbId yet.
//
// Priority 1 — store.examType.dbId  (numeric PK, most precise)
// Priority 2 — store.examType.id    (slug e.g. 'jee-mains'), sent as
//              exam_code so the backend resolves the PK itself
// Priority 3 — store.exam.id        (top-level exam slug e.g. 'jee'),
//              last-resort fallback; backend may return subjects for the
//              whole exam family rather than a specific type
function subjectQueryParams(): Record<string, string> | null {
  // Priority 1: numeric PK (best)
  const dbId = store.examType?.dbId
  if (dbId != null) {
    return { exam_id: String(dbId) }
  }

  // Priority 2: exam type slug (e.g. 'jee-mains')
  const examTypeId = store.examType?.id
  if (examTypeId) {
    console.warn(
      '[SelectSubjectView] examType.dbId is missing — falling back to exam_code:',
      examTypeId,
      '. Make sure SelectExamTypeView sets store.examType.dbId after resolving the exam.'
    )
    return { exam_code: String(examTypeId) }
  }

  // Priority 3: top-level exam slug (e.g. 'jee')
  const examId = (store as any).exam?.id
  if (examId) {
    console.warn(
      '[SelectSubjectView] examType not set — falling back to top-level exam slug:',
      examId
    )
    return { exam_code: String(examId) }
  }

  // Nothing available
  return null
}

onMounted(loadSubjects)

function goNext(): void {
  if (!store.subject) return
  store.setScope('chapter')   // auto-set scope, skipping scope selection page
  router.push({ name: 'practice-chapter' })
}
</script>

<style scoped>
.pt-page { max-width: 880px; margin: 0 auto; }

.pt-title {
  font-size: 19px;
  font-weight: 800;
  color: #1e2536;
  margin: 0 0 4px;
}

.pt-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 20px;
}

.center-box {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 200px; gap: 14px; color: #6b7280;
}
.error-box { color: #ef4444; }
.spinner {
  width: 36px; height: 36px; border: 4px solid #e5e7eb;
  border-top-color: #7c3aed; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.btn-primary {
  background: #7c3aed; color: #fff; border: none; font-weight: 700;
  font-size: 13px; padding: 9px 18px; border-radius: 8px; cursor: pointer;
  user-select: none;
}

.subject-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

@media (max-width: 760px) {
  .subject-grid { grid-template-columns: 1fr; }
}

.subject-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s, background 0.15s;
}

.subject-card:hover {
  border-color: #c4b5fd;
}

.subject-card.selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}

.subject-icon {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.c-purple { background: #ede9fe; }
.c-orange { background: #fef0e0; }
.c-blue { background: #dbeafe; }
.c-amber { background: #fef3c7; }
.c-green { background: #d1fae5; }
.c-teal { background: #ccfbf1; }
.c-pink { background: #fce7f3; }
.c-indigo { background: #e0e7ff; }

.subject-info h4 {
  font-size: 13.5px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 2px;
}

.subject-info p {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.check-mark {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #7c3aed;
  color: #fff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pt-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #1e2536;
  font-weight: 600;
  font-size: 13px;
  padding: 9px 16px;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
}

.continue-btn {
  background: #7c3aed;
  border: none;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
}

.continue-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>