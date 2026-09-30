<template>
  <div class="import-page">
    <!-- Stepper + Exam Banner -->
    <ImportWizardHeader
      :steps="['Select Exam', 'Upload File', 'Validate & Preview', 'Import Valid Questions']"
      :current-step="4"
      :exam-name="examName"
      :allow-change-exam="false"
    />

    <!-- Card -->
    <div class="card">
      <div class="success-layout">
        <!-- Left: success illustration -->
        <div class="success-panel">
          <div class="success-icon">
            <CheckBigIcon />
          </div>
          <h2 class="success-title">Import Successful!</h2>
          <p class="success-sub">{{ imported }} valid questions are now added to this exam.</p>
        </div>

        <!-- Right: summary table -->
        <div class="summary-panel">
          <div class="summary-row">
            <span class="summary-label">Total Rows</span>
            <span class="summary-value">{{ total }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Valid Questions Imported</span>
            <span class="summary-value success">{{ imported }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Invalid Questions Skipped</span>
            <span class="summary-value danger">{{ failed }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Duplicate Questions {{ mapped > 0 ? 'Mapped' : 'Skipped' }}</span>
            <span class="summary-value warning">{{ duplicates }}</span>
          </div>
          <p v-if="mapped > 0" class="summary-footnote">
            <MapIcon /> {{ mapped }} duplicate question{{ mapped === 1 ? '' : 's' }} mapped to another exam
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="footer-actions">
        <button class="back-btn" @click="$emit('go-to-mock-test')">
          <ArrowLeftIcon /> Back to Mock Tests
        </button>
        <button class="goto-btn" @click="$emit('go-to-question-bank')">
          Go to Mock Test
          <ArrowRightIcon />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import ImportWizardHeader from './ImportWizardHeader.vue'

defineProps({
  total:      { type: [Number, String], default: 0 },
  imported:   { type: [Number, String], default: 0 },
  failed:     { type: [Number, String], default: 0 },
  duplicates: { type: [Number, String], default: 0 },
  mapped:     { type: [Number, String], default: 0 },
  examName:   { type: String, default: '' },
})
defineEmits(['go-to-question-bank', 'go-to-mock-test'])

const CheckBigIcon   = { template: `<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>` }
const ArrowLeftIcon  = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const ArrowRightIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>` }
const MapIcon        = { template: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>` }
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
  padding: 48px 28px 28px;
}

.success-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: center;
  margin-bottom: 32px;
}

/* Success panel */
.success-panel {
  display: flex; flex-direction: column;
  align-items: center; text-align: center;
  padding: 24px;
}
.success-icon {
  width: 96px; height: 96px; border-radius: 50%;
  background: #E1FAEC; color: #1FAE5C;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 24px;
}
.success-title { font-size: 22px; font-weight: 700; color: #14121F; margin: 0 0 8px; }
.success-sub { font-size: 13.5px; color: #8A879C; margin: 0; }

/* Summary table */
.summary-panel {
  border: 1px solid #ECEBF3;
  border-radius: 12px; overflow: hidden;
}
.summary-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #F2F1F7;
}
.summary-row:last-child { border-bottom: none; }
.summary-label { font-size: 13.5px; color: #524F6B; }
.summary-value { font-size: 15px; font-weight: 700; color: #14121F; }
.summary-value.success { color: #1FAE5C; }
.summary-value.danger  { color: #E5453B; }
.summary-value.warning { color: #D97706; }
.summary-footnote {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 20px 14px;
  font-size: 11.5px; font-weight: 600; color: #D97706; margin: 0;
}

/* Footer */
.footer-actions {
  display: flex; justify-content: space-between;
}
.back-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 9px;
  border: 1px solid #ECEBF3; background: #fff;
  color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer;
}
.back-btn:hover { background: #F6F5FB; }
.goto-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 11px 24px; border-radius: 9px;
  background: #6C4CF1; color: #fff;
  font-size: 13.5px; font-weight: 600; cursor: pointer; border: none;
}
.goto-btn:hover { background: #5B3EE0; }

@media (max-width: 720px) {
  .success-layout { grid-template-columns: 1fr; }
}
</style>