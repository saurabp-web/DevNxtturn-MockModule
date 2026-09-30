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
    <p class="pt-subtitle">Choose a mock test to start your preparation</p>

    <!-- Tab Cards -->
    <div class="tab-cards">
      <div
        class="tab-card"
        :class="{ 'tab-card--active': activeTab === 'latest' }"
        @click="activeTab = 'latest'; selectedTest = null"
      >
        <div class="tab-card__icon">
          <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="tab-card__text">
          <span class="tab-card__title">Latest Mock Tests</span>
          <span class="tab-card__desc">Attempt the latest mock tests prepared by our experts</span>
        </div>
      </div>
      <div
        class="tab-card"
        :class="{ 'tab-card--active': activeTab === 'pyq' }"
        @click="activeTab = 'pyq'; selectedTest = null"
      >
        <div class="tab-card__icon">
          <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
            <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M8 2v4M16 2v4M3 10h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="tab-card__text">
          <span class="tab-card__title">Previous Year Mock Tests (PYQs)</span>
          <span class="tab-card__desc">Attempt mock tests from previous years</span>
        </div>
      </div>
    </div>

    <!-- Filters Row -->
    <div class="filters-row">
      <span class="filter-label">Filter Tests</span>
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
      <select v-if="activeTab === 'latest'" v-model="sortBy" class="filter-select">
        <option value="newest">Newest First</option>
        <option value="oldest">Oldest First</option>
      </select>
      <select v-if="activeTab === 'pyq'" v-model="sortBy" class="filter-select">
        <option value="newest">Year (Latest)</option>
        <option value="oldest">Year (Oldest)</option>
      </select>
      <button class="reset-btn" @click="resetFilters">
        <svg viewBox="0 0 20 20" fill="none" width="13" height="13" style="margin-right:4px">
          <path d="M4 10a6 6 0 1 0 1.22-3.65" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          <polyline points="1,6 4,10 8,7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Reset Filters
      </button>
    </div>

    <!-- Year Filter (PYQ only) -->
    <div v-if="activeTab === 'pyq'" class="year-filter-row">
      <span class="year-filter-label">Select Year</span>
      <div class="year-pills">
        <button
          v-for="yr in visibleYears"
          :key="yr"
          class="year-pill"
          :class="{ 'year-pill--active': selectedYear === yr }"
          @click="selectedYear = yr"
        >{{ yr === 'all' ? 'All Years' : yr }}</button>
        <button v-if="hiddenYears.length" class="year-pill year-pill--more" @click="showAllYears = !showAllYears">
          More {{ showAllYears ? '▲' : '▼' }}
        </button>
      </div>
    </div>

    <!-- Content -->
    <div v-if="loadingTests" class="empty-msg">Loading mock tests…</div>
    <div v-else-if="loadTestsError" class="empty-msg error-msg">⚠ {{ loadTestsError }}</div>

    <!-- Latest Tab -->
    <div v-else-if="activeTab === 'latest'" class="section-block">
      <div class="section-header">
        <div class="section-header__left">
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
            <path d="M10 2l1.5 4.5H16l-3.6 2.6 1.4 4.4L10 11l-3.8 2.5 1.4-4.4L4 6.5h4.5z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
          <span>Latest Mock Tests</span>
        </div>
        <span class="section-count">{{ filteredTests.length }} Tests</span>
      </div>

      <div class="mock-list">
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
            </div>
            <p class="mc-meta">
              <span class="mc-meta-item"><svg viewBox="0 0 16 16" width="12" height="12" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> {{ test.questions }} Questions</span>
              <span class="mc-meta-dot">·</span>
              <span class="mc-meta-item"><svg viewBox="0 0 16 16" width="12" height="12" fill="none"><rect x="2" y="3" width="12" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/></svg> {{ test.marks }} Marks</span>
              <span class="mc-meta-dot">·</span>
              <span class="mc-meta-item"><svg viewBox="0 0 16 16" width="12" height="12" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> {{ test.duration }}</span>
            </p>
          </div>
          <div class="mc-right">
            <span class="mc-difficulty" :class="diffClass(test.difficulty)">{{ test.difficulty }}</span>
            <span class="mc-badge badge-latest">Latest</span>
          </div>
        </div>
        <p v-if="filteredTests.length === 0" class="empty-msg">No mock tests match the selected filters.</p>
      </div>
    </div>

    <!-- PYQ Tab -->
    <div v-else-if="activeTab === 'pyq'" class="section-block">
      <div class="section-header">
        <div class="section-header__left">
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
            <rect x="3" y="3" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7 1v4M13 1v4M3 8h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>Previous Year Mock Tests (PYQs)</span>
        </div>
        <span class="section-count">{{ filteredTests.length }} Tests</span>
      </div>

      <div class="mock-list">
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
            </div>
            <p class="mc-meta">
              <span class="mc-meta-item"><svg viewBox="0 0 16 16" width="12" height="12" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> {{ test.questions }} Questions</span>
              <span class="mc-meta-dot">·</span>
              <span class="mc-meta-item"><svg viewBox="0 0 16 16" width="12" height="12" fill="none"><rect x="2" y="3" width="12" height="10" rx="1.5" stroke="currentColor" stroke-width="1.5"/></svg> {{ test.marks }} Marks</span>
              <span class="mc-meta-dot">·</span>
              <span class="mc-meta-item"><svg viewBox="0 0 16 16" width="12" height="12" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg> {{ test.duration }}</span>
            </p>
          </div>
          <div class="mc-right">
            <span class="mc-difficulty" :class="diffClass(test.difficulty)">{{ test.difficulty }}</span>
            <span class="mc-badge badge-year">Year {{ test.year }}</span>
          </div>
        </div>
        <p v-if="filteredTests.length === 0" class="empty-msg">No mock tests match the selected filters.</p>
      </div>
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

// ── Tabs ────────────────────────────────────────────────────
const activeTab = ref<'latest' | 'pyq'>('latest')

// ── Filters ─────────────────────────────────────────────────
const filterAttempt    = ref('')
const filterLanguage   = ref('')
const filterDifficulty = ref('')
const sortBy           = ref('newest')

// ── Year filter (PYQ) ────────────────────────────────────────
const selectedYear  = ref<string | number>('all')
const showAllYears  = ref(false)

const VISIBLE_YEAR_COUNT = 6

const allPyqYears = computed(() => {
  const years = [...new Set(
    pyqTests.value.map(t => t.year).filter(Boolean)
  )].sort((a, b) => Number(b) - Number(a))
  return ['all', ...years]
})

const visibleYears = computed(() =>
  showAllYears.value
    ? allPyqYears.value
    : allPyqYears.value.slice(0, VISIBLE_YEAR_COUNT + 1) // +1 for "all"
)

const hiddenYears = computed(() =>
  allPyqYears.value.slice(VISIBLE_YEAR_COUNT + 1)
)

function resetFilters() {
  filterAttempt.value    = ''
  filterLanguage.value   = ''
  filterDifficulty.value = ''
  sortBy.value           = 'newest'
  selectedYear.value     = 'all'
}

// ── Mock test data ────────────────────────────────────────────
const mockTests     = ref<MockTest[]>([])
const loadingTests  = ref(false)
const loadTestsError = ref('')

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

/**
 * Heuristic: PYQ tests typically have a year in their name (e.g. "2024")
 * and don't have "Mock Test 0X" style numbering.
 * Adjust this logic to match your real API field (e.g. m.is_pyq or m.year).
 */
function isPyq(m: any): boolean {
  return !!(m.year && Number(m.year) < new Date().getFullYear())
}

async function loadMockTests() {
  loadingTests.value   = true
  loadTestsError.value = ''
  mockTests.value      = []
  try {
    const examCode = store.exam?.code
    if (!examCode) throw new Error('No exam selected.')

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

    mockTests.value = allMockExams.map((m: any, idx: number) => ({
      id:         m.mockexam_id,
      name:       m.mockexam_name,
      questions:  m.question_count ?? 0,
      marks:      m.total_marks ?? (m.question_count ?? 0) * 4,
      duration:   formatDuration(m.duration_minutes ?? 180),
      difficulty: normalizeDifficulty(m.difficulty),
      language:   m.language || 'English',
      attempted:  false,
      isLatest:   !isPyq(m),
      year:       m.year ?? null,
    }))
  } catch (e: any) {
    loadTestsError.value = e.message ?? 'Failed to load mock tests.'
  } finally {
    loadingTests.value = false
  }
}

// ── Derived lists ─────────────────────────────────────────────
const latestTests = computed(() => mockTests.value.filter(t => t.isLatest))
const pyqTests    = computed(() => mockTests.value.filter(t => !t.isLatest))

const selectedTest = ref<MockTest | null>(null)

const filteredTests = computed(() => {
  const base = activeTab.value === 'latest' ? latestTests.value : pyqTests.value

  let result = base.filter(t => {
    if (filterDifficulty.value && t.difficulty !== filterDifficulty.value) return false
    if (filterLanguage.value   && t.language   !== filterLanguage.value)   return false
    if (filterAttempt.value === '0' && t.attempted)  return false
    if (filterAttempt.value === '1' && !t.attempted) return false
    if (activeTab.value === 'pyq' && selectedYear.value !== 'all' && String(t.year) !== String(selectedYear.value)) return false
    return true
  })

  result = [...result].sort((a, b) => {
    const aId = Number(a.id) || 0
    const bId = Number(b.id) || 0
    return sortBy.value === 'newest' ? bId - aId : aId - bId
  })

  return result
})

function diffClass(d: string) {
  return { 'diff-easy': d === 'Easy', 'diff-medium': d === 'Medium', 'diff-hard': d === 'Hard' }
}

function goNext() {
  if (!selectedTest.value) return
  store.setMockTest(selectedTest.value)
  router.push({ name: 'mock-instructions' })
}
</script>

<style scoped>
/* ── Page ─────────────────────────────────────────── */
.pt-page     { max-width: 900px; margin: 0 auto; user-select: none; }
.pt-title    { font-size: 19px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.pt-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 18px; }

/* ── Tab Cards ────────────────────────────────────── */
.tab-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.tab-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1.5px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  user-select: none;
}
.tab-card:hover {
  border-color: #c4b5fd;
  box-shadow: 0 2px 8px rgba(124,58,237,0.07);
}
.tab-card--active {
  border-color: #7c3aed;
  background: #f5f3ff;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.08);
}

.tab-card__icon {
  width: 42px; height: 42px;
  border-radius: 10px;
  background: #ede9fe;
  display: flex; align-items: center; justify-content: center;
  color: #7c3aed;
  flex-shrink: 0;
}
.tab-card--active .tab-card__icon {
  background: #7c3aed;
  color: #fff;
}

.tab-card__text {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.tab-card__title {
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
  line-height: 1.2;
}
.tab-card--active .tab-card__title { color: #5b21b6; }
.tab-card__desc {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

/* ── Filters ──────────────────────────────────────── */
.filters-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}
.filter-select {
  flex: 1;
  min-width: 120px;
  padding: 7px 10px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 12.5px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  outline: none;
}
.filter-select:focus { border-color: #7c3aed; }

.reset-btn {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 7px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  color: #7c3aed;
  background: #fff;
  cursor: pointer;
  white-space: nowrap;
}
.reset-btn:hover { border-color: #7c3aed; background: #f5f3ff; }

/* ── Year Filter ──────────────────────────────────── */
.year-filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.year-filter-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}
.year-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.year-pill {
  padding: 5px 14px;
  border-radius: 20px;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  font-size: 12.5px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  transition: border-color 0.13s, background 0.13s;
}
.year-pill:hover { border-color: #c4b5fd; }
.year-pill--active {
  background: #7c3aed;
  color: #fff;
  border-color: #7c3aed;
}
.year-pill--more {
  color: #7c3aed;
  border-color: #c4b5fd;
  background: #f5f3ff;
}

/* ── Section block ────────────────────────────────── */
.section-block { margin-bottom: 20px; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 2px;
}
.section-header__left {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
}
.section-header__left svg { color: #7c3aed; }
.section-count {
  font-size: 11.5px;
  font-weight: 700;
  color: #7c3aed;
  background: #ede9fe;
  padding: 3px 10px;
  border-radius: 20px;
}

/* ── Mock list / card ─────────────────────────────── */
.mock-list { display: flex; flex-direction: column; gap: 8px; }

.mock-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px 18px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.mock-card:hover  { border-color: #c4b5fd; box-shadow: 0 2px 8px rgba(124,58,237,0.07); }
.mock-card.selected { border-color: #7c3aed; background: #faf8ff; }

.mc-radio {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid #d1d5db; flex-shrink: 0;
  transition: border-color 0.13s;
}
.mc-radio.on {
  border-color: #7c3aed;
  background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%);
}

.mc-body { flex: 1; min-width: 0; }
.mc-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.mc-name  { font-size: 13.5px; font-weight: 700; color: #1e2536; }

.mc-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}
.mc-meta-item { display: flex; align-items: center; gap: 4px; }
.mc-meta-dot  { color: #d1d5db; }

.mc-right { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; flex-shrink: 0; }
.mc-difficulty { font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 20px; }
.diff-easy   { background: #d1fae5; color: #065f46; }
.diff-medium { background: #fef3c7; color: #92400e; }
.diff-hard   { background: #fce7f3; color: #9d174d; }

.mc-badge { font-size: 10.5px; font-weight: 700; padding: 2px 9px; border-radius: 20px; }
.badge-latest { background: #7c3aed; color: #fff; }
.badge-year   { background: #e0e7ff; color: #3730a3; }

.empty-msg { text-align: center; color: #9ca3af; font-size: 13px; padding: 24px 0; }
.error-msg { color: #dc2626; }

/* ── Footer ───────────────────────────────────────── */
.pt-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 8px; }
.back-btn {
  background: #fff; border: 1px solid #e5e7eb; color: #1e2536;
  font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: 8px; cursor: pointer;
}
.continue-btn {
  background: #7c3aed; border: none; color: #fff;
  font-weight: 700; font-size: 13px; padding: 10px 22px; border-radius: 8px; cursor: pointer;
}
.continue-btn:disabled { opacity: 0.45; cursor: not-allowed; }
</style>