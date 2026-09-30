<template>
  <div class="import-card">
    <div class="card-header">
      <div>
        <h1 class="page-title">Import Questions</h1>
        <p class="page-subtitle">Map columns from your file with system fields.</p>
      </div>
      <button class="back-btn">
        <ArrowLeftIcon />
        Back to Question Bank
      </button>
    </div>

    <div class="card">
      <div class="progress-track">
        <div class="progress-item">
          <div class="progress-circle done"><CheckIcon /></div>
          <span class="progress-label done">Upload File</span>
        </div>
        <div class="progress-line filled" />
        <div class="progress-item">
          <div class="progress-circle active">2</div>
          <span class="progress-label active">Map Columns</span>
        </div>
        <div class="progress-line" />
        <div class="progress-item">
          <div class="progress-circle">3</div>
          <span class="progress-label">Preview &amp; Validate</span>
        </div>
        <div class="progress-line" />
        <div class="progress-item">
          <div class="progress-circle">4</div>
          <span class="progress-label">Import</span>
        </div>
      </div>

      <div class="file-summary">
        <div class="file-summary-left">
          <div class="file-icon"><FileIcon /></div>
          <div>
            <p class="file-label">Uploaded File</p>
            <p class="file-name">{{ fileName }} <span class="file-rows">{{ totalRows }} rows</span></p>
          </div>
        </div>
        <button class="change-file-btn" @click="$emit('previous')">Change File</button>
      </div>

      <!--
        CHANGED: the backend's validate endpoint already parses and maps
        columns itself (it requires fixed header names — see
        BulkUploadValidateView's REQUIRED_COLUMNS check), so there is no
        separate "map my arbitrary headers to system fields" step on the
        server today. This table is left as a read-only confirmation view
        of the expected template columns rather than fake editable
        selects, so it doesn't imply a mapping that never gets sent
        anywhere. If you want real column re-mapping, the backend needs
        a matching endpoint that accepts a mapping dict.
      -->
      <p class="mapping-note">
        Your file's columns are matched to these fields automatically based on
        the template headers. Use the exact column names from the template for
        best results.
      </p>
      <div class="mapping-table">
        <div class="mapping-row mapping-head">
          <span>System Field</span>
          <span>Required?</span>
        </div>
        <div v-for="row in templateFields" :key="row.field" class="mapping-row">
          <span class="file-col">{{ row.field }}</span>
          <span class="preview-val">{{ row.required ? 'Required' : 'Optional' }}</span>
        </div>
      </div>

      <div class="footer-actions">
        <button class="prev-btn" @click="$emit('previous')">
          <ArrowLeftIcon />
          Previous Step
        </button>
        <button class="next-btn" @click="$emit('next')">
          Next Step
          <ArrowRightIcon />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  fileName: { type: String, default: '' },
  totalRows: { type: [Number, String], default: 0 },
})
defineEmits(['previous', 'next'])

// Mirrors BulkUploadTemplateView's headers/README sheet on the backend.
const templateFields = [
  { field: 'question_text', required: true },
  { field: 'option_a', required: true },
  { field: 'option_b', required: true },
  { field: 'option_c', required: true },
  { field: 'option_d', required: true },
  { field: 'option_e', required: false },
  { field: 'correct_answer', required: true },
  { field: 'subject', required: false },
  { field: 'chapter', required: false },
  { field: 'question_type', required: false },
  { field: 'difficulty', required: false },
  { field: 'marks', required: false },
  { field: 'negative_marks', required: false },
  { field: 'explanation', required: false },
  { field: 'hint', required: false },
]

const CheckIcon = { template: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>` }
const FileIcon = { template: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>` }
const ArrowLeftIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const ArrowRightIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>` }
</script>

<style scoped>
* { box-sizing: border-box; }
.import-card { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1200px; margin: 0 auto; padding: 24px; }

.card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; gap: 16px; flex-wrap: wrap; }
.page-title { font-size: 24px; font-weight: 700; color: #14121F; margin: 0 0 4px; }
.page-subtitle { font-size: 13.5px; color: #8A879C; margin: 0; }
.back-btn { display: flex; align-items: center; gap: 8px; padding: 9px 16px; border-radius: 9px; border: 1px solid #ECEBF3; background: #fff; color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.back-btn:hover { background: #F6F5FB; }
.card { background: #fff; border-radius: 16px; border: 1px solid #ECEBF3; padding: 24px; }

.progress-track { display: flex; align-items: center; margin-bottom: 4px; }
.progress-item { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.progress-circle { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: #F3F2F9; color: #A6A4B4; border: 1.5px solid #E4E2ED; }
.progress-circle.active { background: #6C4CF1; color: #fff; border: none; }
.progress-circle.done { background: #E9FBF0; color: #1FAE5C; border: 1.5px solid #1FAE5C; }
.progress-label { font-size: 13.5px; font-weight: 600; color: #A6A4B4; white-space: nowrap; }
.progress-label.active { color: #14121F; }
.progress-label.done { color: #1FAE5C; }
.progress-line { width: 56px; height: 2px; background: #E4E2ED; margin: 0 8px; flex-shrink: 0; }
.progress-line.filled { background: #1FAE5C; }

.file-summary { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-radius: 12px; background: #F9F8FC; border: 1px solid #ECEBF3; margin: 24px 0 12px; }
.file-summary-left { display: flex; align-items: center; gap: 12px; }
.file-icon { width: 38px; height: 38px; border-radius: 9px; background: #F1EDFF; color: #6C4CF1; display: flex; align-items: center; justify-content: center; }
.file-label { font-size: 12px; color: #8A879C; margin: 0 0 2px; }
.file-name { font-size: 13.5px; font-weight: 600; color: #14121F; margin: 0; }
.file-rows { font-weight: 400; color: #8A879C; margin-left: 6px; }
.change-file-btn { padding: 8px 16px; border-radius: 8px; border: 1px solid #ECEBF3; background: #fff; font-size: 13px; font-weight: 600; color: #524F6B; cursor: pointer; }
.change-file-btn:hover { background: #F6F5FB; }

.mapping-note { font-size: 12.5px; color: #8A879C; margin: 0 0 14px; }

.mapping-table { border: 1px solid #ECEBF3; border-radius: 12px; overflow: hidden; }
.mapping-row { display: grid; grid-template-columns: 1fr 1fr; align-items: center; gap: 16px; padding: 13px 18px; border-bottom: 1px solid #ECEBF3; }
.mapping-row:last-child { border-bottom: none; }
.mapping-head { background: #F9F8FC; font-size: 11.5px; font-weight: 700; letter-spacing: 0.3px; color: #8A879C; text-transform: uppercase; padding: 11px 18px; }
.file-col { font-size: 13.5px; font-weight: 600; color: #14121F; }
.preview-val { font-size: 13px; color: #8A879C; }

.footer-actions { display: flex; justify-content: space-between; margin-top: 28px; }
.prev-btn, .next-btn { display: flex; align-items: center; gap: 8px; padding: 11px 22px; border-radius: 10px; font-size: 13.5px; font-weight: 600; border: none; cursor: pointer; }
.prev-btn { background: #fff; border: 1px solid #ECEBF3; color: #524F6B; }
.prev-btn:hover { background: #F6F5FB; }
.next-btn { background: #6C4CF1; color: #fff; }
.next-btn:hover { background: #5B3EE0; }

@media (max-width: 760px) { .mapping-row { grid-template-columns: 1fr; gap: 6px; } }
</style>