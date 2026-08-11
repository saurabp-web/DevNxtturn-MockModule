<template>
  <div class="mock-shell" v-if="phase !== 'result'">

    <!-- ══════ TOP BAR ══════ -->
    <div class="topbar">
      <div class="topbar-brand">
        <div class="brand-icon">N</div>
        <span class="brand-name">NxtTurn</span>
        <span class="topbar-test-name">{{ store.mockTest?.name ?? 'Mock Test' }}</span>
      </div>
      <div class="topbar-actions">
        <button class="btn-pause" @click="paused = !paused">
          <span class="btn-icon">⏸</span> {{ paused ? 'Resume' : 'Pause' }}
        </button>
        <div class="topbar-stat">
          <span class="ts-icon">⏱</span>
          <div class="ts-body">
            <span class="ts-label">Time Left</span>
            <span class="ts-value" :class="{ warning: timeLeft < 300 }">{{ formattedTime }}</span>
          </div>
        </div>
        <div class="topbar-stat">
          <span class="ts-icon">📋</span>
          <div class="ts-body">
            <span class="ts-label">Questions</span>
            <span class="ts-value">{{ globalQIndex + 1 }} / {{ totalQuestions }}</span>
          </div>
        </div>
        <button class="btn-end-test" @click="confirmingSubmit = true">
          <span>↪</span> End Test
        </button>
      </div>
    </div>

    <!-- ══════ LOADING / ERROR ══════ -->
    <div v-if="loadingQuestions" class="load-state">
      <span class="load-spinner"></span> Loading questions…
    </div>
    <div v-else-if="loadError" class="load-state load-error">
      ⚠ {{ loadError }}
    </div>

    <!-- ══════ MAIN BODY ══════ -->
    <div v-else class="main-body">

      <!-- LEFT: Progress sidebar -->
      <aside class="left-sidebar">
        <div class="sidebar-card">
          <div class="progress-header">
            <span class="progress-title">📊 Progress</span>
            <div class="progress-dropdown" v-click-outside="() => progressDropdownOpen = false">
              <button
                class="overall-btn"
                :class="'pf-' + progressFilter.toLowerCase()"
                @click="progressDropdownOpen = !progressDropdownOpen"
              >
                <span>{{ progressFilterIcon }}</span> {{ progressFilter }} <span class="dd-caret">∨</span>
              </button>
              <div v-if="progressDropdownOpen" class="progress-dropdown-menu">
                <button
                  v-for="opt in ['Overall', ...sections.map(s => s.name)]"
                  :key="opt"
                  class="progress-dropdown-item"
                  :class="{ active: progressFilter === opt }"
                  @click="selectProgressFilter(opt)"
                >{{ opt }}</button>
              </div>
            </div>
          </div>

          <!-- Donut -->
          <div class="donut-wrap">
            <svg viewBox="0 0 120 120" class="donut-svg">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#f0f0f0" stroke-width="12"/>
              <circle cx="60" cy="60" r="50" fill="none" stroke="#10b981" stroke-width="12"
                :stroke-dasharray="progressArc + ' ' + (314 - progressArc)"
                stroke-dashoffset="78.5" stroke-linecap="round"/>
              <text x="60" y="55" text-anchor="middle" font-size="18" font-weight="800" fill="#1e2536">{{ progressPct }}%</text>
              <text x="60" y="70" text-anchor="middle" font-size="9" fill="#9ca3af">Completed</text>
            </svg>
          </div>
          <p class="solved-label">{{ progressStats.answered + progressStats.answeredMarked }} / {{ progressStats.total }} Solved</p>

          <!-- Question status -->
          <div class="status-section-title">QUESTION STATUS</div>
          <div class="status-grid">
            <div class="status-box">
              <span class="sb-num gray">{{ progressStats.notVisited }}</span>
              <span class="sb-lbl">Not Visited</span>
            </div>
            <div class="status-box">
              <span class="sb-num orange">{{ progressStats.skipped }}</span>
              <span class="sb-lbl">Skipped</span>
            </div>
            <div class="status-box">
              <span class="sb-num green">{{ progressStats.answered }}</span>
              <span class="sb-lbl">Answered</span>
            </div>
            <div class="status-box">
              <span class="sb-num purple">{{ progressStats.marked }}</span>
              <span class="sb-lbl">Marked for R...</span>
            </div>
            <div class="status-box">
              <span class="sb-num red">{{ progressStats.answeredMarked }}</span>
              <span class="sb-lbl">Answered & ...</span>
            </div>
          </div>

          <!-- Subject overview -->
          <div class="status-section-title" style="margin-top:16px">SUBJECT OVERVIEW</div>
          <div class="subject-bars">
            <div v-for="(sec, si) in sections" :key="sec.name" class="subj-bar-row">
              <div class="subj-bar-header">
                <span class="subj-name">{{ sec.name }}</span>
                <span class="subj-pct" :class="subjectPctClass(si)">{{ subjectPct(si) }}%</span>
              </div>
              <div class="subj-bar-track">
                <div class="subj-bar-fill" :style="{ width: subjectPct(si) + '%' }"></div>
              </div>
            </div>
          </div>

          <div class="total-questions-row">
            <span>Total Questions</span>
            <span class="tq-num">{{ totalQuestions }}</span>
          </div>
        </div>
      </aside>

      <!-- CENTER: Question area -->
      <section class="question-area">

        <!-- Subject tabs + Download -->
        <div class="subject-tabs-bar">
          <div class="subject-tabs">
            <button
              v-for="(sec, si) in sections"
              :key="sec.name"
              class="subj-tab"
              :class="{ active: currentSection === si }"
              @click="switchSection(si)"
            >
              <span class="subj-tab-icon">{{ subjectIcon(sec.name) }}</span>
              {{ sec.name }}
            </button>
          </div>
          <button class="btn-download" @click="openPdfPreview">⬇ Download</button>
        </div>

        <!-- Question card -->
        <div class="question-card">
          <div class="q-header">
            <span class="q-num-label">Question {{ currentQIndex + 1 }} <span class="q-of">of {{ currentSectionQs.length }}</span></span>
          </div>
          <div class="q-divider"></div>
          <p class="q-text">{{ currentQ?.question_text }}</p>

          <div class="options-list">
            <div
              v-for="opt in currentOptions"
              :key="opt.key"
              class="option-row"
              :class="optionClass(opt.key)"
              @click="selectAnswer(opt.key)"
            >
              <span class="opt-label">{{ opt.key }}</span>
              <span class="opt-text">{{ opt.text }}</span>
              <span class="opt-radio-wrap">
                <span class="opt-radio" :class="{ on: answers[currentQId] === opt.key }"></span>
              </span>
            </div>
          </div>
        </div>

        <!-- Footer actions -->
        <div class="q-footer">
          <button class="btn-prev" @click="prevQuestion" :disabled="globalQIndex === 0">‹ Previous</button>
          <button class="btn-clear-sel" @click="clearAnswer" :disabled="!answers[currentQId]">
            🗑 Clear Selection
          </button>
          <button class="btn-mark-review" @click="markAndNext">
            🏳 Mark for Review & Next
          </button>
          <button
            v-if="answers[currentQId]"
            class="btn-skip-next btn-submit-next"
            @click="submitAndNext"
          >
            Submit & Next →
          </button>
          <button v-else class="btn-skip-next" @click="skipAndNext">
            Skip & Next →
          </button>
        </div>
      </section>

      <!-- RIGHT: Question overview -->
      <aside class="right-sidebar">
        <div class="sidebar-card">
          <div class="overview-header">
            <span class="overview-title">Question Overview</span>
            <span class="overview-collapse">∧</span>
          </div>

          <!-- Filter tabs -->
          <div class="overview-filter-tabs">
            <button
              v-for="f in overviewFilters"
              :key="f.key"
              class="ovf-tab"
              :class="{ active: overviewFilter === f.key }"
              @click="overviewFilter = f.key"
            >
              <span class="ovf-icon">{{ f.icon }}</span>
              <span class="ovf-label">{{ f.label }}</span>
            </button>
          </div>

          <!-- Subject filter pills -->
          <div class="overview-subject-pills-wrap">
            <button class="pill-scroll-btn" @click="scrollPills(-100)">‹</button>
            <div class="overview-subject-pills" ref="pillsScrollEl">
              <button
                v-for="pill in ['All', ...sections.map(s => s.name)]"
                :key="pill"
                class="subj-pill"
                :class="{ active: overviewSubject === pill }"
                @click="overviewSubject = pill"
              >{{ pill }}</button>
            </div>
            <button class="pill-scroll-btn" @click="scrollPills(100)">›</button>
          </div>

          <!-- Quick navigation grid -->
          <div class="quick-nav-label">Quick Navigation</div>
          <div class="q-nav-grid">
            <button
              v-for="q in overviewQuestions"
              :key="q.question_id"
              class="nav-cell"
              :class="navCellClass(q.question_id)"
              @click="jumpToGlobal(globalIndexMap[q.question_id])"
            >{{ globalIndexMap[q.question_id] + 1 }}</button>
          </div>

          <!-- Preview list: shown for Review / Skipped filters -->
          <div v-if="overviewFilter !== 'all'" class="ov-question-list">
            <div
              v-for="q in overviewQuestions"
              :key="q.question_id"
              class="ov-list-item"
              :class="{ current: globalIndexMap[q.question_id] === globalQIndex }"
              @click="jumpToGlobal(globalIndexMap[q.question_id])"
            >
              <span class="ov-dot leg-dot" :class="dotStatusClass(q.question_id)"></span>
              <span class="ov-list-text"><b>Q{{ globalIndexMap[q.question_id] + 1 }}.</b> {{ questionPreview(q.question_text) }}</span>
            </div>
            <p v-if="overviewQuestions.length === 0" class="ov-empty">No questions here yet.</p>
          </div>

          <!-- Legend -->
          <template v-else>
            <div class="legend-title">Legend</div>
            <div class="legend-grid">
              <span class="legend-item"><span class="leg-dot leg-green"></span> Answered</span>
              <span class="legend-item"><span class="leg-dot leg-orange"></span> Skipped</span>
              <span class="legend-item"><span class="leg-dot leg-purple"></span> Marked for Review</span>
              <span class="legend-item"><span class="leg-dot leg-red"></span> Answered & Marked</span>
              <span class="legend-item"><span class="leg-dot leg-gray"></span> Not Visited</span>
            </div>
          </template>
        </div>
      </aside>
    </div>

    <!-- Download PDF preview modal -->
    <div v-if="showPdfPreview" class="modal-backdrop" @click.self="closePdfPreview">
      <div class="pdf-modal" :class="{ 'pdf-fullscreen': pdfFullscreen }">
        <div class="pdf-modal-topbar">
          <div class="pdf-tabs">
            <button
              v-for="t in ['All', ...sections.map(s => s.name)]"
              :key="t"
              class="pdf-tab"
              :class="{ active: pdfSubjectFilter === t }"
              @click="pdfSubjectFilter = t"
            >
              <span v-if="t !== 'All'">{{ subjectIcon(t) }}</span><span v-else>❐</span>
              {{ t }}
            </button>
          </div>
          <div class="pdf-topbar-actions">
            <button class="btn-pdf-expand" title="Toggle fullscreen" @click="pdfFullscreen = !pdfFullscreen">⛶</button>
            <button class="btn-pdf-download" @click="downloadPdf">⬇ Download PDF</button>
            <button class="btn-pdf-close" @click="closePdfPreview">✕</button>
          </div>
        </div>

        <div class="pdf-body" id="pdf-print-area">
          <p class="pdf-kicker">NXTTURN TEST SERIES</p>
          <h2 class="pdf-title">{{ store.mockTest?.name ?? 'Mock Test' }}</h2>
          <div class="pdf-meta-row">
            <span><b>Total Questions:</b> {{ totalQuestions }}</span>
            <span><b>Total Marks:</b> {{ totalQuestions * 4 }}</span>
            <span>Generated on {{ pdfGeneratedDate }}</span>
          </div>

          <div class="pdf-instructions">
            <p class="pdf-instructions-title">Instructions</p>
            <ul>
              <li>Each question carries the marks indicated alongside it (correct / incorrect).</li>
              <li>Numerical-type questions have no options — space is left for a written answer.</li>
              <li>This paper is generated for personal practice and reference only.</li>
            </ul>
          </div>

          <div v-for="sec in pdfSections" :key="sec.name" class="pdf-subject-block">
            <div class="pdf-subject-header" :class="'pf-bar-' + sec.name.toLowerCase()">
              <span>{{ sec.name.toUpperCase() }}</span>
              <span>{{ sec.questions.length }} Questions</span>
            </div>

            <div v-for="(q, qi) in sec.questions" :key="q.question_id" class="pdf-question">
              <div class="pdf-question-head">
                <p class="pdf-question-text"><b>Q{{ qi + 1 }}.</b> {{ questionBody(q.question_text) }}</p>
                <span class="pdf-marks">+4 / -1</span>
              </div>
              <div class="pdf-options-grid">
                <div v-for="opt in q.options" :key="opt.key" class="pdf-option">
                  <span class="pdf-opt-key">{{ opt.key }}</span>
                  <span>{{ opt.text }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirm submit modal -->
    <div v-if="confirmingSubmit" class="modal-backdrop" @click.self="confirmingSubmit = false">
      <div class="modal-box">
        <h3>Submit Test?</h3>
        <p class="modal-sub">
          You have {{ totalAnswered }} answered, {{ skippedCount }} skipped, and {{ markedCount }} marked for review.
          Are you sure you want to submit?
        </p>
        <div class="modal-actions">
          <button class="btn-modal-cancel" @click="confirmingSubmit = false">Cancel</button>
          <button class="btn-modal-submit" @click="submitTest">Submit</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ══════ RESULT SCREEN ══════ -->
  <div v-else class="result-page">
    <div class="trophy-wrap">🏆</div>
    <h2 class="result-title">Test Submitted Successfully!</h2>
    <p class="result-sub">Your test has been submitted.</p>

    <div class="result-stats-row">
      <div class="rs-box">
        <span class="rs-num c-purple">{{ result.score }}<span class="rs-denom">/{{ store.mockTest?.marks ?? 300 }}</span></span>
        <span class="rs-lbl">Score</span>
      </div>
      <div class="rs-box">
        <span class="rs-num c-green">{{ result.percentile }}</span>
        <span class="rs-lbl">Percentile</span>
      </div>
      <div class="rs-box">
        <span class="rs-num c-orange">{{ result.accuracy }}%</span>
        <span class="rs-lbl">Accuracy</span>
      </div>
      <div class="rs-box">
        <span class="rs-num c-blue">{{ result.rank }}<span class="rs-denom">/{{ result.totalStudents }}</span></span>
        <span class="rs-lbl">Rank</span>
      </div>
    </div>

    <div class="sectional-card">
      <h4 class="sectional-title">Sectional Summary</h4>
      <div class="sectional-row">
        <div v-for="sec in sections" :key="sec.name" class="sec-result">
          <span class="sec-result-name">{{ sec.name }}</span>
          <span class="sec-result-score c-green">{{ sectionScore(sec) }}<span class="sec-denom">/{{ sec.questions.length * 4 }}</span></span>
          <span class="sec-result-pct">{{ sectionAccuracy(sec) }}%</span>
        </div>
      </div>
    </div>

    <div class="result-actions">
      <button class="btn-analysis" @click="router.push({ name: 'exams' })">⊙ View Detailed Analysis</button>
      <button class="btn-dashboard" @click="router.push({ name: 'exams' })">Back to Dashboard</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePracticeTestStore } from '../../stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

// Simple click-outside directive used by the progress subject dropdown
const vClickOutside = {
  mounted(el: HTMLElement, binding: any) {
    el.__clickOutsideHandler__ = (e: MouseEvent) => {
      if (!(el === e.target || el.contains(e.target as Node))) binding.value(e)
    }
    document.addEventListener('click', el.__clickOutsideHandler__, true)
  },
  unmounted(el: any) {
    document.removeEventListener('click', el.__clickOutsideHandler__, true)
  },
}

onMounted(() => {
  if (!store.exam || !store.mockTest) { router.replace({ name: 'mock-select' }); return }
  loadQuestions()   // fetches real questions from API, then starts timer
})
onUnmounted(() => clearInterval(timerInterval))

// ── Phase ─────────────────────────────────────────────────────
type Phase = 'active' | 'result'
const phase = ref<Phase>('active')
const paused = ref(false)

// ── Timer ─────────────────────────────────────────────────────
const timeLeft = ref(180 * 60)
let timerInterval: ReturnType<typeof setInterval>

function startTimer() {
  timerInterval = setInterval(() => {
    if (paused.value) return
    if (timeLeft.value <= 0) { clearInterval(timerInterval); submitTest(); return }
    timeLeft.value--
  }, 1000)
}

const formattedTime = computed(() => {
  const h = Math.floor(timeLeft.value / 3600)
  const m = Math.floor((timeLeft.value % 3600) / 60)
  const s = timeLeft.value % 60
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
})

// ── Sections / Questions ──────────────────────────────────────
interface Question {
  question_id:  string           // kept as string so all downstream code works unchanged
  question_text: string
  options:      { key: string; text: string }[]
  correct_key:  string           // empty during test; filled after submitTest()
}
interface Section { name: string; questions: Question[] }

const sections          = ref<Section[]>([])
const loadingQuestions  = ref(false)
const loadError         = ref('')

// Preferred tab order; anything not listed falls back to alphabetical
const SUBJECT_ORDER = ['Physics', 'Chemistry', 'Mathematics', 'Biology']

async function loadQuestions() {
  loadingQuestions.value = true
  loadError.value        = ''
  sections.value         = []
  try {
    const examId = (store.mockTest as any)?.id
    if (!examId) throw new Error('No mock test selected.')

    // CustomQuestionListView — always serializes with context={'mode':'test'}
    // server-side, so correct_answer/solution are hidden already.
    // count is capped server-side to whatever exists, but must be passed
    // explicitly (default is only 50) — set high enough to fetch every
    // active question for the exam.
    const res = await fetch(`/api/questions/custom/?subject_ids=all&exam_id=${examId}&count=1000`)
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.error ?? `Server error ${res.status}`)
    }
    const json = await res.json()
    const flatQuestions: any[] = json.questions ?? []
    if (flatQuestions.length === 0) throw new Error('No questions found for this test.')

    // API shape: { questions: [{ question_id, question_text, subject_name,
    //   options: [{ option_A, option_B, option_C, option_D, ... }] }] }
    // Group the flat list into sections by subject_name.
    const bySubject = new Map<string, Question[]>()
    flatQuestions.forEach((q: any) => {
      const subjectName = q.subject_name ?? 'General'
      const opt = (q.options ?? [])[0] ?? {}
      const question: Question = {
        question_id:   String(q.question_id),
        question_text: q.question_text ?? '',
        correct_key:   '',   // hidden in test mode
        options: (['A', 'B', 'C', 'D'] as const).map(letter => ({
          key:  letter,
          text: String(opt[`option_${letter}`] ?? ''),
        })),
      }
      if (!bySubject.has(subjectName)) bySubject.set(subjectName, [])
      bySubject.get(subjectName)!.push(question)
    })

    sections.value = Array.from(bySubject.entries())
      .map(([name, questions]) => ({ name, questions }))
      .sort((a, b) => {
        const ai = SUBJECT_ORDER.indexOf(a.name)
        const bi = SUBJECT_ORDER.indexOf(b.name)
        if (ai === -1 && bi === -1) return a.name.localeCompare(b.name)
        if (ai === -1) return 1
        if (bi === -1) return -1
        return ai - bi
      })

    startTimer()   // only starts after questions load successfully
  } catch (e: any) {
    loadError.value = e.message ?? 'Failed to load questions.'
  } finally {
    loadingQuestions.value = false
  }
}

// ── Navigation ────────────────────────────────────────────────
const currentSection = ref(0)
const currentQIndex  = ref(0)

const currentSectionQs = computed(() => sections.value[currentSection.value]?.questions ?? [])
const currentQ         = computed(() => currentSectionQs.value[currentQIndex.value])
const currentQId       = computed(() => currentQ.value?.question_id ?? '')
const currentOptions   = computed(() => currentQ.value?.options ?? [])

// Global question index across all sections
const globalQIndex = computed(() => {
  let idx = 0
  for (let i = 0; i < currentSection.value; i++) idx += sections.value[i]?.questions.length ?? 0
  return idx + currentQIndex.value
})

const totalQuestions = computed(() => sections.value.reduce((s, sec) => s + sec.questions.length, 0))

function switchSection(si: number) { currentSection.value = si; currentQIndex.value = 0 }

function prevQuestion() {
  if (currentQIndex.value > 0) { currentQIndex.value--; return }
  if (currentSection.value > 0) {
    currentSection.value--
    currentQIndex.value = currentSectionQs.value.length - 1
  }
}

function skipAndNext() {
  skipped.value.add(currentQId.value)
  visited.value.add(currentQId.value)
  goNext()
}

function submitAndNext() {
  visited.value.add(currentQId.value)
  skipped.value.delete(currentQId.value)
  goNext()
}

function markAndNext() {
  marked.value[currentQId.value] = true
  visited.value.add(currentQId.value)
  goNext()
}

function goNext() {
  if (currentQIndex.value < currentSectionQs.value.length - 1) {
    currentQIndex.value++
  } else if (currentSection.value < sections.value.length - 1) {
    switchSection(currentSection.value + 1)
  }
}

function jumpToGlobal(gi: number) {
  let remaining = gi
  for (let si = 0; si < sections.value.length; si++) {
    const len = sections.value[si].questions.length
    if (remaining < len) { currentSection.value = si; currentQIndex.value = remaining; return }
    remaining -= len
  }
}

// ── Answers / State ───────────────────────────────────────────
const answers = ref<Record<string, string>>({})
const marked  = ref<Record<string, boolean>>({})
const skipped = ref<Set<string>>(new Set())
const visited = ref<Set<string>>(new Set())

function selectAnswer(key: string) {
  visited.value.add(currentQId.value)
  skipped.value.delete(currentQId.value)
  answers.value[currentQId.value] = key
}

function clearAnswer() {
  delete answers.value[currentQId.value]
  marked.value[currentQId.value] = false
}

function optionClass(key: string) {
  return { 'opt-selected': answers.value[currentQId.value] === key }
}

// ── Stats ─────────────────────────────────────────────────────
const totalAnswered      = computed(() => Object.keys(answers.value).filter(k => !marked.value[k]).length)
const markedCount        = computed(() => Object.values(marked.value).filter(Boolean).length)
const skippedCount       = computed(() => skipped.value.size)
const answeredMarkedCount= computed(() => Object.keys(answers.value).filter(k => marked.value[k]).length)
const notVisitedCount    = computed(() => totalQuestions.value - visited.value.size - skippedCount.value)

function subjectPct(si: number) {
  const sec = sections.value[si]
  if (!sec) return 0
  const ans = sec.questions.filter(q => answers.value[q.question_id]).length
  return Math.round((ans / sec.questions.length) * 100)
}
function subjectPctClass(si: number) {
  const p = subjectPct(si)
  return p === 0 ? 'pct-zero' : 'pct-active'
}
function subjectIcon(name: string) {
  if (name === 'Physics') return '⚛'
  if (name === 'Chemistry') return '⚗'
  return 'Σ'
}

// ── Progress subject filter (Overall / Physics / Chemistry / Mathematics) ──
const progressFilter = ref('Overall')
const progressDropdownOpen = ref(false)

function selectProgressFilter(opt: string) {
  progressFilter.value = opt
  progressDropdownOpen.value = false
}

const progressFilterIcon = computed(() => {
  if (progressFilter.value === 'Overall') return '✓'
  return subjectIcon(progressFilter.value)
})

const progressQuestions = computed(() => {
  if (progressFilter.value === 'Overall') return sections.value.flatMap(s => s.questions)
  return sections.value.find(s => s.name === progressFilter.value)?.questions ?? []
})

function statusStatsFor(qs: Question[]) {
  let answered = 0, skippedC = 0, markedOnly = 0, answeredMarked = 0, visitedC = 0
  qs.forEach(q => {
    const id = q.question_id
    const isAnswered = !!answers.value[id]
    const isMarked = !!marked.value[id]
    if (skipped.value.has(id)) skippedC++
    if (visited.value.has(id)) visitedC++
    if (isAnswered && isMarked) answeredMarked++
    else if (isAnswered) answered++
    else if (isMarked) markedOnly++
  })
  return {
    total: qs.length,
    answered,
    skipped: skippedC,
    marked: markedOnly,
    answeredMarked,
    notVisited: qs.length - visitedC,
  }
}

const progressStats = computed(() => statusStatsFor(progressQuestions.value))
const progressPct = computed(() => {
  const t = progressStats.value.total
  if (t === 0) return 0
  return Math.round(((progressStats.value.answered + progressStats.value.answeredMarked) / t) * 100)
})
const progressArc = computed(() => (progressPct.value / 100) * 314)

// ── Overview panel ────────────────────────────────────────────
const overviewFilter  = ref('all')
const overviewSubject = ref('All')
const pillsScrollEl   = ref<HTMLElement | null>(null)

function scrollPills(delta: number) {
  pillsScrollEl.value?.scrollBy({ left: delta, behavior: 'smooth' })
}

const overviewFilters = [
  { key: 'all',    label: 'All Questions', icon: '⊞' },
  { key: 'review', label: 'Review',        icon: '📄' },
  { key: 'skipped',label: 'Skipped',       icon: '☆'  },
]

const overviewQuestions = computed(() => {
  let allQs = sections.value.flatMap(s => s.questions)
  if (overviewSubject.value !== 'All') {
    const sec = sections.value.find(s => s.name === overviewSubject.value)
    allQs = sec?.questions ?? []
  }
  if (overviewFilter.value === 'review')  return allQs.filter(q => marked.value[q.question_id])
  if (overviewFilter.value === 'skipped') return allQs.filter(q => skipped.value.has(q.question_id))
  return allQs
})

// Maps every question_id to its true position across the whole test (used
// so quick-nav numbers/list stay correct even when a filter narrows the list)
const globalIndexMap = computed(() => {
  const map: Record<string, number> = {}
  let idx = 0
  sections.value.forEach(sec => sec.questions.forEach(q => { map[q.question_id] = idx++ }))
  return map
})

function navCellClass(qid: string) {
  if (answers.value[qid] && marked.value[qid]) return 'cell-answered-marked'
  if (marked.value[qid])    return 'cell-marked'
  if (answers.value[qid])   return 'cell-answered'
  if (skipped.value.has(qid)) return 'cell-skipped'
  if (visited.value.has(qid)) return 'cell-visited'
  return 'cell-unvisited'
}

function dotStatusClass(qid: string) {
  if (answers.value[qid] && marked.value[qid]) return 'leg-red'
  if (marked.value[qid])    return 'leg-purple'
  if (answers.value[qid])   return 'leg-green'
  if (skipped.value.has(qid)) return 'leg-orange'
  return 'leg-gray'
}

// Turns "Physics Question 2: The dimensional formula of Planck's constant is
// the same as that of:" into a short "The dimensional formula .....that of:" preview
function questionPreview(text: string) {
  const body = text.replace(/^.*?:\s*/, '').trim()
  const words = body.split(/\s+/)
  if (words.length <= 6) return body
  const start = words.slice(0, 3).join(' ')
  const end = words.slice(-2).join(' ')
  return `${start} .....${end}`
}

// ── Download PDF preview ────────────────────────────────────────
const showPdfPreview  = ref(false)
const pdfFullscreen   = ref(false)
const pdfSubjectFilter = ref('All')

const pdfGeneratedDate = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })

const pdfSections = computed(() => {
  if (pdfSubjectFilter.value === 'All') return sections.value
  return sections.value.filter(s => s.name === pdfSubjectFilter.value)
})

function questionBody(text: string) {
  return text.replace(/^.*?:\s*/, '').trim()
}

function openPdfPreview() {
  pdfSubjectFilter.value = 'All'
  showPdfPreview.value = true
}
function closePdfPreview() {
  showPdfPreview.value = false
  pdfFullscreen.value = false
}
function downloadPdf() {
  window.print()
}

// ── Submit ────────────────────────────────────────────────────
const confirmingSubmit = ref(false)
const result = ref({ score: 0, percentile: 0, accuracy: '0', rank: 0, totalStudents: 15230 })

async function submitTest() {
  clearInterval(timerInterval)
  confirmingSubmit.value = false

  // Build payload: { "<question_id>": "A" | "B" | "C" | "D" }
  const payload: Record<string, string> = {}
  sections.value.forEach(sec =>
    sec.questions.forEach(q => {
      const ans = answers.value[q.question_id]
      if (ans) payload[q.question_id] = ans
    })
  )

  try {
    const res = await fetch('/api/questions/submit/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ answers: payload }),
    })
    if (!res.ok) throw new Error(`Submit failed: ${res.status}`)
    const json = await res.json()
    // json = { score, max_score, total, correct, wrong, skipped, percentage, results:[...] }

    // Backfill correct_key on every question so sectionScore() works on result screen
    const correctMap: Record<string, string> = {}
    ;(json.results ?? []).forEach((r: any) => { correctMap[String(r.question_id)] = r.correct_answer ?? '' })
    sections.value.forEach(sec =>
      sec.questions.forEach(q => { q.correct_key = correctMap[q.question_id] ?? '' })
    )

    result.value = {
      // json.score is a raw correct-count over only the answered questions,
      // not scaled to store.mockTest.marks — compute the displayed score
      // locally instead, using the existing +4/-1 sectionScore() so it lines
      // up with the "/ marks" denominator shown on the result page.
      score:        sections.value.reduce((sum, sec) => sum + sectionScore(sec), 0),
      percentile:   0,
      accuracy:     json.percentage != null ? String(json.percentage.toFixed(1)) : '0',
      rank:         0,
      totalStudents: 0,
    }
  } catch {
    // Fallback: just show 0 — correct_keys are hidden server-side in test mode
    result.value = { score: 0, percentile: 0, accuracy: '0', rank: 0, totalStudents: 0 }
  }

  phase.value = 'result'
}

function sectionScore(sec: Section) {
  let s = 0
  sec.questions.forEach(q => {
    const ans = answers.value[q.question_id]
    if (ans) s += ans === q.correct_key ? 4 : -1
  })
  return Math.max(0, s)
}
function sectionAccuracy(sec: Section) {
  const ans = sec.questions.filter(q => answers.value[q.question_id]).length
  return sec.questions.length > 0 ? Math.round((ans / sec.questions.length) * 100) : 0
}
</script>

<style scoped>
* { user-select: none; box-sizing: border-box; }

/* ── Loading state ─────────────────────────────────────────── */
.load-state {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 12px; font-size: 14px; color: #6b7280;
}
.load-error { color: #dc2626; }
.load-spinner {
  display: inline-block; width: 22px; height: 22px;
  border: 3px solid #e5e7eb; border-top-color: #7c3aed;
  border-radius: 50%; animation: ld-spin 0.75s linear infinite;
}
@keyframes ld-spin { to { transform: rotate(360deg); } }

/* ── Shell ─────────────────────────────────────────────────── */
.mock-shell {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #f5f5f7;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Top bar ───────────────────────────────────────────────── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #e5e7eb;
  padding: 0 20px; height: 56px; flex-shrink: 0;
  gap: 16px;
}
.topbar-brand { display: flex; align-items: center; gap: 10px; }
.brand-icon {
  width: 32px; height: 32px; border-radius: 8px; background: #7c3aed;
  color: #fff; font-weight: 800; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
}
.brand-name { font-weight: 800; font-size: 15px; color: #7c3aed; }
.topbar-test-name { font-size: 13px; font-weight: 600; color: #374151; margin-left: 8px; }

.topbar-actions { display: flex; align-items: center; gap: 12px; }

.btn-pause {
  display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1.5px solid #e5e7eb; border-radius: 8px;
  padding: 7px 14px; font-size: 13px; font-weight: 600; color: #374151; cursor: pointer;
}
.btn-pause:hover { border-color: #7c3aed; color: #7c3aed; }

.topbar-stat {
  display: flex; align-items: center; gap: 8px;
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 6px 12px;
}
.ts-icon { font-size: 14px; }
.ts-body { display: flex; flex-direction: column; }
.ts-label { font-size: 10px; color: #9ca3af; font-weight: 500; }
.ts-value { font-size: 14px; font-weight: 800; color: #1e2536; }
.ts-value.warning { color: #ef4444; }

.btn-end-test {
  display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1.5px solid #fca5a5; border-radius: 8px;
  padding: 7px 14px; font-size: 13px; font-weight: 700; color: #ef4444; cursor: pointer;
}
.btn-end-test:hover { background: #fef2f2; }

/* ── Main 3-col layout ─────────────────────────────────────── */
.main-body {
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  gap: 16px;
  padding: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  align-items: stretch;
}
@media (max-width: 1100px) { .main-body { grid-template-columns: 1fr; } }

/* ── Shared sidebar card ───────────────────────────────────── */
.sidebar-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
}

/* Left sidebar — fills grid cell, scrolls internally */
.left-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.left-sidebar .sidebar-card {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.left-sidebar .sidebar-card::-webkit-scrollbar { width: 4px; }
.left-sidebar .sidebar-card::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }

/* Right sidebar — fills grid cell, scrolls internally */
.right-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.right-sidebar .sidebar-card {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.right-sidebar .sidebar-card::-webkit-scrollbar { width: 4px; }
.right-sidebar .sidebar-card::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }

/* ── LEFT sidebar ──────────────────────────────────────────── */
.progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.progress-title  { font-size: 13px; font-weight: 700; color: #1e2536; }

.progress-dropdown { position: relative; }
.overall-btn {
  display: flex; align-items: center; gap: 4px;
  background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a;
  font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px; cursor: pointer;
  white-space: nowrap;
}
.overall-btn .dd-caret { font-size: 9px; opacity: 0.7; }
.overall-btn.pf-overall     { background: #f0fdf4; border-color: #bbf7d0; color: #16a34a; }
.overall-btn.pf-physics     { background: #f5f3ff; border-color: #ddd6fe; color: #7c3aed; }
.overall-btn.pf-chemistry   { background: #fff7ed; border-color: #fed7aa; color: #ea580c; }
.overall-btn.pf-mathematics { background: #eff6ff; border-color: #bfdbfe; color: #2563eb; }

.progress-dropdown-menu {
  position: absolute; top: calc(100% + 6px); right: 0; z-index: 20;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1); padding: 6px; min-width: 140px;
  display: flex; flex-direction: column; gap: 2px;
}
.progress-dropdown-item {
  background: none; border: none; text-align: left; border-radius: 6px;
  padding: 7px 10px; font-size: 12px; font-weight: 600; color: #374151; cursor: pointer;
}
.progress-dropdown-item:hover { background: #f5f3ff; color: #7c3aed; }
.progress-dropdown-item.active { background: #ede9fe; color: #7c3aed; }

.donut-wrap { display: flex; justify-content: center; margin-bottom: 6px; }
.donut-svg  { width: 120px; height: 120px; }
.solved-label { text-align: center; font-size: 12px; color: #6b7280; margin: 0 0 14px; }

.status-section-title { font-size: 10px; font-weight: 800; color: #9ca3af; letter-spacing: 0.05em; margin-bottom: 10px; }

.status-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 4px; }
.status-box  { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.sb-num {
  width: 32px; height: 32px; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800;
}
.gray   { background: #f3f4f6; color: #6b7280; }
.orange { background: #fff7ed; color: #ea580c; }
.green  { background: #f0fdf4; color: #16a34a; }
.purple { background: #f5f3ff; color: #7c3aed; }
.red    { background: #fef2f2; color: #ef4444; }
.sb-lbl { font-size: 10px; color: #6b7280; text-align: center; }

.subject-bars { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
.subj-bar-row {}
.subj-bar-header { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }
.subj-name { font-weight: 600; color: #1e2536; }
.pct-zero   { color: #ef4444; font-weight: 700; }
.pct-active { color: #7c3aed; font-weight: 700; }
.subj-bar-track { height: 6px; background: #f3f4f6; border-radius: 999px; overflow: hidden; }
.subj-bar-fill  { height: 100%; background: linear-gradient(90deg, #7c3aed, #10b981); border-radius: 999px; transition: width 0.3s; }

.total-questions-row { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #6b7280; padding-top: 12px; border-top: 1px solid #f3f4f6; }
.tq-num { font-size: 14px; font-weight: 800; color: #1e2536; }

/* ── CENTER question area ──────────────────────────────────── */
.question-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.question-area::-webkit-scrollbar { width: 4px; }
.question-area::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }

.subject-tabs-bar { display: flex; justify-content: space-between; align-items: center; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 8px 12px; }
.subject-tabs { display: flex; gap: 4px; }
.subj-tab {
  display: flex; align-items: center; gap: 6px;
  background: none; border: none; border-radius: 8px;
  padding: 8px 16px; font-size: 13px; font-weight: 600; color: #6b7280; cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.subj-tab:hover { background: #f5f3ff; color: #7c3aed; }
.subj-tab.active { background: #7c3aed; color: #fff; }
.subj-tab-icon { font-size: 14px; }
.btn-download {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 7px 14px; font-size: 12px; font-weight: 600; color: #6b7280; cursor: pointer;
}
.btn-download:hover { border-color: #7c3aed; color: #7c3aed; }

.question-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 24px; flex: 1; }
.q-header { margin-bottom: 8px; }
.q-num-label { font-size: 15px; font-weight: 800; color: #1e2536; }
.q-of { font-size: 13px; font-weight: 500; color: #9ca3af; }
.q-divider { height: 1px; background: #f3f4f6; margin: 12px 0; }
.q-text { font-size: 15px; color: #1e2536; line-height: 1.7; margin: 0 0 24px; }

.options-list { display: flex; flex-direction: column; gap: 0; }
.option-row {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background 0.12s;
}
.option-row:last-child { border-bottom: none; }
.option-row:hover { background: #fafafa; }
.opt-selected { background: #f5f3ff !important; }
.opt-label { width: 24px; height: 24px; border-radius: 50%; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #6b7280; flex-shrink: 0; }
.opt-selected .opt-label { background: #7c3aed; color: #fff; }
.opt-text { flex: 1; font-size: 14px; color: #1e2536; }
.opt-radio-wrap { margin-left: auto; }
.opt-radio { display: block; width: 18px; height: 18px; border-radius: 50%; border: 2px solid #d1d5db; }
.opt-radio.on { border-color: #7c3aed; background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%); }

.q-footer {
  display: flex; align-items: center; gap: 10px; flex-wrap: nowrap;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px 16px;
  overflow-x: auto;
}
.q-footer::-webkit-scrollbar { display: none; }
.btn-prev {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 8px 16px; font-size: 13px; font-weight: 600; color: #374151; cursor: pointer;
  white-space: nowrap; flex-shrink: 0;
}
.btn-prev:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-clear-sel {
  background: #fff; border: 1.5px solid #fca5a5; border-radius: 8px;
  padding: 8px 14px; font-size: 13px; font-weight: 600; color: #ef4444; cursor: pointer;
  white-space: nowrap; flex-shrink: 0;
}
.btn-clear-sel:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-mark-review {
  background: #f5f3ff; border: 1.5px solid #ddd6fe; border-radius: 8px;
  padding: 8px 14px; font-size: 13px; font-weight: 700; color: #7c3aed; cursor: pointer;
  margin-left: auto; white-space: nowrap; flex-shrink: 0;
}
.btn-skip-next {
  background: #1e2536; border: none; border-radius: 8px;
  padding: 8px 18px; font-size: 13px; font-weight: 700; color: #fff; cursor: pointer;
  white-space: nowrap; flex-shrink: 0;
  width: 168px; text-align: center;
}
.btn-skip-next:hover { background: #374151; }
.btn-submit-next { background: #16a34a; }
.btn-submit-next:hover { background: #15803d; }

@media (max-width: 640px) {
  .q-footer { gap: 6px; padding: 10px 12px; }
  .btn-prev, .btn-clear-sel, .btn-mark-review, .btn-skip-next { padding: 7px 10px; font-size: 12px; }
  .btn-skip-next { width: auto; }
}

/* ── RIGHT sidebar ─────────────────────────────────────────── */
.overview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.overview-title  { font-size: 13px; font-weight: 800; color: #1e2536; }
.overview-collapse { color: #9ca3af; cursor: pointer; font-size: 12px; }

.overview-filter-tabs { display: flex; gap: 4px; margin-bottom: 10px; }
.ovf-tab {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px;
  background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 8px 4px; font-size: 10px; font-weight: 600; color: #6b7280; cursor: pointer;
}
.ovf-tab.active { background: #ede9fe; border-color: #c4b5fd; color: #7c3aed; }
.ovf-icon { font-size: 14px; }
.ovf-label { font-size: 9px; }

.overview-subject-pills-wrap { display: flex; align-items: center; gap: 4px; margin-bottom: 10px; }
.overview-subject-pills {
  display: flex; gap: 4px; flex-wrap: nowrap; flex: 1;
  overflow-x: auto; scroll-behavior: smooth;
  scrollbar-width: none; -ms-overflow-style: none;
}
.overview-subject-pills::-webkit-scrollbar { display: none; }
.subj-pill {
  background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 4px 10px; font-size: 11px; font-weight: 600; color: #6b7280; cursor: pointer;
  white-space: nowrap; flex-shrink: 0;
}
.subj-pill.active { background: #1e2536; border-color: #1e2536; color: #fff; }
.pill-scroll-btn {
  flex-shrink: 0; width: 20px; height: 20px; border-radius: 6px;
  background: #fff; border: 1px solid #e5e7eb; color: #6b7280;
  font-size: 12px; line-height: 1; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.pill-scroll-btn:hover { border-color: #7c3aed; color: #7c3aed; }

.quick-nav-label { font-size: 10px; font-weight: 700; color: #9ca3af; margin-bottom: 8px; letter-spacing: 0.05em; }
.q-nav-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; margin-bottom: 10px; max-height: 220px; overflow-y: auto; padding-right: 2px; }
.q-nav-grid::-webkit-scrollbar { width: 4px; }
.q-nav-grid::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
.q-nav-grid::-webkit-scrollbar-track { background: transparent; }
.nav-cell {
  width: 100%; aspect-ratio: 1; border-radius: 6px; border: 1px solid #e5e7eb;
  font-size: 11px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: transform 0.1s;
}
.nav-cell:hover { transform: scale(1.1); }
.cell-answered        { background: #22c55e; color: #fff; border-color: #22c55e; }
.cell-skipped         { background: #f59e0b; color: #fff; border-color: #f59e0b; }
.cell-marked          { background: #8b5cf6; color: #fff; border-color: #8b5cf6; }
.cell-answered-marked { background: #ef4444; color: #fff; border-color: #ef4444; }
.cell-visited         { background: #f3f4f6; color: #6b7280; }
.cell-unvisited       { background: #fff; color: #9ca3af; }

.ov-question-list { max-height: 320px; overflow-y: auto; display: flex; flex-direction: column; gap: 2px; margin-top: 2px; }
.ov-list-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 9px 6px; border-radius: 8px; cursor: pointer;
  font-size: 12px; color: #4b5563; line-height: 1.45;
  transition: background 0.12s;
}
.ov-list-item:hover { background: #f9fafb; }
.ov-list-item.current { background: #ede9fe; }
.ov-list-item .ov-dot { margin-top: 5px; }
.ov-list-text b { color: #1e2536; font-weight: 700; }
.ov-empty { font-size: 12px; color: #9ca3af; text-align: center; padding: 16px 0; }

.legend-title { font-size: 10px; font-weight: 700; color: #9ca3af; margin-bottom: 8px; letter-spacing: 0.05em; }
.legend-grid  { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.legend-item  { display: flex; align-items: center; gap: 6px; font-size: 10px; color: #374151; }
.leg-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.leg-green  { background: #15803d; }
.leg-orange { background: #d97706; }
.leg-purple { background: #7c3aed; }
.leg-red    { background: #991b1b; }
.leg-gray   { background: #fff; border: 1.5px solid #9ca3af; box-sizing: border-box; }

/* ── Modal ─────────────────────────────────────────────────── */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 50; }
.modal-box { background: #fff; border-radius: 14px; padding: 24px; width: 380px; max-width: 90vw; }
.modal-box h3 { margin: 0 0 8px; font-size: 16px; color: #1e2536; }
.modal-sub { font-size: 13px; color: #6b7280; margin: 0 0 18px; line-height: 1.5; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-modal-cancel { background: #fff; border: 1.5px solid #e5e7eb; color: #374151; font-size: 13px; font-weight: 600; padding: 9px 16px; border-radius: 8px; cursor: pointer; }
.btn-modal-submit { background: #7c3aed; border: none; color: #fff; font-size: 13px; font-weight: 700; padding: 9px 20px; border-radius: 8px; cursor: pointer; }

/* ── Result page ───────────────────────────────────────────── */
.result-page { max-width: 680px; margin: 40px auto; padding: 0 20px; display: flex; flex-direction: column; align-items: center; }
.trophy-wrap { font-size: 64px; margin-bottom: 12px; }
.result-title { font-size: 22px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.result-sub   { font-size: 13px; color: #6b7280; margin: 0 0 28px; }
.result-stats-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; width: 100%; margin-bottom: 24px; }
.rs-box { background: #fff; border: 1.5px solid #e5e7eb; border-radius: 14px; padding: 18px 12px; text-align: center; display: flex; flex-direction: column; gap: 6px; }
.rs-num { font-size: 22px; font-weight: 800; }
.rs-denom { font-size: 13px; color: #9ca3af; font-weight: 600; }
.rs-lbl { font-size: 12px; color: #6b7280; }
.sectional-card { background: #fff; border: 1.5px solid #e5e7eb; border-radius: 14px; padding: 20px; width: 100%; margin-bottom: 24px; }
.sectional-title { font-size: 14px; font-weight: 800; color: #1e2536; margin: 0 0 16px; }
.sectional-row { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
.sec-result { display: flex; flex-direction: column; gap: 4px; text-align: center; }
.sec-result-name  { font-size: 12px; color: #6b7280; font-weight: 600; }
.sec-result-score { font-size: 18px; font-weight: 800; }
.sec-denom { font-size: 12px; color: #9ca3af; font-weight: 600; }
.sec-result-pct { font-size: 12px; color: #6b7280; }
.result-actions { display: flex; gap: 12px; }
.btn-analysis  { background: #fff; border: 1.5px solid #7c3aed; color: #7c3aed; font-size: 13px; font-weight: 700; padding: 10px 18px; border-radius: 8px; cursor: pointer; }
.btn-dashboard { background: #7c3aed; border: none; color: #fff; font-size: 13px; font-weight: 700; padding: 10px 22px; border-radius: 8px; cursor: pointer; }

/* ── Color utils ───────────────────────────────────────────── */
.c-green  { color: #10b981; }
.c-purple { color: #7c3aed; }
.c-orange { color: #f59e0b; }
.c-blue   { color: #2563eb; }

/* ── Download PDF preview modal ───────────────────────────────── */
.pdf-modal {
  background: #fff; border-radius: 16px; width: 900px; max-width: 92vw;
  height: 88vh; display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
}
.pdf-modal.pdf-fullscreen { width: 100vw; height: 100vh; max-width: 100vw; border-radius: 0; }

.pdf-modal-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; gap: 12px;
}
.pdf-tabs { display: flex; gap: 4px; background: #f3f4f6; border-radius: 10px; padding: 4px; }
.pdf-tab {
  display: flex; align-items: center; gap: 6px;
  background: none; border: none; border-radius: 8px;
  padding: 7px 14px; font-size: 12px; font-weight: 700; color: #6b7280; cursor: pointer;
}
.pdf-tab.active { background: #7c3aed; color: #fff; }
.pdf-topbar-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.btn-pdf-expand {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  width: 32px; height: 32px; font-size: 14px; color: #6b7280; cursor: pointer;
}
.btn-pdf-download {
  display: flex; align-items: center; gap: 6px;
  background: #7c3aed; border: none; border-radius: 8px;
  padding: 8px 16px; font-size: 12px; font-weight: 700; color: #fff; cursor: pointer;
}
.btn-pdf-download:hover { background: #6d28d9; }
.btn-pdf-close {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  width: 32px; height: 32px; font-size: 13px; color: #6b7280; cursor: pointer;
}

.pdf-body { overflow-y: auto; padding: 28px 36px 48px; flex: 1; }
.pdf-kicker { font-size: 11px; font-weight: 800; letter-spacing: 0.08em; color: #9ca3af; margin: 0 0 4px; }
.pdf-title { font-size: 22px; font-weight: 800; color: #1e2536; margin: 0 0 10px; }
.pdf-meta-row { display: flex; gap: 24px; font-size: 12.5px; color: #6b7280; padding-bottom: 16px; margin-bottom: 18px; border-bottom: 2px solid #1e2536; }
.pdf-meta-row b { color: #1e2536; }

.pdf-instructions { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 18px; margin-bottom: 24px; }
.pdf-instructions-title { font-size: 13px; font-weight: 800; color: #1e2536; margin: 0 0 8px; }
.pdf-instructions ul { margin: 0; padding-left: 18px; }
.pdf-instructions li { font-size: 12.5px; color: #4b5563; line-height: 1.7; }

.pdf-subject-block { margin-bottom: 28px; }
.pdf-subject-header {
  display: flex; justify-content: space-between; align-items: center;
  background: #7c3aed; color: #fff; border-radius: 8px;
  padding: 10px 16px; font-size: 13px; font-weight: 800; letter-spacing: 0.03em;
  margin-bottom: 16px;
}
.pdf-subject-header.pf-bar-chemistry { background: #ea580c; }
.pdf-subject-header.pf-bar-mathematics { background: #2563eb; }

.pdf-question { padding-bottom: 18px; margin-bottom: 18px; border-bottom: 1px dashed #e5e7eb; }
.pdf-question:last-child { border-bottom: none; }
.pdf-question-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.pdf-question-text { font-size: 13.5px; color: #1e2536; line-height: 1.65; margin: 0; }
.pdf-marks { font-size: 11px; color: #9ca3af; font-weight: 700; white-space: nowrap; flex-shrink: 0; }
.pdf-options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; padding-left: 4px; }
.pdf-option { display: flex; align-items: baseline; gap: 8px; font-size: 13px; color: #374151; }
.pdf-opt-key {
  width: 20px; height: 20px; border-radius: 50%; background: #f3f4f6;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; color: #6b7280; flex-shrink: 0;
}

@media print {
  body * { visibility: hidden; }
  #pdf-print-area, #pdf-print-area * { visibility: visible; }
  #pdf-print-area { position: absolute; inset: 0; padding: 20px; }
}
</style>