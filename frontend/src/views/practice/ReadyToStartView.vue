<template>
  <div class="pt-page">
    <PracticeBreadcrumb :crumbs="breadcrumbs" :active-index="breadcrumbs.length - 1" />

    <div class="ready-layout">
      <div class="ready-art">
        <svg viewBox="0 0 200 200" fill="none">
          <circle cx="100" cy="100" r="90" fill="#f5f3ff" />
          <rect x="60" y="50" width="80" height="100" rx="8" fill="#fff" stroke="#7c3aed" stroke-width="3" />
          <rect x="80" y="40" width="40" height="20" rx="4" fill="#7c3aed" />
          <path d="M75 80h50M75 95h50M75 110h30" stroke="#7c3aed" stroke-width="3" stroke-linecap="round" />
          <circle cx="135" cy="135" r="28" fill="#7c3aed" />
          <path d="M135 122v13l9 9" stroke="#fff" stroke-width="3" stroke-linecap="round" />
        </svg>
      </div>

      <div class="ready-content">
        <h2>You&rsquo;re All Set!</h2>
        <p>Review your test details before you begin.</p>

        <div class="summary-card">
          <div class="summary-row">
            <span>Subject</span>
            <strong>{{ store.subject?.label || '—' }}</strong>
          </div>
          <div class="summary-row">
            <span>Chapter</span>
            <strong>{{ store.chapter?.label || 'Full Syllabus' }}</strong>
          </div>
          <div class="summary-row">
            <span>Mode</span>
            <strong>{{ store.mode === 'test' ? 'Test Mode' : 'Practice Mode' }}</strong>
          </div>
          <div class="summary-row">
            <span>Questions</span>
            <strong>{{ store.questionCount }}</strong>
          </div>
          <div class="summary-row">
            <span>Duration</span>
            <strong>{{ store.durationMinutes }} Minutes</strong>
          </div>
          <div class="summary-row">
            <span>Difficulty</span>
            <strong>{{ store.difficulty }}</strong>
          </div>
        </div>

        <div class="pt-footer">
          <button class="back-btn" @click="router.push({ name: 'practice-mode' })">&larr; Back</button>
          <button class="begin-btn" @click="beginTest">Begin Test &rarr;</button>
        </div>
      </div>
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
  if (!store.subject || !store.scope || !store.mode) {
    router.replace({ name: 'practice-start' })
  }
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
  base.push({ label: 'Choose Mode', to: { name: 'practice-mode' } })
  base.push({ label: 'Start Test' })
  return base
})

function beginTest(): void {
  router.push({ name: 'practice-test' })
}
</script>

<style scoped>
.pt-page { max-width: 900px; margin: 0 auto; }

.ready-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 32px;
  align-items: center;
  margin-top: 20px;
}

@media (max-width: 700px) {
  .ready-layout { grid-template-columns: 1fr; }
}

.ready-art svg {
  width: 100%;
  height: auto;
}

.ready-content h2 {
  font-size: 22px;
  font-weight: 800;
  color: #1e2536;
  margin: 0 0 4px;
}

.ready-content > p {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 18px;
}

.summary-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  margin-bottom: 22px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #374151;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-row strong {
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

.begin-btn {
  background: #7c3aed;
  border: none;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  padding: 10px 22px;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
}
</style>