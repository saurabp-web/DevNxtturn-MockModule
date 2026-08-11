<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Select Exam', to: { name: 'exams' } },
        { label: store.exam?.label ?? 'Exam', to: { name: 'exams' } },
        { label: 'Select Test Type', to: { name: 'practice-test-type' } },
        { label: 'Select Mock Test' },
      ]"
      :active-index="3"
    />

    <h2 class="pt-title">Select Mock Test</h2>
    <p class="pt-subtitle">Choose a mock test to start</p>

    <!-- Filters -->
    <div class="filters-row">
      <select v-model="filterAttempt" class="filter-select">
        <option value="">All Attempts</option>
        <option value="0">Not Attempted</option>
        <option value="1">Attempted</option>
      </select>
      <select v-model="filterLanguage" class="filter-select">
        <option value="">All Languages</option>
        <option value="English">English</option>
        <option value="Hindi">Hindi</option>
      </select>
      <select v-model="filterDifficulty" class="filter-select">
        <option value="">All Difficulty</option>
        <option value="Easy">Easy</option>
        <option value="Medium">Medium</option>
        <option value="Hard">Hard</option>
      </select>
      <button class="filter-icon-btn" title="More filters">
        <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
          <path d="M3 5h14M6 10h8M9 15h2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- Mock test list -->
    <div v-if="loadingTests" class="empty-msg">Loading mock tests…</div>
    <div v-else-if="loadTestsError" class="empty-msg" style="color:#dc2626">⚠ {{ loadTestsError }}</div>
    <div v-else class="mock-list">
      <div
        v-for="test in filteredTests"
        :key="test.id"
        class="mock-card"
        :class="{ selected: selectedTest?.id === test.id }"
        @click="selectedTest = test"
      >
        <div class="mc-radio" :class="{ on: selectedTest?.id === test.id }"></div>
        <div class="mc-body">
          <div class="mc-title-row">
            <span class="mc-name">{{ test.name }}</span>
            <span v-if="test.isLatest" class="mc-badge badge-latest">Latest</span>
          </div>
          <p class="mc-meta">Full Syllabus &bull; {{ test.questions }} Questions &bull; {{ test.duration }}</p>
        </div>
        <div class="mc-right">
          <span class="mc-difficulty" :class="diffClass(test.difficulty)">{{ test.difficulty }}</span>
          <span class="mc-marks">{{ test.marks }} Marks</span>
        </div>
      </div>

      <p v-if="filteredTests.length === 0" class="empty-msg">No mock tests match the selected filters.</p>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'practice-test-type' })">&larr; Back</button>
      <button class="continue-btn" :disabled="!selectedTest" @click="goNext">Continue &rarr;</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import { usePracticeTestStore } from '../../stores/practiceTest'
import type { MockTest } from '../../stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

onMounted(() => {
  if (!store.exam) { router.replace({ name: 'exams' }); return }
  loadMockTests()
})

// ── Filters ────────────────────────────────────────────────
const filterAttempt    = ref('')
const filterLanguage   = ref('')
const filterDifficulty = ref('')

// ── Mock test data — fetched from /api/mockexams/, scoped to the
// selected exam via its exam_code (not the broken exam_category
// text-match against /api/exams/ this used to do) ──
const mockTests       = ref<MockTest[]>([])
const loadingTests     = ref(false)
const loadTestsError   = ref('')

function formatDuration(minutes: number) {
  if (minutes % 60 === 0) return `${minutes / 60} Hour${minutes === 60 ? '' : 's'}`
  return `${minutes} Minutes`
}

function normalizeDifficulty(raw: string): 'Easy' | 'Medium' | 'Hard' {
  const d = (raw || '').toLowerCase()
  if (d === 'easy') return 'Easy'
  if (d === 'hard') return 'Hard'
  return 'Medium'
}

async function loadMockTests() {
  loadingTests.value   = true
  loadTestsError.value = ''
  mockTests.value      = []
  try {
    const examCode = store.exam?.code
    if (!examCode) throw new Error('No exam selected.')

    // Pull every page from /api/mockexams/?exam_code=... (PAGE_SIZE=20 server-side).
    const allMockExams: any[] = []
    let page = 1
    while (true) {
      const res = await fetch(`/api/mockexams/?exam_code=${encodeURIComponent(examCode)}&page=${page}`)
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const json = await res.json()
      allMockExams.push(...(json.results ?? []))
      if (allMockExams.length >= (json.count ?? 0) || (json.results ?? []).length === 0) break
      page++
    }

    if (allMockExams.length === 0) throw new Error('No mock tests available for this exam yet.')

    // Backend already orders by -year, mockexam_name; keep that order.
    mockTests.value = allMockExams.map((m: any, idx: number) => ({
      id:         m.mockexam_id,
      name:       m.mockexam_name,
      // MockExam has no question_count / difficulty / language fields yet
      // (see MockExamSerializer note) — default the same way the UI
      // already did, until those are added to the schema.
      questions:  m.question_count ?? 0,
      marks:      m.total_marks ?? (m.question_count ?? 0) * 4,
      duration:   formatDuration(m.duration_minutes ?? 180),
      difficulty: normalizeDifficulty(m.difficulty),
      language:   m.language || 'English',
      attempted:  false,   // no attempt-history endpoint yet
      isLatest:   idx === 0,
    }))
  } catch (e: any) {
    loadTestsError.value = e.message ?? 'Failed to load mock tests.'
  } finally {
    loadingTests.value = false
  }
}

const selectedTest = ref<MockTest | null>(null)

const filteredTests = computed(() => mockTests.value.filter(t => {
  if (filterDifficulty.value && t.difficulty !== filterDifficulty.value) return false
  if (filterLanguage.value   && t.language   !== filterLanguage.value)   return false
  if (filterAttempt.value === '0' && t.attempted)  return false
  if (filterAttempt.value === '1' && !t.attempted) return false
  return true
}))

function diffClass(d: string) {
  return { 'diff-easy': d === 'Easy', 'diff-medium': d === 'Medium', 'diff-hard': d === 'Hard' }
}

function goNext() {
  if (!selectedTest.value) return
  // Save selected mock test to store
  store.setMockTest(selectedTest.value)
  router.push({ name: 'mock-instructions' })
}
</script>

<style scoped>
.pt-page     { max-width: 900px; margin: 0 auto; user-select: none; }
.pt-title    { font-size: 19px; font-weight: 800; color: #1e2536; margin: 0 0 4px; user-select: none; }
.pt-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 16px; user-select: none; }

/* Filters */
.filters-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}
.filter-select {
  flex: 1;
  padding: 8px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  user-select: none;
  outline: none;
}
.filter-select:focus { border-color: #7c3aed; }
.filter-icon-btn {
  width: 36px; height: 36px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  user-select: none; color: #6b7280;
}
.filter-icon-btn:hover { border-color: #7c3aed; color: #7c3aed; }

/* Mock list */
.mock-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }

.mock-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 18px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.mock-card:hover  { border-color: #c4b5fd; box-shadow: 0 2px 8px rgba(124,58,237,0.07); }
.mock-card.selected { border-color: #7c3aed; background: #faf8ff; }

.mc-radio {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid #d1d5db; flex-shrink: 0;
}
.mc-radio.on {
  border-color: #7c3aed;
  background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%);
}

.mc-body { flex: 1; min-width: 0; user-select: none; }
.mc-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.mc-name  { font-size: 14px; font-weight: 700; color: #1e2536; user-select: none; }
.mc-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; }
.badge-latest { background: #7c3aed; color: #fff; }
.mc-meta  { font-size: 12px; color: #6b7280; margin: 0; user-select: none; }

.mc-right { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.mc-difficulty { font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 20px; }
.diff-easy   { background: #d1fae5; color: #065f46; }
.diff-medium { background: #fef3c7; color: #92400e; }
.diff-hard   { background: #fce7f3; color: #9d174d; }
.mc-marks { font-size: 12px; color: #6b7280; user-select: none; }

.empty-msg { text-align: center; color: #9ca3af; font-size: 13px; padding: 24px 0; }

/* Footer */
.pt-footer { display: flex; justify-content: space-between; align-items: center; }
.back-btn {
  background: #fff; border: 1px solid #e5e7eb; color: #1e2536;
  font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
.continue-btn {
  background: #7c3aed; border: none; color: #fff;
  font-weight: 700; font-size: 13px; padding: 10px 20px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
.continue-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>