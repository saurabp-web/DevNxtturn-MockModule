<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Select Exam', to: { name: 'exams' } },
        { label: store.exam?.label ?? 'Exam', to: { name: 'exams' } },
        { label: 'Select Test Type', to: { name: 'practice-test-type' } },
        { label: 'Select Mock Test', to: { name: 'mock-select' } },
        { label: 'Instructions' },
      ]"
      :active-index="4"
    />

    <h2 class="pt-title">Test Instructions</h2>
    <p class="pt-subtitle">Please go through the instructions before starting the test.</p>

    <div class="instr-layout">
      <!-- Left: Test Details -->
      <div class="details-card">
        <h3 class="card-heading">Test Details</h3>
        <div class="detail-row">
          <span class="dr-icon">🎓</span>
          <span class="dr-label">Exam</span>
          <span class="dr-value">{{ store.exam?.label ?? '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">📋</span>
          <span class="dr-label">Test Name</span>
          <span class="dr-value">{{ mockTest?.name ?? '—' }}</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">❓</span>
          <span class="dr-label">Questions</span>
          <span class="dr-value">{{ mockTest?.questions ?? 300 }}</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">⭐</span>
          <span class="dr-label">Total Marks</span>
          <span class="dr-value">{{ mockTest?.marks ?? 300 }}</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">⏱️</span>
          <span class="dr-label">Duration</span>
          <span class="dr-value">3 Hours (180 Minutes)</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">➖</span>
          <span class="dr-label">Negative Marking</span>
          <span class="dr-value">Yes</span>
        </div>
        <div class="marking-scheme">
          <span class="scheme-correct">Correct Answer : +4</span>
          <span class="scheme-wrong">Wrong Answer : -1</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">🌐</span>
          <span class="dr-label">Language</span>
          <span class="dr-value">{{ mockTest?.language ?? 'English' }}</span>
        </div>
        <div class="detail-row">
          <span class="dr-icon">📂</span>
          <span class="dr-label">Sections</span>
          <span class="dr-value">3 (Physics, Chemistry, Mathematics)</span>
        </div>
      </div>

      <!-- Right: Instructions -->
      <div class="instructions-card">
        <h3 class="card-heading">Instructions</h3>
        <ul class="instr-list">
          <li v-for="(item, i) in instructions" :key="i" class="instr-item">
            <span class="instr-dot">{{ i + 1 }}</span>
            <span class="instr-text">{{ item }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'mock-select' })">&larr; Back</button>
      <button class="start-btn" @click="startTest">Start Test &rarr;</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import { usePracticeTestStore } from '../../stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

onMounted(() => {
  if (!store.exam || !store.mockTest) router.replace({ name: 'mock-select' })
})

const mockTest = computed(() => store.mockTest)

const instructions = [
  "The test will start immediately after you click 'Start Test'.",
  'The timer will be visible on the top of the screen.',
  'You can navigate between sections and questions.',
  'Do not refresh or close the browser during the test.',
  'Your test will be auto submitted when time is up.',
  'All the best!',
]

function startTest() {
  router.push({ name: 'mock-attempt' })
}
</script>

<style scoped>
.pt-page     { max-width: 1000px; margin: 0 auto; user-select: none; }
.pt-title    { font-size: 19px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.pt-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 20px; }

.instr-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 720px) {
  .instr-layout { grid-template-columns: 1fr; }
}

.details-card,
.instructions-card {
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px;
}

.card-heading {
  font-size: 14px;
  font-weight: 800;
  color: #1e2536;
  margin: 0 0 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f3f4f6;
}

/* Detail rows */
.detail-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}
.detail-row:last-of-type { border-bottom: none; }
.dr-icon  { font-size: 14px; flex-shrink: 0; width: 20px; text-align: center; }
.dr-label { color: #6b7280; flex: 1; }
.dr-value { color: #1e2536; font-weight: 600; text-align: right; }

.marking-scheme {
  display: flex;
  gap: 12px;
  padding: 8px 0 8px 30px;
  font-size: 12px;
  font-weight: 700;
  border-bottom: 1px solid #f3f4f6;
}
.scheme-correct { color: #10b981; }
.scheme-wrong   { color: #ef4444; }

/* Instructions list */
.instr-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.instr-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}
.instr-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ede9fe;
  color: #7c3aed;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.instr-text { flex: 1; }

/* Footer */
.pt-footer { display: flex; justify-content: space-between; align-items: center; }
.back-btn {
  background: #fff; border: 1px solid #e5e7eb; color: #1e2536;
  font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
.start-btn {
  background: #7c3aed; border: none; color: #fff;
  font-weight: 700; font-size: 13px; padding: 10px 22px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
.start-btn:hover { background: #6d28d9; }
</style>