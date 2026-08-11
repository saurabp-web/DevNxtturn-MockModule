<template>
  <div class="result-page">

    <!-- Breadcrumb -->
    <div class="breadcrumb">
      <RouterLink :to="{ name: 'exams' }" class="bc-link">Practice Test</RouterLink>
      <span class="bc-sep">›</span>
      <span class="bc-link">{{ result?.subjectName ?? 'Custom Test' }}</span>
      <span class="bc-sep">›</span>
      <span class="bc-current">Test Result</span>
    </div>

    <!-- Header card -->
    <div class="header-card">
      <div class="header-left">
        <span class="completed-badge">✓ Test completed</span>
        <h2 class="test-name">{{ result?.testName ?? 'Custom Test' }}</h2>
        <p class="test-meta">
          Submitted on {{ submittedDate }} · Test Mode
        </p>
      </div>
      <div class="header-actions">
        <button class="btn-reattempt" @click="reattempt">
          ↺ Reattempt test
        </button>
        <button class="btn-examine" @click="examineTest">
          ⊙ Examine test
        </button>
      </div>
    </div>

    <!-- Greeting -->
    <h3 class="greeting">👋 Nice work, {{ username }}</h3>

    <!-- Top 4 stat cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon star">☆</div>
        <div class="stat-info">
          <span class="stat-label">Score</span>
          <span class="stat-value">{{ result?.score }}<span class="stat-denom">/{{ result?.total }}</span></span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon trophy">🏆</div>
        <div class="stat-info">
          <span class="stat-label">Rank</span>
          <span class="stat-value">{{ rank }}<span class="stat-denom rank-suffix">{{ rankSuffix }}</span></span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon clock">⏱</div>
        <div class="stat-info">
          <span class="stat-label">Time taken</span>
          <span class="stat-value">{{ formattedTimeTaken }}<span class="stat-denom">/{{ formattedTotalTime }}</span></span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon target">◎</div>
        <div class="stat-info">
          <span class="stat-label">Accuracy</span>
          <span class="stat-value">{{ accuracy }}<span class="stat-denom">%</span></span>
        </div>
      </div>
    </div>

    <!-- Bottom 4 count cards -->
    <div class="count-grid">
      <div class="count-card">
        <span class="count-num correct">{{ result?.correct }}/{{ result?.total }}</span>
        <span class="count-label">Questions</span>
        <span class="count-tag correct-tag">CORRECT</span>
      </div>
      <div class="count-card">
        <span class="count-num wrong">{{ result?.wrong }}/{{ result?.total }}</span>
        <span class="count-label">Questions</span>
        <span class="count-tag wrong-tag">WRONG</span>
      </div>
      <div class="count-card">
        <span class="count-num skipped">{{ result?.skipped }}/{{ result?.total }}</span>
        <span class="count-label">Questions</span>
        <span class="count-tag skipped-tag">SKIPPED</span>
      </div>
      <div class="count-card">
        <span class="count-num attempted">{{ result?.attempted }}/{{ result?.total }}</span>
        <span class="count-label">Questions</span>
        <span class="count-tag attempted-tag">ATTEMPTED</span>
      </div>
    </div>

    <!-- Action buttons -->
    <div class="action-row">
      <button class="btn-rate" @click="showRating = true">☆ Rate the test</button>
      <button class="btn-download" @click="downloadResult">⬇ Download result</button>
    </div>

    <!-- Rating modal -->
    <div v-if="showRating" class="modal-backdrop" @click.self="showRating = false">
      <div class="modal-box">
        <h3>Rate this test</h3>
        <div class="stars">
          <button
            v-for="n in 5"
            :key="n"
            class="star-btn"
            :class="{ filled: n <= rating }"
            @click="rating = n"
          >★</button>
        </div>
        <textarea v-model="ratingComment" placeholder="Share your feedback…" rows="3"></textarea>
        <div class="modal-actions">
          <button class="btn-sec" @click="showRating = false">Cancel</button>
          <button class="btn-pri" @click="submitRating">Submit</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePracticeTestStore } from '@/stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

const result    = computed(() => store.customTestResult)
const showRating = ref(false)
const rating     = ref(0)
const ratingComment = ref('')

onMounted(() => {
  if (!result.value) router.replace({ name: 'exams' })
})

// ── Computed display values ────────────────────────────────────────
const username = computed(() => 'User') // wire to auth store if available

const submittedDate = computed(() => {
  const d = result.value?.submittedAt ? new Date(result.value.submittedAt) : new Date()
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
})

const accuracy = computed(() => {
  const r = result.value
  if (!r || !r.attempted) return 0
  return Math.round((r.correct / r.attempted) * 100)
})

// Simulated rank based on score percentage
const rank = computed(() => {
  const pct = result.value?.percentage ?? 0
  if (pct >= 90) return 1
  if (pct >= 75) return 12
  if (pct >= 50) return 47
  if (pct >= 30) return 89
  return 120
})

const rankSuffix = computed(() => {
  const n = rank.value
  if (n === 1) return 'st'
  if (n === 2) return 'nd'
  if (n === 3) return 'rd'
  return 'th'
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

// ── Actions ───────────────────────────────────────────────────────
function reattempt(): void {
  store.clearCustomTestResult()
  router.push({ name: 'practice-test' })
}

function examineTest(): void {
  // Future: navigate to detailed question-by-question review
  alert('Examine test feature coming soon!')
}

function downloadResult(): void {
  const r = result.value
  if (!r) return
  const text = [
    `Test: ${r.testName}`,
    `Submitted: ${submittedDate.value}`,
    `Score: ${r.score}/${r.total}`,
    `Accuracy: ${accuracy.value}%`,
    `Correct: ${r.correct} | Wrong: ${r.wrong} | Skipped: ${r.skipped}`,
    `Time Taken: ${formattedTimeTaken.value}`,
  ].join('\n')
  const blob = new Blob([text], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = 'test-result.txt'; a.click()
  URL.revokeObjectURL(url)
}

function submitRating(): void {
  showRating.value = false
  rating.value = 0
  ratingComment.value = ''
  alert('Thanks for your rating!')
}
</script>

<style scoped>
.result-page { max-width: 900px; margin: 0 auto; padding: 0 0 40px; }

/* Breadcrumb */
.breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 13px; margin-bottom: 20px; }
.bc-link { color: #7c3aed; text-decoration: none; font-weight: 500; }
.bc-link:hover { text-decoration: underline; }
.bc-sep { color: #9ca3af; }
.bc-current { color: #374151; font-weight: 600; }

/* Header card */
.header-card {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 14px;
  padding: 20px 24px; margin-bottom: 24px;
  display: flex; justify-content: space-between; align-items: center; gap: 16px;
}
.completed-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: #ecfdf5; color: #065f46; font-size: 12px; font-weight: 700;
  padding: 4px 12px; border-radius: 20px; margin-bottom: 8px;
}
.test-name { font-size: 18px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.test-meta { font-size: 12.5px; color: #6b7280; margin: 0; }
.header-actions { display: flex; gap: 10px; flex-shrink: 0; }
.btn-reattempt {
  background: #fff; border: 1.5px solid #7c3aed; color: #7c3aed;
  font-size: 13px; font-weight: 700; padding: 9px 18px; border-radius: 9px;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}
.btn-examine {
  background: #7c3aed; border: none; color: #fff;
  font-size: 13px; font-weight: 700; padding: 9px 18px; border-radius: 9px;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

/* Greeting */
.greeting { font-size: 20px; font-weight: 800; color: #1e2536; margin: 0 0 20px; }

/* Top stat cards */
.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 14px; margin-bottom: 14px;
}
@media (max-width: 700px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }

.stat-card {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 14px;
  padding: 16px; display: flex; align-items: center; gap: 14px;
}
.stat-icon {
  width: 40px; height: 40px; border-radius: 10px; background: #ede9fe;
  display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;
}
.stat-info { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 11px; color: #6b7280; font-weight: 500; }
.stat-value { font-size: 20px; font-weight: 800; color: #1e2536; line-height: 1; }
.stat-denom { font-size: 13px; font-weight: 600; color: #6b7280; }
.rank-suffix { font-size: 13px; }

/* Bottom count cards */
.count-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 14px; margin-bottom: 24px;
}
@media (max-width: 700px) { .count-grid { grid-template-columns: repeat(2, 1fr); } }

.count-card {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 14px;
  padding: 20px 16px; display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.count-num {
  font-size: 26px; font-weight: 800; line-height: 1;
}
.count-num.correct  { color: #10b981; }
.count-num.wrong    { color: #ef4444; }
.count-num.skipped  { color: #6b7280; }
.count-num.attempted{ color: #7c3aed; }

.count-label { font-size: 12px; color: #6b7280; }
.count-tag {
  font-size: 10px; font-weight: 800; letter-spacing: 0.08em;
  padding: 2px 10px; border-radius: 20px; margin-top: 4px;
}
.correct-tag  { background: #ecfdf5; color: #10b981; }
.wrong-tag    { background: #fef2f2; color: #ef4444; }
.skipped-tag  { background: #f3f4f6; color: #6b7280; }
.attempted-tag{ background: #f5f3ff; color: #7c3aed; }

/* Action row */
.action-row {
  display: flex; justify-content: center; gap: 14px; margin-bottom: 24px;
}
.btn-rate {
  background: #fff; border: 1.5px solid #e5e7eb; color: #374151;
  font-size: 13px; font-weight: 700; padding: 10px 22px; border-radius: 9px; cursor: pointer;user-select: none;
}
.btn-download {
  background: #7c3aed; border: none; color: #fff;
  font-size: 13px; font-weight: 700; padding: 10px 22px; border-radius: 9px; cursor: pointer;user-select: none;
}

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 50;
}
.modal-box { background: #fff; border-radius: 14px; padding: 24px; width: 360px; max-width: 90vw; }
.modal-box h3 { margin: 0 0 14px; font-size: 16px; color: #1e2536; }
.stars { display: flex; gap: 8px; margin-bottom: 16px; }
.star-btn {
  font-size: 28px; background: none; border: none; cursor: pointer;user-select: none; color: #d1d5db; line-height: 1;
}
.star-btn.filled { color: #f59e0b; }
.modal-box textarea {
  width: 100%; box-sizing: border-box; border: 1.5px solid #e5e7eb; border-radius: 8px;
  padding: 10px; font-size: 13px; resize: vertical; margin-bottom: 14px; font-family: inherit;
}
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-pri { background: #7c3aed; color: #fff; border: none; padding: 9px 18px; border-radius: 8px; font-weight: 700; cursor: pointer;user-select: none; }
.btn-sec { background: #fff; color: #374151; border: 1.5px solid #e5e7eb; padding: 9px 18px; border-radius: 8px; font-weight: 600; cursor: pointer;user-select: none; }
</style>