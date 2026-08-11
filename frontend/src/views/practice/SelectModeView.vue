<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="breadcrumbs"
      :active-index="breadcrumbs.length - 1"
    />

    <h2 class="pt-title">Choose Test Mode</h2>
    <p class="pt-subtitle">Select the mode in which you want to attempt the test</p>

    <div class="mode-layout">
      <div class="selected-chapter-card" v-if="store.chapter">
        <span class="scc-label">Selected Chapter</span>
        <div class="scc-icon">📋</div>
        <h4>{{ store.chapter.label }}</h4>
        <p>{{ store.subject?.label }}</p>
        <RouterLink :to="{ name: 'practice-chapter' }" class="change-link">Change Chapter</RouterLink>
      </div>

      <div class="mode-options">
        <div
          class="mode-card"
          :class="{ selected: store.mode === 'test' }"
          @click="store.setMode('test')"
        >
          <div class="mode-radio" :class="{ on: store.mode === 'test' }"></div>
          <div class="mode-icon icon-purple">🕓</div>
          <h4>Test Mode</h4>
          <p>Simulate real exam environment.</p>
          <ul>
            <li>&#10003; Timed test</li>
            <li>&#10007; No explanations during test</li>
            <li>&#10003; Real exam experience</li>
          </ul>
        </div>

        <div
          class="mode-card"
          :class="{ selected: store.mode === 'practice' }"
          @click="store.setMode('practice')"
        >
          <div class="mode-radio" :class="{ on: store.mode === 'practice' }"></div>
          <div class="mode-icon icon-green">📖</div>
          <h4>Practice Mode</h4>
          <p>Learn while you practice.</p>
          <ul>
            <li>&#10003; Explanations after each question</li>
            <li>&#10003; Review your answers</li>
            <li>&#10003; Improve your skills</li>
          </ul>
        </div>
      </div>

      <div class="test-summary-card">
        <span class="tsc-label">Test Summary</span>
        <div class="tsc-row">
          <span>Subject</span>
          <strong>{{ store.subject?.label || '—' }}</strong>
        </div>
        <div class="tsc-row">
          <span>Chapter</span>
          <strong>{{ store.chapter?.label || 'Full Syllabus' }}</strong>
        </div>
        <div class="tsc-row">
          <span>Questions</span>
          <strong>{{ store.questionCount }}</strong>
        </div>
        <div class="tsc-row">
          <span>Difficulty</span>
          <strong>{{ store.difficulty }}</strong>
        </div>
        <div class="tsc-row">
          <span>Total Time</span>
          <strong>{{ store.durationMinutes }} Mins</strong>
        </div>
      </div>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="goBack">&larr; Back</button>
      <button class="start-test-btn" :disabled="!store.mode" @click="goNext">
        Start Test &rarr;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import { usePracticeTestStore } from '../../stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

onMounted(() => {
  if (!store.subject) router.replace({ name: 'practice-subject' })
  else if (!store.scope) router.replace({ name: 'practice-scope' })
  else if (store.scope === 'chapter' && !store.chapter) router.replace({ name: 'practice-chapter' })
})

const breadcrumbs = computed(() => {
  const base = [
    { label: 'Practice Test', to: { name: 'practice-start' } },
    { label: 'Select Subject', to: { name: 'practice-subject' } },
    { label: 'Select Chapter / Test Scope', to: { name: 'practice-scope' } },
  ]
  if (store.scope === 'chapter') {
    base.push({ label: 'Choose Chapter', to: { name: 'practice-chapter' } })
  }
  base.push({ label: 'Choose Mode' })
  return base
})

function goBack(): void {
  router.push({ name: store.scope === 'chapter' ? 'practice-chapter' : 'practice-scope' })
}

function goNext(): void {
  if (!store.mode) return
  router.push({ name: 'practice-review' })
}
</script>

<style scoped>
.pt-page { max-width: 1000px; margin: 0 auto; }

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

.mode-layout {
  display: grid;
  grid-template-columns: 220px 1fr 1fr 240px;
  gap: 14px;
  margin-bottom: 24px;
  align-items: start;
}

@media (max-width: 900px) {
  .mode-layout { grid-template-columns: 1fr; }
}

.selected-chapter-card {
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
  border-radius: 14px;
  padding: 16px;
}

.scc-label {
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  display: block;
  margin-bottom: 10px;
}

.scc-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #ede9fe;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.selected-chapter-card h4 {
  font-size: 13.5px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 2px;
}

.selected-chapter-card p {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 10px;
}

.change-link {
  font-size: 12px;
  font-weight: 700;
  color: #7c3aed;
  text-decoration: none;
}

.mode-options {
  display: contents;
}

.mode-card {
  position: relative;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
  cursor: pointer;
  user-select: none;
}

.mode-card.selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}

.mode-radio {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
}

.mode-radio.on {
  border-color: #7c3aed;
  background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%);
}

.mode-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  margin-bottom: 10px;
}

.icon-purple { background: #ede9fe; }
.icon-green { background: #d1fae5; }

.mode-card h4 {
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 4px;
}

.mode-card p {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 10px;
}

.mode-card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 12px;
  color: #374151;
}

.mode-card ul li {
  margin-bottom: 4px;
}

.test-summary-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
}

.tsc-label {
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  display: block;
  margin-bottom: 10px;
}

.tsc-row {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
  color: #374151;
  margin-bottom: 8px;
}

.tsc-row strong {
  color: #1e2536;
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

.start-test-btn {
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

.start-test-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>