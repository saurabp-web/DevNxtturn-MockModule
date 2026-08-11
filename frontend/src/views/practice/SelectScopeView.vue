<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Practice Test', to: { name: 'practice-start' } },
        { label: 'Select Subject', to: { name: 'practice-subject' } },
        { label: 'Select Chapter / Test Scope' },
      ]"
      :active-index="2"
    />

    <h2 class="pt-title">Select Chapter / Test Scope</h2>
    <p class="pt-subtitle">Choose how you want to attempt the test</p>

    <div class="scope-layout">
      <div class="scope-options">
        <div
          class="scope-card"
          :class="{ selected: store.scope === 'chapter' }"
          @click="store.setScope('chapter')"
        >
          <div class="scope-radio" :class="{ on: store.scope === 'chapter' }"></div>
          <div class="scope-icon icon-purple">📋</div>
          <h4>Chapter-wise Test</h4>
          <p>Select specific chapters to practice and improve.</p>
          <ul>
            <li>&#10003; Choose specific chapters</li>
            <li>&#10003; Focused practice</li>
          </ul>
        </div>

        <div
          class="scope-card"
          :class="{ selected: store.scope === 'full' }"
          @click="store.setScope('full')"
        >
          <div class="scope-radio" :class="{ on: store.scope === 'full' }"></div>
          <div class="scope-icon icon-green">📄</div>
          <h4>Complete Syllabus Test</h4>
          <p>Attempt test from the complete syllabus.</p>
          <ul>
            <li>&#10003; All chapters included</li>
            <li>&#10003; Real exam experience</li>
          </ul>
        </div>
      </div>

      <div class="selected-subject-card">
        <span class="ssc-label">Selected Subject</span>
        <div class="ssc-row">
          <span>{{ store.subject?.label }}</span>
          <RouterLink :to="{ name: 'practice-subject' }" class="change-link">Change Subject</RouterLink>
        </div>
      </div>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'practice-subject' })">&larr; Back</button>
      <button class="continue-btn" :disabled="!store.scope" @click="goNext">
        Continue &rarr;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import { usePracticeTestStore } from '../../stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

// If someone lands here directly without a subject chosen, send them back.
onMounted(() => {
  if (!store.subject) router.replace({ name: 'practice-subject' })
})

function goNext(): void {
  if (!store.scope) return
  if (store.scope === 'chapter') {
    router.push({ name: 'practice-chapter' })
  } else {
    // Complete Syllabus → goes to prep/loading screen
    router.push({ name: 'practice-full-syllabus' })
  }
}
</script>

<style scoped>
.pt-page { max-width: 880px; margin: 0 auto; }

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

.scope-layout {
  display: grid;
  grid-template-columns: 1fr 1fr 230px;
  gap: 14px;
  margin-bottom: 24px;
  align-items: start;
}

@media (max-width: 800px) {
  .scope-layout { grid-template-columns: 1fr; }
}

.scope-options {
  display: contents;
}

.scope-card {
  position: relative;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  cursor: pointer;
  user-select: none;
}

.scope-card.selected {
  border-color: #7c3aed;
  background: #f5f3ff;
}

.scope-radio {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #d1d5db;
}

.scope-radio.on {
  border-color: #7c3aed;
  background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%);
}

.scope-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  margin-bottom: 12px;
}

.icon-purple { background: #ede9fe; }
.icon-green { background: #d1fae5; }

.scope-card h4 {
  font-size: 14.5px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 4px;
}

.scope-card p {
  font-size: 12.5px;
  color: #6b7280;
  margin: 0 0 12px;
}

.scope-card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 12px;
  color: #374151;
}

.scope-card ul li {
  margin-bottom: 4px;
}

.selected-subject-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px;
}

.ssc-label {
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  display: block;
  margin-bottom: 8px;
}

.ssc-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13.5px;
  font-weight: 700;
  color: #1e2536;
}

.change-link {
  font-size: 12px;
  font-weight: 700;
  color: #7c3aed;
  text-decoration: none;
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

.continue-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>