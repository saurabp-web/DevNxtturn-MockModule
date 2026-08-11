<template>
  <div class="pt-page">
    <div class="pt-page-header">
      <button class="back-btn" @click="router.push({ name: 'exams' })">&larr;</button>
      <h2>Practice Test</h2>
    </div>

    <h3 class="section-label">Quick Actions</h3>

    <div class="quick-actions">
      <div class="qa-card qa-blue qa-selected">
        <div class="qa-icon icon-blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
            <rect x="9" y="3" width="6" height="4" rx="1" />
            <path d="M9 12h6M9 16h4" />
          </svg>
        </div>
        <h4>Practice Test</h4>
        <p>Sharpen your skills with topic-wise and section-wise tests.</p>
        <button class="qa-btn btn-blue" @click="startPractice">Start Practice &rarr;</button>
      </div>

      <div class="qa-card qa-green">
        <div class="qa-icon icon-green">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5" />
            <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
        </div>
        <h4>Custom Test</h4>
        <p>Create your own test by selecting topics, difficulty &amp; more.</p>
        <button class="qa-btn btn-green" @click="startCustom">Create Test &rarr;</button>
      </div>

      <div class="qa-card qa-purple">
        <div class="qa-icon icon-purple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="13" r="8" />
            <path d="M12 9v4l2.5 2.5M9 2h6M12 2v3" />
          </svg>
        </div>
        <h4>Mock Test</h4>
        <p>Attempt full-length mock tests simulating the exam.</p>
        <button class="qa-btn btn-purple" @click="startMock">Start Mock &rarr;</button>
      </div>
    </div>

    <div class="available-exams-card">
      <div class="ae-header">
        <h3>Available Exams &amp; Mock Tests</h3>
        <RouterLink :to="{ name: 'exams' }" class="view-all">View All</RouterLink>
      </div>

      <div class="ae-row" v-for="exam in previewExams" :key="exam.id">
        <div class="ae-logo">{{ exam.shortLabel }}</div>
        <div class="ae-info">
          <h4>{{ exam.name }}</h4>
          <div class="ae-meta">
            Full Length Test &bull; {{ exam.questions }} Questions &bull; {{ exam.duration }}
          </div>
          <div class="ae-badges">
            <span class="badge" :class="`badge-${exam.difficulty}`">{{ exam.difficultyLabel }}</span>
            <span class="badge badge-language">{{ exam.language }}</span>
          </div>
        </div>
        <div class="ae-actions">
          <button class="view-details-btn">View Details</button>
          <button class="bookmark-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { usePracticeTestStore } from '@/stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

function startPractice(): void {
  store.setTestType('practice')
  router.push({ name: 'practice-subject' })
}

function startCustom(): void {
  store.setTestType('custom')
  router.push({ name: 'practice-custom' })
}

function startMock(): void {
  store.setTestType('mock')
  router.push({ name: 'practice-subject' })
}

// Static preview data for the two example rows on this landing screen.
const previewExams = [
  {
    id: 1,
    shortLabel: 'UPSC',
    name: 'UPSC Civil Services Preliminary Exam 2024',
    questions: 200,
    duration: '2 Hours',
    difficulty: 'hard',
    difficultyLabel: 'Hard',
    language: 'English',
  },
  {
    id: 2,
    shortLabel: 'SSC',
    name: 'SSC CGL Tier 1 Mock Test 2024',
    questions: 100,
    duration: '60 Minutes',
    difficulty: 'medium',
    difficultyLabel: 'Medium',
    language: 'English',
  },
]
</script>

<style scoped>
.pt-page {
  max-width: 760px;
  margin: 0 auto;
}

.pt-page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.back-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  user-select: none;
  font-size: 14px;
}

.pt-page-header h2 {
  font-size: 18px;
  font-weight: 800;
  color: #7c3aed;
  margin: 0;
}

.section-label {
  font-size: 13px;
  font-weight: 700;
  color: #6b7280;
  margin: 0 0 10px;
}

@media (max-width: 700px) {
  .quick-actions { grid-template-columns: 1fr; }
}

.qa-card {
  border-radius: 14px;
  padding: 16px;
  border: 2px solid transparent;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

.qa-blue { background: #eaf2ff; }
.qa-green { background: #e9f9ef; }
.qa-purple { background: #efeaff; }
.qa-selected { border-color: #2563eb; }

.qa-icon {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.qa-icon svg { width: 20px; height: 20px; }

.icon-blue { background: #dbeafe; color: #2563eb; }
.icon-green { background: #d1fae5; color: #059669; }
.icon-purple { background: #ede9fe; color: #7c3aed; }

.qa-card h4 {
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 4px;
}

.qa-card p {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 12px;
  line-height: 1.4;
}

.qa-btn {
  border: none;
  color: #fff;
  font-size: 12.5px;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  align-self: flex-start;
}

.btn-blue { background: #2563eb; }
.btn-green { background: #059669; }
.btn-purple { background: #7c3aed; }

.available-exams-card {
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 14px;
  padding: 18px;
}

.ae-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.ae-header h3 {
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.view-all {
  font-size: 12.5px;
  font-weight: 700;
  color: #7c3aed;
  text-decoration: none;
}

.ae-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-top: 1px solid #f3f4f6;
}

.ae-row:first-of-type {
  border-top: none;
}

.ae-logo {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 800;
  color: #4b5563;
  flex-shrink: 0;
}

.ae-info {
  flex: 1;
  min-width: 0;
}

.ae-info h4 {
  font-size: 13.5px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 3px;
}

.ae-meta {
  font-size: 11.5px;
  color: #6b7280;
  margin-bottom: 8px;
}

.ae-badges {
  display: flex;
  gap: 6px;
}

.badge {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.badge-easy { background: #d1fae5; color: #047857; }
.badge-medium { background: #fef3c7; color: #b45309; }
.badge-hard { background: #fee2e2; color: #b91c1c; }
.badge-language { background: #ede9fe; color: #6d28d9; }

.ae-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.view-details-btn {
  background: #fff;
  border: 1px solid #7c3aed;
  color: #7c3aed;
  font-weight: 700;
  font-size: 12px;
  padding: 7px 12px;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.bookmark-btn {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.bookmark-btn svg { width: 14px; height: 14px; }
</style>