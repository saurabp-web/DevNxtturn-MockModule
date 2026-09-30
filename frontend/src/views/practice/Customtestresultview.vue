<template>
  <div class="result-page" v-if="result">

    <div class="result-grid">
      <!-- ── Left: profile / test summary panel ── -->
      <aside class="panel profile-panel">
        <div class="profile-card">
          <div class="profile-avatar">
            <svg viewBox="0 0 24 24" width="26" height="26" fill="none">
              <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.8"/>
              <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="profile-info">
            <strong>{{ userName }}</strong>
            <span v-if="userEmail">{{ userEmail }}</span>
          </div>
        </div>

        <div class="meta-row">
          <span class="meta-icon">&#128196;</span>
          <div>
            <span class="meta-label">Exam Name</span>
            <strong class="meta-value">{{ result.examName }}</strong>
          </div>
        </div>
        <div class="meta-row">
          <span class="meta-icon">&#128203;</span>
          <div>
            <span class="meta-label">Test Name</span>
            <strong class="meta-value">{{ result.testName }}</strong>
          </div>
        </div>
        <div class="meta-row">
          <span class="meta-icon">&#128197;</span>
          <div>
            <span class="meta-label">Test Completed On</span>
            <strong class="meta-value">{{ submittedDate }}</strong>
          </div>
        </div>
        <div class="meta-row">
          <span class="meta-icon">&#127942;</span>
          <div>
            <span class="meta-label">Your Score</span>
            <strong class="meta-value">{{ result.marksObtained }} / {{ result.totalMarks }}</strong>
          </div>
        </div>
        <div class="meta-row">
          <span class="meta-icon">&#9989;</span>
          <div>
            <span class="meta-label">Result</span>
            <strong class="meta-value c-green">Completed</strong>
          </div>
        </div>

        <div class="great-job-box">
          <span class="gjb-icon">&#10003;</span>
          <div>
            <strong>Great job!</strong>
            <p>You have completed this assessment.</p>
          </div>
        </div>

        <button class="btn-dashboard" @click="goToDashboard">
          <span>&#128202;</span> Exam Dashboard
        </button>
        <button class="btn-reattempt-side" @click="reattempt">
          <span>&#8635;</span> Reattempt Test
        </button>
      </aside>

      <!-- ── Middle: per-question review ── -->
      <section class="panel review-panel">
        <div class="review-filter">
          <select v-model="statusFilter">
            <option value="all">All Questions</option>
            <option value="correct">Correct</option>
            <option value="wrong">Wrong</option>
            <option value="unattempted">Unattempted</option>
          </select>
        </div>

        <div
          v-for="q in filteredQuestions"
          :key="q.question_id"
          class="q-review-card"
        >
          <div class="q-review-head">
            <span class="q-review-num">{{ q.question_number }}</span>
            <span class="q-review-title">
              Question {{ q.question_number }}
              <span class="status-badge" :class="'status-' + q.status">{{ statusLabel(q.status) }}</span>
            </span>
            <span v-if="q.marksDelta !== 0" class="q-marks" :class="q.marksDelta > 0 ? 'c-green' : 'c-red'">
              {{ q.marksDelta > 0 ? '+' : '' }}{{ q.marksDelta }} Mark{{ Math.abs(q.marksDelta) === 1 ? '' : 's' }}
            </span>
          </div>

          <p class="q-review-text">{{ q.question_text }}</p>

          <!-- Your answer, if attempted -->
          <div
            v-if="q.yourAnswer"
            class="q-review-option"
            :class="q.status === 'correct' ? 'opt-right' : 'opt-wrong'"
          >
            <span class="opt-avatar">{{ q.yourAnswer.key }}</span>
            <span v-if="q.yourAnswer.image" class="opt-image-wrap">
              <img :src="mediaUrl(q.yourAnswer.image)" alt="" class="opt-image" />
            </span>
            <span v-else class="opt-text">{{ q.yourAnswer.text }}</span>
            <span class="opt-status-icon">{{ q.status === 'correct' ? '&#10003;' : '&#10007;' }}</span>
          </div>

          <!-- Correct answer, always shown when the user was wrong or skipped -->
          <div
            v-if="q.status !== 'correct'"
            class="q-review-option opt-right"
          >
            <span class="opt-avatar">{{ q.correctAnswer.key }}</span>
            <span v-if="q.correctAnswer.image" class="opt-image-wrap">
              <img :src="mediaUrl(q.correctAnswer.image)" alt="" class="opt-image" />
            </span>
            <span v-else class="opt-text">{{ q.correctAnswer.text }}</span>
            <span class="opt-status-icon">&#10003;</span>
          </div>

          <div class="q-solution">
            <strong>SOLUTION</strong>
            <p
              class="q-solution-text"
              :class="{ 'is-clamped': !isExpanded(q.question_id) && isLongSolution(q.explanation) }"
            >
              {{ q.explanation || 'Review the key concept related to this question to understand the correct answer.' }}
            </p>
            <button
              v-if="isLongSolution(q.explanation)"
              class="btn-show-more"
              @click="toggleExpanded(q.question_id)"
            >
              {{ isExpanded(q.question_id) ? 'Show less' : 'Show more' }}
              <span class="show-more-caret" :class="{ open: isExpanded(q.question_id) }">&#9662;</span>
            </button>
          </div>
        </div>

        <p v-if="filteredQuestions.length === 0" class="review-empty">No questions match this filter.</p>
      </section>

      <!-- ── Right: performance summary ── -->
      <aside class="panel performance-panel">
        <h3 class="panel-title">Test Performance</h3>

        <div class="score-donut" :style="donutStyle">
          <div class="score-donut-inner">
            <strong>{{ result.percentage }}%</strong>
            <span>Score</span>
          </div>
        </div>
        <p class="score-marks">{{ result.marksObtained }} / {{ result.totalMarks }} Marks</p>

        <div class="perf-grid">
          <div class="perf-cell">
            <span class="perf-icon c-green">&#10003;</span>
            <strong>{{ result.correct }}</strong>
            <span>Correct</span>
          </div>
          <div class="perf-cell">
            <span class="perf-icon c-red">&#10007;</span>
            <strong>{{ result.wrong }}</strong>
            <span>Wrong</span>
          </div>
          <div class="perf-cell">
            <span class="perf-icon c-orange">&#9675;</span>
            <strong>{{ result.skipped }}</strong>
            <span>Skipped</span>
          </div>
          <div class="perf-cell">
            <span class="perf-icon c-purple">&#9989;</span>
            <strong>{{ result.attempted }}</strong>
            <span>Attempted</span>
          </div>
        </div>

        <div class="perf-row"><span>Total Questions</span><strong>{{ result.total }}</strong></div>
        <div class="perf-row"><span>Total Marks</span><strong>{{ result.totalMarks }}</strong></div>
        <div class="perf-row"><span>Marks Obtained</span><strong>{{ result.marksObtained }}</strong></div>
        <div class="perf-row"><span>Negative Marks</span><strong>{{ result.negativeMarks }}</strong></div>
        <div class="perf-row"><span>Time Taken</span><strong>{{ formattedTimeTaken }} / {{ formattedTotalTime }}</strong></div>

        <button class="btn-download-report" @click="downloadResult">
          <span>&#8595;</span> Download Full Report
        </button>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePracticeTestStore } from '@/stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

const result = computed(() => store.customTestResult)
const statusFilter = ref<'all' | 'correct' | 'wrong' | 'unattempted'>('all')

// Solution "Show more" — collapsed by default, tracked per question so
// expanding one card's solution doesn't affect the others. A solution
// counts as "long" past a rough character threshold (matches roughly
// 3 lines at this box's width/font-size) so short solutions never show a
// pointless toggle with nothing left to reveal.
const expandedSolutions = ref(new Set<number>())
const SOLUTION_CLAMP_LENGTH = 180
function isLongSolution(text: string | undefined): boolean {
  return (text?.length ?? 0) > SOLUTION_CLAMP_LENGTH
}
function isExpanded(questionId: number): boolean {
  return expandedSolutions.value.has(questionId)
}
function toggleExpanded(questionId: number): void {
  const next = new Set(expandedSolutions.value)
  if (next.has(questionId)) next.delete(questionId)
  else next.add(questionId)
  expandedSolutions.value = next
}

onMounted(() => {
  if (!result.value) router.replace({ name: 'exams' })
})

// TODO: wire to your real auth store once available — this page doesn't
// have one passed in, so it falls back to generic placeholders rather than
// guessing at a shape that might not match your actual auth state.
const userName  = computed(() => 'You')
const userEmail = computed(() => '')

function mediaUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const MEDIA_BASE = (import.meta as any).env?.VITE_MEDIA_BASE_URL ?? ''
  return `${MEDIA_BASE.replace(/\/+$/, '')}/media/${path.replace(/^\/+/, '')}`
}

const filteredQuestions = computed(() => {
  const list = result.value?.perQuestion ?? []
  if (statusFilter.value === 'all') return list
  return list.filter(q => q.status === statusFilter.value)
})

function statusLabel(status: string): string {
  if (status === 'correct') return 'CORRECT'
  if (status === 'wrong') return 'WRONG'
  return 'UNATTEMPTED'
}

const submittedDate = computed(() => {
  const d = result.value?.submittedAt ? new Date(result.value.submittedAt) : new Date()
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
})

function padTime(n: number) { return String(n).padStart(2, '0') }

const formattedTimeTaken = computed(() => {
  const s = result.value?.timeTakenSeconds ?? 0
  return `${padTime(Math.floor(s / 60))}:${padTime(s % 60)}`
})
const formattedTotalTime = computed(() => {
  const s = result.value?.totalTimeSeconds ?? 0
  return `${padTime(Math.floor(s / 60))}:${padTime(s % 60)}`
})

// Donut ring built with a conic-gradient — no chart library needed.
const donutStyle = computed(() => {
  const pct = Math.max(0, Math.min(100, result.value?.percentage ?? 0))
  return {
    background: `conic-gradient(#7c3aed ${pct}%, #ede9fe ${pct}% 100%)`,
  }
})

function reattempt(): void {
  store.clearCustomTestResult()
  router.push({ name: 'practice-custom' })
}

function goToDashboard(): void {
  router.push({ name: 'exams' })
}

function downloadResult(): void {
  const r = result.value
  if (!r) return
  const lines = [
    `Exam: ${r.examName}`,
    `Test: ${r.testName}`,
    `Completed: ${submittedDate.value}`,
    `Score: ${r.marksObtained}/${r.totalMarks} (${r.percentage}%)`,
    `Correct: ${r.correct} | Wrong: ${r.wrong} | Skipped: ${r.skipped} | Attempted: ${r.attempted}`,
    `Time Taken: ${formattedTimeTaken.value} / ${formattedTotalTime.value}`,
    '',
    '--- Question-by-question ---',
    ...r.perQuestion.map(q =>
      `Q${q.question_number} [${statusLabel(q.status)}] ${q.question_text}\n` +
      `  Your answer: ${q.yourAnswer ? q.yourAnswer.key + ' - ' + (q.yourAnswer.text ?? '') : '(skipped)'}\n` +
      `  Correct answer: ${q.correctAnswer.key} - ${q.correctAnswer.text ?? ''}\n`
    ),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'test-result.txt'; a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.result-page { max-width: 1400px; margin: 0 auto; padding: 24px 0 40px; }

.result-grid {
  display: grid;
  grid-template-columns: 300px 1fr 340px;
  gap: 20px;
  align-items: start;
}
@media (max-width: 1100px) {
  .result-grid { grid-template-columns: 1fr; }
}

.panel {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 14px;
  padding: 20px;
}

/* ── Left profile panel ── */
.profile-panel { display: flex; flex-direction: column; }
.profile-card {
  background: #f5f3ff; border-radius: 12px; padding: 16px;
  display: flex; align-items: center; gap: 12px; margin-bottom: 18px;
}
.profile-avatar {
  width: 46px; height: 46px; border-radius: 50%; background: #7c3aed; color: #fff;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.profile-info { display: flex; flex-direction: column; }
.profile-info strong { font-size: 14.5px; color: #1e2536; }
.profile-info span { font-size: 12px; color: #6b7280; }

.meta-row {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px;
}
.meta-row:last-of-type { border-bottom: none; }
.meta-icon { font-size: 14px; margin-top: 1px; }
.meta-label { display: block; color: #6b7280; font-size: 11.5px; }
.meta-value { display: block; color: #1e2536; font-size: 13.5px; margin-top: 1px; }
.meta-value.c-green { color: #10b981; }

.great-job-box {
  display: flex; gap: 10px; align-items: flex-start;
  background: #ecfdf5; border: 1px solid #d1fae5; border-radius: 12px;
  padding: 14px; margin: 16px 0; font-size: 12.5px; color: #065f46;
}
.gjb-icon {
  width: 22px; height: 22px; border-radius: 50%; background: #10b981; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0;
}
.great-job-box strong { display: block; margin-bottom: 2px; font-size: 13px; }
.great-job-box p { margin: 0; line-height: 1.4; }

.btn-dashboard {
  background: #ede9fe; color: #7c3aed; border: none; font-weight: 700;
  font-size: 13.5px; padding: 12px; border-radius: 10px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin-bottom: 10px;
}
.btn-dashboard:hover { background: #e0d7fc; }
.btn-reattempt-side {
  background: #ecfdf5; color: #10b981; border: none; font-weight: 700;
  font-size: 13.5px; padding: 12px; border-radius: 10px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-reattempt-side:hover { background: #d9f9ec; }

/* ── Middle review panel ── */
.review-filter { margin-bottom: 16px; }
.review-filter select {
  border: 1px solid #e5e7eb; border-radius: 9px; padding: 9px 14px;
  font-size: 13.5px; font-weight: 600; color: #1e2536; background: #fff; cursor: pointer;
}

.q-review-card {
  border: 1px solid #f0f0f0; border-radius: 12px; padding: 18px; margin-bottom: 16px;
}
.q-review-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.q-review-num {
  width: 26px; height: 26px; border-radius: 50%; background: #f3f4f6; color: #374151;
  font-size: 12.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.q-review-title { font-size: 14.5px; font-weight: 700; color: #1e2536; display: flex; align-items: center; gap: 10px; }
.q-marks { margin-left: auto; font-size: 12.5px; font-weight: 700; }
.status-badge {
  font-size: 10px; font-weight: 800; letter-spacing: 0.04em;
  padding: 2px 10px; border-radius: 20px;
}
.status-correct { background: #ecfdf5; color: #10b981; }
.status-wrong { background: #fef2f2; color: #ef4444; }
.status-unattempted { background: #f3f4f6; color: #6b7280; }

.q-review-text { font-size: 14px; color: #1e2536; margin: 0 0 14px; line-height: 1.5; }

.q-review-option {
  display: flex; align-items: center; gap: 12px;
  border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; border: 1px solid transparent;
}
.opt-right { background: #ecfdf5; border-color: #d1fae5; }
.opt-wrong { background: #fef2f2; border-color: #fecaca; }
.opt-avatar {
  width: 24px; height: 24px; border-radius: 50%; color: #fff; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.opt-right .opt-avatar { background: #10b981; }
.opt-wrong .opt-avatar { background: #ef4444; }
.opt-text { flex: 1; font-size: 13.5px; color: #1e2536; }
.opt-image-wrap { flex: 1; display: flex; }
.opt-image { max-width: 100%; max-height: 100px; object-fit: contain; border-radius: 6px; }
.opt-status-icon { font-size: 14px; }
.opt-right .opt-status-icon { color: #10b981; }
.opt-wrong .opt-status-icon { color: #ef4444; }

.q-solution {
  background: #f9fafb; border-radius: 10px; padding: 12px 14px; margin-top: 12px;
}
.q-solution strong { font-size: 11px; letter-spacing: 0.04em; color: #6b7280; }
.q-solution p { margin: 6px 0 0; font-size: 13px; color: #374151; line-height: 1.5; }
.q-solution-text.is-clamped {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.btn-show-more {
  background: none; border: none; padding: 0; margin-top: 8px;
  color: #7c3aed; font-size: 12.5px; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; gap: 4px;
}
.btn-show-more:hover { text-decoration: underline; }
.show-more-caret { display: inline-block; transition: transform 0.15s ease; font-size: 10px; }
.show-more-caret.open { transform: rotate(180deg); }

.review-empty { text-align: center; color: #9ca3af; font-size: 13.5px; padding: 40px 0; }

/* ── Right performance panel ── */
.panel-title { font-size: 15px; font-weight: 800; color: #1e2536; margin: 0 0 18px; }

.score-donut {
  width: 130px; height: 130px; border-radius: 50%; margin: 0 auto 8px;
  display: flex; align-items: center; justify-content: center;
}
.score-donut-inner {
  width: 100px; height: 100px; border-radius: 50%; background: #fff;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.score-donut-inner strong { font-size: 22px; font-weight: 800; color: #1e2536; }
.score-donut-inner span { font-size: 11px; color: #6b7280; }
.score-marks { text-align: center; font-size: 12.5px; color: #6b7280; margin: 0 0 18px; }

.perf-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px;
}
.perf-cell {
  background: #f9fafb; border-radius: 12px; padding: 14px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.perf-icon {
  width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 13px; margin-bottom: 4px;
}
.perf-icon.c-green  { background: #ecfdf5; color: #10b981; }
.perf-icon.c-red    { background: #fef2f2; color: #ef4444; }
.perf-icon.c-orange { background: #fff7ed; color: #f59e0b; }
.perf-icon.c-purple { background: #f5f3ff; color: #7c3aed; }
.perf-cell strong { font-size: 20px; font-weight: 800; color: #1e2536; }
.perf-cell span { font-size: 11.5px; color: #6b7280; }

.perf-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; color: #4b5563; padding: 8px 0; border-bottom: 1px solid #f5f5f5;
}
.perf-row:last-of-type { border-bottom: none; }
.perf-row strong { color: #1e2536; }

.btn-download-report {
  width: 100%; background: #7c3aed; color: #fff; border: none; font-weight: 700;
  font-size: 13.5px; padding: 13px; border-radius: 10px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 18px;
}
.btn-download-report:hover { background: #6d28d9; }
</style>