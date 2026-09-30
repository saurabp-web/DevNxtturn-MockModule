<template>
  <div class="import-page">
    <!-- Stepper + Exam Banner -->
    <ImportWizardHeader
      :steps="['Select Exam', 'Upload File', 'Validate & Preview', 'Import Valid Questions']"
      :current-step="2"
      :exam-name="examName"
      @change-exam="$emit('change-exam')"
    />

    <!-- Card -->
    <div class="card">
      <div class="progress-layout">
        <!-- Left: step checklist -->
        <div class="steps-list">
          <div
            v-for="(step, i) in progressSteps"
            :key="step.label"
            class="progress-step"
            :class="step.status"
          >
            <div class="ps-circle">
              <CheckIcon v-if="step.status === 'done'" />
              <SpinnerIcon v-else-if="step.status === 'active'" class="spinning" />
            </div>
            <div class="ps-body">
              <span class="ps-label">{{ step.label }}</span>
              <span class="ps-status">{{ statusText(step.status) }}</span>
            </div>
          </div>
        </div>

        <!-- Right: animated illustration -->
        <div class="anim-panel">
          <div class="anim-icon">
            <FileSearchIcon />
          </div>
          <p class="anim-title">Validating your questions...</p>
          <p class="anim-sub">We are checking the file for errors, duplicates and invalid data.</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="footer-actions">
        <button class="back-btn" @click="$emit('back')">
          <ArrowLeftIcon /> Back
        </button>
        <button class="cancel-btn" @click="$emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ImportWizardHeader from './ImportWizardHeader.vue'

defineProps({
  total:     { type: [Number, String], default: 0 },
  examName:  { type: String, default: '' },
})
defineEmits(['back', 'cancel', 'change-exam'])

// Simulate progress states: done / active / pending
const progressSteps = ref([
  { label: 'Reading file',        status: 'done' },
  { label: 'Validating data',     status: 'active' },
  { label: 'Checking duplicates', status: 'pending' },
  { label: 'Preparing preview',   status: 'pending' },
])

function statusText(s) {
  if (s === 'done')    return 'Completed'
  if (s === 'active')  return 'In progress'
  return 'Pending'
}

const CheckIcon    = { template: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>` }
const SpinnerIcon  = { template: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>` }
const ArrowLeftIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const FileSearchIcon = { template: `<svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><circle cx="11" cy="15" r="2"/><path d="m13.5 17.5 2 2"/></svg>` }
</script>

<style scoped>
* { box-sizing: border-box; }
.import-page {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  max-width: 1100px; margin: 0 auto; padding: 28px 24px;
}

.card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #ECEBF3;
  padding: 36px 28px;
}

.progress-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  align-items: center;
}

/* Step checklist */
.steps-list { display: flex; flex-direction: column; gap: 0; }
.progress-step {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid #F2F1F7;
}
.progress-step:last-child { border-bottom: none; }

.ps-circle {
  width: 28px; height: 28px; border-radius: 50%;
  border: 1.5px solid #E4E2ED;
  background: #F9F8FC;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.progress-step.done .ps-circle    { background: #E1FAEC; border-color: #1FAE5C; color: #1FAE5C; }
.progress-step.active .ps-circle  { background: #F1EDFF; border-color: #6C4CF1; color: #6C4CF1; }
.progress-step.pending .ps-circle { background: #F9F8FC; border-color: #E4E2ED; color: #A6A4B4; }

.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.ps-body { display: flex; justify-content: space-between; align-items: center; flex: 1; }
.ps-label { font-size: 13.5px; font-weight: 600; color: #14121F; }
.ps-status { font-size: 12.5px; color: #A6A4B4; }
.progress-step.done   .ps-status  { color: #1FAE5C; }
.progress-step.active .ps-status  { color: #6C4CF1; }

/* Animation panel */
.anim-panel {
  display: flex; flex-direction: column;
  align-items: center; text-align: center;
  padding: 24px;
}
.anim-icon {
  width: 100px; height: 100px; border-radius: 20px;
  background: #F1EDFF; color: #6C4CF1;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 24px;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(108, 76, 241, 0.15); }
  50%       { box-shadow: 0 0 0 12px rgba(108, 76, 241, 0); }
}
.anim-title { font-size: 17px; font-weight: 700; color: #14121F; margin: 0 0 8px; }
.anim-sub { font-size: 13px; color: #8A879C; margin: 0; max-width: 280px; }

/* Footer */
.footer-actions {
  display: flex; justify-content: space-between;
  margin-top: 32px;
}
.back-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 9px;
  border: 1px solid #ECEBF3; background: #fff;
  color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer;
}
.back-btn:hover { background: #F6F5FB; }
.cancel-btn {
  padding: 10px 20px; border-radius: 9px;
  border: 1px solid #ECEBF3; background: #fff;
  color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer;
}
.cancel-btn:hover { background: #F6F5FB; }

@media (max-width: 720px) {
  .progress-layout { grid-template-columns: 1fr; }
  .anim-panel { display: none; }
}
</style>