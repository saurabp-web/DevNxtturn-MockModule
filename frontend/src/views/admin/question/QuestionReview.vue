<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Question Review</h1>
        <p class="page-desc">Review and approve questions before publishing.</p>
      </div>
      <button class="btn btn--secondary" @click="router.push({ name: 'question-bank' })">
        ← Back to Question Bank
      </button>
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-value">{{ questions.length }}</span>
        <span class="stat-label">Total Pending</span>
      </div>
      <div class="stat-card stat-card--green">
        <span class="stat-value">{{ approved.length }}</span>
        <span class="stat-label">Approved</span>
      </div>
      <div class="stat-card stat-card--red">
        <span class="stat-value">{{ rejected.length }}</span>
        <span class="stat-label">Rejected</span>
      </div>
    </div>

    <!-- Question Cards -->
    <div v-if="pendingQuestions.length === 0" class="empty-state">
      <p>🎉 All questions have been reviewed!</p>
      <button class="btn btn--primary" @click="router.push({ name: 'question-bank' })">
        Go to Question Bank
      </button>
    </div>

    <div v-else class="review-layout">
      <!-- Question Card -->
      <div class="card question-card">
        <div class="question-meta">
          <span class="meta-tag">{{ currentQuestion.subject }}</span>
          <span class="meta-tag">{{ currentQuestion.chapter }}</span>
          <span v-if="currentQuestion.topic" class="meta-tag">{{ currentQuestion.topic }}</span>
          <span :class="['badge', `badge--${currentQuestion.difficulty}`]">
            {{ currentQuestion.difficulty }}
          </span>
          <span class="meta-tag meta-tag--type">{{ currentQuestion.type }}</span>
        </div>

        <div class="question-counter">
          Question {{ currentIndex + 1 }} of {{ pendingQuestions.length }}
        </div>

        <h3 class="question-heading">Question</h3>
        <p class="question-text">{{ currentQuestion.text }}</p>

        <div v-if="currentQuestion.image" class="question-image">
          <img :src="currentQuestion.image" alt="Question image" />
        </div>

        <!-- Options -->
        <div class="options-list">
          <div
            v-for="(option, index) in currentQuestion.options"
            :key="index"
            :class="['option-item', { 'option-item--correct': option.isCorrect }]"
          >
            <span class="option-label">{{ String.fromCharCode(65 + index) }}</span>
            <span class="option-text">{{ option.text }}</span>
            <span v-if="option.isCorrect" class="correct-tick">✓</span>
          </div>
        </div>

        <!-- Explanation -->
        <div v-if="currentQuestion.explanation" class="explanation-box">
          <p class="explanation-title">Explanation</p>
          <p class="explanation-text">{{ currentQuestion.explanation }}</p>
        </div>

        <!-- Marks -->
        <div class="marks-row">
          <div class="marks-item">
            <span class="marks-label">Correct Marks</span>
            <span class="marks-value marks-value--green">+{{ currentQuestion.marks }}</span>
          </div>
          <div class="marks-item">
            <span class="marks-label">Negative Marks</span>
            <span class="marks-value marks-value--red">-{{ currentQuestion.negativeMarks }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="review-actions">
          <button class="btn btn--outline" @click="skipQuestion">
            Skip →
          </button>
          <button class="btn btn--danger" @click="rejectQuestion">
            ✕ Reject
          </button>
          <button class="btn btn--success" @click="approveQuestion">
            ✓ Approve
          </button>
        </div>
      </div>

      <!-- Sidebar: Reviewed List -->
      <div class="reviewed-sidebar">
        <h3 class="sidebar-title">Reviewed</h3>
        <div v-if="reviewed.length === 0" class="sidebar-empty">
          No questions reviewed yet.
        </div>
        <div
          v-for="item in reviewed"
          :key="item.id"
          class="reviewed-item"
        >
          <span class="reviewed-text">{{ item.text.slice(0, 50) }}...</span>
          <span :class="['reviewed-badge', item.status === 'approved' ? 'reviewed-badge--green' : 'reviewed-badge--red']">
            {{ item.status === 'approved' ? '✓' : '✕' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const currentIndex = ref(0)
const reviewed = ref([])

const questions = ref([
  {
    id: 1,
    text: "A resistor of 10Ω is connected to a 5V battery. What is the current flowing through the circuit?",
    subject: 'Physics',
    chapter: 'Current Electricity',
    topic: "Ohm's Law",
    type: 'Single Correct',
    difficulty: 'easy',
    marks: 4,
    negativeMarks: 1,
    explanation: "Using Ohm's Law: I = V/R = 5/10 = 0.5A",
    options: [
      { text: '0.5 A', isCorrect: true },
      { text: '2 A', isCorrect: false },
      { text: '50 A', isCorrect: false },
      { text: '0.2 A', isCorrect: false },
    ]
  },
  {
    id: 2,
    text: "Which of the following is a characteristic property of an ideal gas?",
    subject: 'Chemistry',
    chapter: 'States of Matter',
    topic: '',
    type: 'Single Correct',
    difficulty: 'medium',
    marks: 4,
    negativeMarks: 1,
    explanation: "An ideal gas has no intermolecular forces and its molecules occupy negligible volume.",
    options: [
      { text: 'High intermolecular forces', isCorrect: false },
      { text: 'No intermolecular forces', isCorrect: true },
      { text: 'Fixed volume', isCorrect: false },
      { text: 'Non-compressible', isCorrect: false },
    ]
  },
])

const pendingQuestions = computed(() =>
  questions.value.filter(q => !reviewed.value.find(r => r.id === q.id))
)

const currentQuestion = computed(() => pendingQuestions.value[currentIndex.value])

const approved = computed(() => reviewed.value.filter(r => r.status === 'approved'))
const rejected = computed(() => reviewed.value.filter(r => r.status === 'rejected'))

function approveQuestion() {
  reviewed.value.push({ ...currentQuestion.value, status: 'approved' })
  advanceIndex()
}

function rejectQuestion() {
  reviewed.value.push({ ...currentQuestion.value, status: 'rejected' })
  advanceIndex()
}

function skipQuestion() {
  advanceIndex()
}

function advanceIndex() {
  if (currentIndex.value >= pendingQuestions.value.length - 1) {
    currentIndex.value = 0
  }
}
</script>

<style scoped>
.page-wrapper {
  padding: 28px 32px;
  background: #f5f6fa;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
}

.page-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

/* Stats */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 130px;
}

.stat-card--green { border-left: 4px solid #16a34a; }
.stat-card--red { border-left: 4px solid #dc2626; }

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

/* Layout */
.review-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
  align-items: start;
}

/* Question Card */
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.meta-tag {
  padding: 3px 10px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  color: #374151;
}

.meta-tag--type {
  background: #ede9fe;
  color: #4f46e5;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.badge--easy { background: #dcfce7; color: #16a34a; }
.badge--medium { background: #fef3c7; color: #d97706; }
.badge--hard { background: #fee2e2; color: #dc2626; }

.question-counter {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 16px;
}

.question-heading {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.question-text {
  font-size: 15px;
  color: #111827;
  line-height: 1.6;
  margin: 0 0 20px;
}

.question-image img {
  max-width: 100%;
  border-radius: 8px;
  margin-bottom: 20px;
}

/* Options */
.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
  transition: all 0.15s;
}

.option-item--correct {
  border-color: #16a34a;
  background: #f0fdf4;
  color: #15803d;
}

.option-label {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.option-item--correct .option-label {
  background: #dcfce7;
  color: #16a34a;
}

.option-text { flex: 1; }

.correct-tick {
  font-size: 14px;
  color: #16a34a;
  font-weight: 700;
}

/* Explanation */
.explanation-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 20px;
}

.explanation-title {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0 0 6px;
}

.explanation-text {
  font-size: 14px;
  color: #374151;
  margin: 0;
  line-height: 1.6;
}

/* Marks */
.marks-row {
  display: flex;
  gap: 24px;
  padding: 14px 0;
  border-top: 1px solid #f3f4f6;
  border-bottom: 1px solid #f3f4f6;
  margin-bottom: 24px;
}

.marks-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.marks-label {
  font-size: 13px;
  color: #6b7280;
}

.marks-value {
  font-size: 14px;
  font-weight: 600;
}

.marks-value--green { color: #16a34a; }
.marks-value--red { color: #dc2626; }

/* Actions */
.review-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--primary { background: #4f46e5; color: #fff; }
.btn--primary:hover { background: #4338ca; }
.btn--secondary { background: #fff; color: #374151; border: 1px solid #d1d5db; }
.btn--secondary:hover { background: #f3f4f6; }
.btn--outline { background: transparent; color: #6b7280; border: 1px solid #d1d5db; }
.btn--outline:hover { background: #f3f4f6; }
.btn--success { background: #16a34a; color: #fff; }
.btn--success:hover { background: #15803d; }
.btn--danger { background: #dc2626; color: #fff; }
.btn--danger:hover { background: #b91c1c; }

/* Sidebar */
.reviewed-sidebar {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  position: sticky;
  top: 20px;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 16px;
}

.sidebar-empty {
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
  padding: 20px 0;
}

.reviewed-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.reviewed-item:last-child { border-bottom: none; }

.reviewed-text {
  font-size: 13px;
  color: #374151;
  line-height: 1.4;
  flex: 1;
}

.reviewed-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.reviewed-badge--green { background: #dcfce7; color: #16a34a; }
.reviewed-badge--red { background: #fee2e2; color: #dc2626; }

/* Empty state */
.empty-state {
  text-align: center;
  padding: 64px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  font-size: 16px;
  color: #6b7280;
}
</style>