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
      <h2 class="section-title">Validation Summary</h2>
      <p class="section-subtitle">Validation completed. Review the summary below.</p>

      <!-- Stat cards — matching image -->
      <div class="stats-row">
        <div class="stat-card default">
          <p class="stat-label">Total Rows</p>
          <p class="stat-value">{{ totalRows }}</p>
        </div>
        <div class="stat-card success">
          <p class="stat-label">Valid Questions</p>
          <p class="stat-value">{{ validRows.length }}</p>
        </div>
        <div class="stat-card danger">
          <p class="stat-label">Invalid Questions</p>
          <p class="stat-value">{{ errorRows.length }}</p>
        </div>
        <div class="stat-card warning">
          <p class="stat-label">Duplicate Questions</p>
          <p class="stat-value">{{ duplicateRows.length }}</p>
          <p v-if="mappedDuplicates && duplicateRows.length" class="stat-note">
            Mapped to another exam
          </p>
        </div>
        <div class="stat-card import">
          <p class="stat-label">Imported (Only Valid)</p>
          <p class="stat-value">{{ validRows.length }}</p>
        </div>
      </div>

      <!-- Info note -->
      <div class="info-note">
        <CheckCircleIcon />
        <span v-if="mappedDuplicates && duplicateRows.length">
          {{ validRows.length }} valid questions plus {{ duplicateRows.length }} mapped duplicate question{{ duplicateRows.length === 1 ? '' : 's' }} will be imported. Invalid questions will still be skipped.
        </span>
        <span v-else>
          Only {{ validRows.length }} valid questions will be imported. Invalid and duplicate questions will be skipped.
        </span>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button class="tab" :class="{ active: activeTab === 'valid' }" @click="activeTab = 'valid'">
          Valid Questions ({{ validRows.length }})
        </button>
        <button class="tab" :class="{ active: activeTab === 'errors' }" @click="activeTab = 'errors'">
          Errors ({{ errorRows.length }})
        </button>
        <button class="tab" :class="{ active: activeTab === 'duplicates' }" @click="activeTab = 'duplicates'">
          Duplicates ({{ duplicateRows.length }})
        </button>
      </div>

      <!-- Valid questions table -->
      <div v-if="activeTab === 'valid'" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Question</th>
              <th>Subject</th>
              <th>Chapter</th>
              <th>Type</th>
              <th>Difficulty</th>
              <th>Marks</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in validRows" :key="row.id">
              <td>{{ row.id }}</td>
              <td class="q-cell">{{ row.text }}</td>
              <td>{{ row.subject }}</td>
              <td>{{ row.chapter }}</td>
              <td><span class="pill pill-type">{{ row.type || 'MCQ' }}</span></td>
              <td><span class="pill" :class="'diff-' + String(row.difficulty).toLowerCase()">{{ row.difficulty }}</span></td>
              <td>{{ row.marks }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!validRows.length" class="empty-note">No valid rows found in this file.</p>

        <!-- Pagination hint -->
        <div v-if="validRows.length" class="table-footer">
          <span class="table-count">Showing 1 to {{ Math.min(validRows.length, 5) }} of {{ validRows.length }} valid questions</span>
        </div>
      </div>

      <!-- Errors table -->
      <div v-else-if="activeTab === 'errors'" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Row No.</th>
              <th>Question</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="err in errorRows" :key="err.id">
              <td>{{ err.id }}</td>
              <td class="q-cell">{{ err.text }}</td>
              <td>{{ err.reason }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!errorRows.length" class="empty-note">No invalid rows. 🎉</p>
      </div>

      <!-- Duplicates table -->
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Question</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in duplicateRows" :key="row.id">
              <td>{{ row.id }}</td>
              <td class="q-cell">{{ row.text }}</td>
              <td>{{ row.reason }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="!duplicateRows.length" class="empty-note">No duplicates found.</p>
      </div>

      <p v-if="importError" class="error-banner">{{ importError }}</p>

      <!-- Footer -->
      <div class="footer-actions">
        <button class="back-btn" @click="$emit('previous')">
          <ArrowLeftIcon /> Back
        </button>
        <button
          class="next-btn"
          :disabled="importing || !validRows.length"
          @click="$emit('confirm-import')"
        >
          <template v-if="importing">
            <SpinnerIcon class="spin-icon" /> Importing…
          </template>
          <template v-else>
            Preview Questions
            <ArrowRightIcon />
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ImportWizardHeader from './ImportWizardHeader.vue'

defineProps({
  totalRows:        { type: [Number, String], default: 0 },
  validRows:        { type: Array, default: () => [] },
  errorRows:        { type: Array, default: () => [] },
  duplicateRows:    { type: Array, default: () => [] },
  mappedDuplicates: { type: Boolean, default: false },
  importing:        { type: Boolean, default: false },
  importError:      { type: String, default: '' },
  examName:         { type: String, default: '' },
})
defineEmits(['previous', 'confirm-import', 'change-exam'])

const activeTab = ref('valid')

const CheckCircleIcon = { template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>` }
const ArrowLeftIcon   = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const ArrowRightIcon  = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>` }
const SpinnerIcon     = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>` }
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
  padding: 28px;
}

.section-title { font-size: 17px; font-weight: 700; color: #14121F; margin: 0 0 4px; }
.section-subtitle { font-size: 13px; color: #8A879C; margin: 0 0 20px; }

/* ── Stat Cards ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  border-radius: 12px; border: 1px solid #ECEBF3;
  padding: 16px 18px; background: #F9F8FC;
}
.stat-label { font-size: 12px; color: #8A879C; font-weight: 500; margin: 0 0 6px; }
.stat-value { font-size: 26px; font-weight: 700; color: #14121F; margin: 0; }

.stat-card.success { background: #F0FBF5; border-color: #B8EDD2; }
.stat-card.success .stat-value { color: #1FAE5C; }

.stat-card.danger { background: #FEF2F2; border-color: #FCCFCF; }
.stat-card.danger .stat-value { color: #E5453B; }

.stat-card.warning { background: #FFFBEB; border-color: #FDE68A; }
.stat-card.warning .stat-value { color: #D97706; }
.stat-note {
  font-size: 10.5px; font-weight: 600; color: #D97706; margin: 4px 0 0;
}

.stat-card.import { background: #F5F2FF; border-color: #DDD5FA; }
.stat-card.import .stat-label { color: #6C4CF1; }
.stat-card.import .stat-value { color: #6C4CF1; }

/* Info note */
.info-note {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 10px;
  background: #F0FBF5; border: 1px solid #B8EDD2;
  color: #1FAE5C; font-size: 13px; font-weight: 500;
  margin-bottom: 20px;
}

/* Tabs */
.tabs {
  display: flex; gap: 0;
  border-bottom: 1px solid #ECEBF3;
  margin-bottom: 16px;
}
.tab {
  padding: 10px 0; margin-right: 28px;
  background: none; border: none;
  border-bottom: 2px solid transparent;
  font-size: 13.5px; font-weight: 600;
  color: #8A879C; cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.tab.active { color: #6C4CF1; border-bottom-color: #6C4CF1; }

/* Table */
.table-wrap { border: 1px solid #ECEBF3; border-radius: 12px; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 12px 16px;
  font-size: 11.5px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.3px;
  color: #8A879C; background: #F9F8FC;
  border-bottom: 1px solid #ECEBF3; white-space: nowrap;
}
.data-table td {
  padding: 13px 16px; font-size: 13px; color: #14121F;
  border-bottom: 1px solid #F2F1F7;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.q-cell { max-width: 280px; }

.table-footer {
  padding: 12px 16px;
  border-top: 1px solid #ECEBF3;
  font-size: 12.5px; color: #8A879C;
}
.table-count {}

.pill {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
}
.pill-type { background: #EDE9FE; color: #6C4CF1; }
.diff-easy   { background: #E1FAEC; color: #1FAE5C; }
.diff-medium { background: #FFF3DE; color: #E08A00; }
.diff-hard   { background: #FDE9E8; color: #E5453B; }

.empty-note { padding: 28px; text-align: center; color: #8A879C; font-size: 13px; }

.error-banner {
  margin-top: 16px; padding: 12px 16px;
  border-radius: 10px; background: #FDE9E8;
  border: 1px solid #F6C6C3; color: #B3261E;
  font-size: 13px; font-weight: 600;
}

/* Footer */
.footer-actions {
  display: flex; justify-content: space-between;
  margin-top: 24px;
}
.back-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 9px;
  border: 1px solid #ECEBF3; background: #fff;
  color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer;
}
.back-btn:hover { background: #F6F5FB; }
.next-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 11px 24px; border-radius: 9px;
  background: #6C4CF1; color: #fff;
  font-size: 13.5px; font-weight: 600; cursor: pointer; border: none;
}
.next-btn:hover:not(:disabled) { background: #5B3EE0; }
.next-btn:disabled { background: #D8D5E8; cursor: not-allowed; }
.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .table-wrap { overflow-x: auto; }
  .data-table { min-width: 640px; }
}
</style>