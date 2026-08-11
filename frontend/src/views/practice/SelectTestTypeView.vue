<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Select Exam', to: { name: 'exams' } },
        { label: store.exam?.label ?? 'Exam', to: { name: 'exams' } },
        { label: 'Select Test Type' },
      ]"
      :active-index="2"
    />

    <h2 class="pt-title">Select Test Type</h2>
    <p class="pt-subtitle">Choose how you want to attempt the test</p>

    <div class="test-type-grid">
      <div class="test-card test-card--blue" :class="{ selected: selectedType === 'practice' }" @click="selectedType = 'practice'">
        <div class="tc-icon icon-blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
            <rect x="9" y="3" width="6" height="4" rx="1" />
            <path d="M9 12h6M9 16h4" />
          </svg>
        </div>
        <div class="tc-radio" :class="{ on: selectedType === 'practice' }"></div>
        <h3>Practice Test</h3>
        <p>Sharpen your skills with topic-wise and section-wise tests.</p>
        <ul>
          <li>&#10003; Choose specific chapters</li>
          <li>&#10003; Focused practice</li>
        </ul>
      </div>

      <div class="test-card test-card--green" :class="{ selected: selectedType === 'custom' }" @click="selectedType = 'custom'">
        <div class="tc-icon icon-green">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5" />
            <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
        </div>
        <div class="tc-radio" :class="{ on: selectedType === 'custom' }"></div>
        <h3>Custom Test</h3>
        <p>Create your own test by selecting topics, difficulty &amp; more.</p>
        <ul>
          <li>&#10003; Pick your topics</li>
          <li>&#10003; Set difficulty</li>
        </ul>
      </div>

      <div class="test-card test-card--purple" :class="{ selected: selectedType === 'mock' }" @click="selectedType = 'mock'">
        <div class="tc-icon icon-purple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="13" r="8" />
            <path d="M12 9v4l2.5 2.5M9 2h6M12 2v3" />
          </svg>
        </div>
        <div class="tc-radio" :class="{ on: selectedType === 'mock' }"></div>
        <h3>Mock Test</h3>
        <p>Attempt full-length mock tests simulating the exam.</p>
        <ul>
          <li>&#10003; All chapters included</li>
          <li>&#10003; Real exam experience</li>
        </ul>
      </div>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'exams' })">&larr; Back</button>
      <button class="continue-btn" :disabled="!selectedType" @click="goNext">
        Continue &rarr;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import { usePracticeTestStore } from '../../stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

onMounted(() => {
  // Only require store.exam — examType is now pre-set by ExamView when
  // navigating from exam cards, so SelectExamTypeView is no longer needed.
  if (!store.exam) router.replace({ name: 'exams' })
})

const selectedType = ref<'practice' | 'custom' | 'mock' | null>(null)

function goNext(): void {
  if (!selectedType.value) return
  store.setTestType(selectedType.value)
  if (selectedType.value === 'practice') {
    router.push({ name: 'practice-subject' })
  } else if (selectedType.value === 'custom') {
    router.push({ name: 'practice-custom' })
  } else {
    router.push({ name: 'mock-select' })
  }
}
</script>

<style scoped>
.pt-page { max-width: 900px; margin: 0 auto; }

.pt-title { font-size: 19px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.pt-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 20px; }

.test-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

@media (max-width: 800px) {
  .test-type-grid { grid-template-columns: 1fr; }
}

.test-card {
  position: relative;
  border-radius: 14px;
  padding: 18px;
  border: 2px solid transparent;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s;
}

.test-card.selected { border-color: #7c3aed; }

.test-card--blue { background: #eaf2ff; }
.test-card--green { background: #e9f9ef; }
.test-card--purple { background: #efeaff; }

.tc-radio {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
}
.tc-radio.on {
  border-color: #7c3aed;
  background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%);
}

.tc-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}
.tc-icon svg { width: 20px; height: 20px; }

.icon-blue { background: #c7dffe; color: #2563eb; }
.icon-green { background: #bbf7d0; color: #15803d; }
.icon-purple { background: #ddd6fe; color: #7c3aed; }

.test-card h3 { font-size: 15px; font-weight: 700; color: #1e2536; margin: 0 0 6px; }
.test-card p { font-size: 12px; color: #6b7280; margin: 0 0 10px; line-height: 1.4; }

.test-card ul { list-style: none; margin: 0; padding: 0; font-size: 12px; color: #374151; }
.test-card ul li { margin-bottom: 3px; }

.pt-footer { display: flex; justify-content: space-between; align-items: center; }

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

.continue-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>