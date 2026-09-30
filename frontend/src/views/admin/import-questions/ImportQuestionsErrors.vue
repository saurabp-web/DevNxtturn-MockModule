<template>
  <div class="import-page">
    <ImportWizardHeader
      :steps="['Select Exam', 'Upload File', 'Validate & Preview', 'Import Valid Questions']"
      :current-step="2"
      :exam-name="examName"
      @change-exam="$emit('change-exam')"
    />

    <div class="card">
      <h2 class="section-title">Validation Summary</h2>
      <p class="section-subtitle">Validation completed. Review the summary below.</p>

      <!-- Stat cards -->
      <div class="stats-row">
        <div class="stat-card default">
          <p class="stat-label">Total Rows</p>
          <p class="stat-value">{{ totalRows }}</p>
        </div>
        <div class="stat-card success">
          <p class="stat-label">Valid Questions</p>
          <p class="stat-value">{{ validCount }}</p>
        </div>
        <div class="stat-card danger">
          <p class="stat-label">Invalid Questions</p>
          <p class="stat-value">{{ invalidCount }}</p>
        </div>
        <div class="stat-card warning">
          <p class="stat-label">Duplicate Questions</p>
          <p class="stat-value">{{ duplicateCount }}</p>
        </div>
        <div class="stat-card import">
          <p class="stat-label">Imported (Only Valid)</p>
          <p class="stat-value">{{ validCount }}</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button class="tab" :class="{ active: activeTab === 'valid' }" @click="activeTab = 'valid'">
          Valid Questions ({{ validCount }})
        </button>
        <button class="tab" :class="{ active: activeTab === 'errors' }" @click="activeTab = 'errors'">
          Errors ({{ invalidCount }})
        </button>
      </div>

      <!-- Errors table -->
      <div v-if="activeTab === 'errors'" class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Row No.</th>
              <th>Error Type</th>
              <th>Error Description</th>
              <th>Data Found</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="err in errorRows" :key="err.id">
              <td>{{ err.id }}</td>
              <td>{{ err.rowNo }}</td>
              <td><span class="pill" :class="'err-' + err.type.toLowerCase().replace(' ', '-')">{{ err.type }}</span></td>
              <td>{{ err.description }}</td>
              <td class="mono">{{ err.dataFound }}</td>
            </tr>
          </tbody>
        </table>
        <div class="table-footer">
          <button class="download-btn"><DownloadIcon /> Download Error Report</button>
        </div>
      </div>

      <!-- Valid table -->
      <div v-else class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Question</th>
              <th>Subject</th>
              <th>Chapter</th>
              <th>Difficulty</th>
              <th>Marks</th>
              <th>Negative Marks</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in validRows" :key="row.id">
              <td>{{ row.id }}</td>
              <td class="q-cell">{{ row.question }}</td>
              <td>{{ row.subject }}</td>
              <td>{{ row.chapter }}</td>
              <td><span class="pill" :class="'diff-' + row.difficulty.toLowerCase()">{{ row.difficulty }}</span></td>
              <td>{{ row.marks }}</td>
              <td>{{ row.negativeMarks }}</td>
              <td><span class="pill status-valid">Valid</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div class="footer-actions">
        <button class="back-btn" @click="$emit('previous')">
          <ArrowLeftIcon /> Previous Step
        </button>
        <button class="next-btn" @click="$emit('next')">
          Next Step <ArrowRightIcon />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ImportWizardHeader from './ImportWizardHeader.vue'

defineProps({
  totalRows:     { type: [Number, String], default: '150' },
  validCount:    { type: [Number, String], default: '120' },
  invalidCount:  { type: [Number, String], default: 15 },
  duplicateCount:{ type: [Number, String], default: 10 },
  examName:      { type: String, default: '' },
})
defineEmits(['previous', 'next', 'change-exam'])

const activeTab = ref('errors')

const errorRows = ref([
  { id: 1, rowNo: 15,  type: 'Missing Field',  description: 'Question text is required.', dataFound: '(blank)' },
  { id: 2, rowNo: 27,  type: 'Invalid Option', description: 'Correct option must be one of A, B, C, D.', dataFound: 'E' },
  { id: 3, rowNo: 45,  type: 'Missing Field',  description: 'Subject is required.', dataFound: '(blank)' },
  { id: 4, rowNo: 78,  type: 'Invalid Marks',  description: 'Marks must be a positive number.', dataFound: '-4' },
  { id: 5, rowNo: 102, type: 'Missing Field',  description: 'Correct option is required.', dataFound: '(blank)' },
])

const validRows = ref([
  { id: 1, question: 'What is the value of sin 90°?', subject: 'Mathematics', chapter: 'Trigonometry', difficulty: 'Easy', marks: 4, negativeMarks: 1 },
  { id: 2, question: 'If cos θ = 0, then the value of θ is:', subject: 'Mathematics', chapter: 'Trigonometry', difficulty: 'Medium', marks: 4, negativeMarks: 1 },
  { id: 3, question: 'The unit of force is:', subject: 'Physics', chapter: 'Units & Measurements', difficulty: 'Easy', marks: 4, negativeMarks: 1 },
])

const DownloadIcon   = { template: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>` }
const ArrowLeftIcon  = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const ArrowRightIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>` }
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

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px; margin-bottom: 20px;
}
.stat-card {
  border-radius: 12px; border: 1px solid #ECEBF3;
  padding: 16px 18px; background: #F9F8FC;
}
.stat-label { font-size: 12px; color: #8A879C; font-weight: 500; margin: 0 0 6px; }
.stat-value { font-size: 26px; font-weight: 700; color: #14121F; margin: 0; }
.stat-card.success { background: #F0FBF5; border-color: #B8EDD2; }
.stat-card.success .stat-value { color: #1FAE5C; }
.stat-card.danger  { background: #FEF2F2; border-color: #FCCFCF; }
.stat-card.danger  .stat-value { color: #E5453B; }
.stat-card.warning { background: #FFFBEB; border-color: #FDE68A; }
.stat-card.warning .stat-value { color: #D97706; }
.stat-card.import  { background: #F5F2FF; border-color: #DDD5FA; }
.stat-card.import  .stat-value { color: #6C4CF1; }

/* Tabs */
.tabs { display: flex; border-bottom: 1px solid #ECEBF3; margin-bottom: 16px; }
.tab {
  padding: 10px 0; margin-right: 28px;
  background: none; border: none; border-bottom: 2px solid transparent;
  font-size: 13.5px; font-weight: 600; color: #8A879C; cursor: pointer;
}
.tab.active { color: #6C4CF1; border-bottom-color: #6C4CF1; }

/* Table */
.table-wrap { border: 1px solid #ECEBF3; border-radius: 12px; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 12px 16px;
  font-size: 11.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.3px; color: #8A879C;
  background: #F9F8FC; border-bottom: 1px solid #ECEBF3; white-space: nowrap;
}
.data-table td {
  padding: 13px 16px; font-size: 13px; color: #14121F;
  border-bottom: 1px solid #F2F1F7;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.q-cell { max-width: 300px; }
.mono { font-family: 'SFMono-Regular', Consolas, monospace; color: #8A879C; }

.table-footer { padding: 14px 16px; border-top: 1px solid #ECEBF3; }
.download-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 16px; border-radius: 9px;
  border: 1px solid #ECEBF3; background: #fff;
  font-size: 13px; font-weight: 600; color: #524F6B; cursor: pointer;
}
.download-btn:hover { background: #F6F5FB; }

.pill {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
}
.diff-easy { background: #E1FAEC; color: #1FAE5C; }
.diff-medium { background: #FFF3DE; color: #E08A00; }
.diff-hard { background: #FDE9E8; color: #E5453B; }
.status-valid { background: #E1FAEC; color: #1FAE5C; }
.err-missing-field { background: #FDE9E8; color: #E5453B; }
.err-invalid-option { background: #FFF3DE; color: #E08A00; }
.err-invalid-marks { background: #FFF3DE; color: #E08A00; }

/* Footer */
.footer-actions { display: flex; justify-content: space-between; margin-top: 24px; }
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
.next-btn:hover { background: #5B3EE0; }

@media (max-width: 900px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .table-wrap { overflow-x: auto; }
  .data-table { min-width: 640px; }
}
</style>