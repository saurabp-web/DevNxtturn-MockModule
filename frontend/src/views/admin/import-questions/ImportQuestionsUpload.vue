<template>
  <div class="import-card">
    <div class="card-header">
      <div>
        <h1 class="page-title">Import Questions</h1>
        <p class="page-subtitle">Upload questions in bulk using Excel or CSV file.</p>
      </div>
      <button class="back-btn">
        <ArrowLeftIcon />
        Back to Question Bank
      </button>
    </div>

    <div class="card">
      <div class="progress-track">
        <div class="progress-item">
          <div class="progress-circle active">1</div>
          <span class="progress-label active">Upload File</span>
        </div>
        <div class="progress-line" />
        <div class="progress-item">
          <div class="progress-circle">2</div>
          <span class="progress-label">Map Columns</span>
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

      <div class="layout-grid">
        <div class="info-panel">
          <h3 class="panel-title">Steps to Import</h3>
          <ol class="info-list">
            <li v-for="(s, i) in howTo" :key="i" class="info-row">
              <span class="info-num">{{ i + 1 }}</span>
              <div>
                <p class="info-title">{{ s.title }}</p>
                <p class="info-desc">{{ s.desc }}</p>
              </div>
            </li>
          </ol>
        </div>

        <div class="drop-panel">
          <div
            class="dropzone"
            :class="{ dragging: isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <template v-if="submitting">
              <div class="dropzone-icon spin"><UploadCloudIcon /></div>
              <p class="dropzone-title">Validating your file…</p>
              <p class="dropzone-or">This won't take long.</p>
            </template>
            <template v-else>
              <div class="dropzone-icon"><UploadCloudIcon /></div>
              <p class="dropzone-title">Drag and drop your file here</p>
              <p class="dropzone-or">or</p>
              <label class="choose-file-btn">
                Choose File
                <input type="file" accept=".xlsx,.xls,.csv" hidden @change="onFileSelected" />
              </label>
              <p class="dropzone-formats">Supports .xlsx, .xls, .csv files</p>
              <p class="dropzone-max">Maximum file size: 10MB</p>
            </template>
          </div>
        </div>
      </div>

      <p v-if="error" class="error-banner">{{ error }}</p>

      <div class="notes-box">
        <h4 class="notes-title">Important Notes</h4>
        <ul class="notes-list">
          <li>Download the template file and follow the format.</li>
          <li>First row must contain headers.</li>
          <li>All required fields must be filled.</li>
          <li>Maximum 5000 questions can be imported at once.</li>
        </ul>
        <div class="template-btns">
          <button class="template-btn">
            <FileIcon class="icon-green" />
            Excel Template
          </button>
          <button class="template-btn">
            <FileIcon class="icon-orange" />
            CSV Template
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  error: { type: String, default: '' },
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['file-selected'])

const isDragging = ref(false)

const howTo = [
  { title: 'Download Template', desc: 'Download our template file and prepare your questions.' },
  { title: 'Upload File', desc: 'Upload your filled template file.' },
  { title: 'Map Columns', desc: 'Map your columns with system fields.' },
  { title: 'Preview & Validate', desc: 'Verify your questions and fix any errors.' },
  { title: 'Import', desc: 'Import your questions to the system.' }
]

// CHANGED: previously this only flipped a local `fileChosen` boolean and
// never sent the file anywhere — there was no emit/API call at all, which
// is why choosing or dropping a file did nothing. Now the actual File
// object is emitted up to the wizard, which does the real upload.
function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) emit('file-selected', file)
}
function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (file) emit('file-selected', file)
  e.target.value = '' // allow re-selecting the same file after an error
}

const ArrowLeftIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const UploadCloudIcon = { template: `<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>` }
const FileIcon = { template: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>` }
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
.progress-label { font-size: 13.5px; font-weight: 600; color: #A6A4B4; white-space: nowrap; }
.progress-label.active { color: #14121F; }
.progress-line { width: 56px; height: 2px; background: #E4E2ED; margin: 0 8px; flex-shrink: 0; }

.layout-grid { display: grid; grid-template-columns: 320px 1fr; gap: 24px; margin-top: 24px; }
.panel-title { font-size: 15px; font-weight: 700; color: #14121F; margin: 0 0 16px; }
.info-list { list-style: none; margin: 0; padding: 0; }
.info-row { display: flex; gap: 12px; padding-bottom: 22px; position: relative; }
.info-row:not(:last-child)::before { content: ''; position: absolute; left: 13px; top: 28px; bottom: 0; width: 2px; background: #ECEBF3; }
.info-num { width: 26px; height: 26px; border-radius: 50%; background: #F1EDFF; color: #6C4CF1; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; z-index: 1; }
.info-title { font-size: 13.5px; font-weight: 600; color: #14121F; margin: 0 0 2px; }
.info-desc { font-size: 12.5px; color: #8A879C; margin: 0; line-height: 1.4; }

.drop-panel { display: flex; }
.dropzone { flex: 1; border: 2px dashed #D8D5E8; border-radius: 14px; background: #FAFAFD; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 24px; }
.dropzone.dragging { border-color: #6C4CF1; background: #F5F2FF; }
.dropzone-icon { width: 56px; height: 56px; border-radius: 50%; background: #F1EDFF; color: #6C4CF1; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.dropzone-icon.spin svg { animation: spin 1.2s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.dropzone-title { font-size: 15px; font-weight: 600; color: #14121F; margin: 0 0 8px; }
.dropzone-or { font-size: 12.5px; color: #A6A4B4; margin: 0 0 14px; }
.choose-file-btn { padding: 10px 22px; border-radius: 9px; background: #6C4CF1; color: #fff; font-size: 13.5px; font-weight: 600; cursor: pointer; border: none; }
.choose-file-btn:hover { background: #5B3EE0; }
.dropzone-formats, .dropzone-max { font-size: 12px; color: #A6A4B4; margin: 4px 0 0; }

.error-banner { margin-top: 16px; padding: 12px 16px; border-radius: 10px; background: #FDE9E8; border: 1px solid #F6C6C3; color: #B3261E; font-size: 13px; font-weight: 600; }

.notes-box { margin-top: 24px; padding: 18px 20px; border-radius: 12px; background: #F9F8FC; border: 1px solid #ECEBF3; }
.notes-title { font-size: 13.5px; font-weight: 700; color: #14121F; margin: 0 0 10px; }
.notes-list { margin: 0 0 16px; padding-left: 18px; color: #524F6B; font-size: 13px; line-height: 1.9; }
.template-btns { display: flex; gap: 12px; }
.template-btn { display: flex; align-items: center; gap: 8px; padding: 9px 16px; border-radius: 9px; border: 1px solid #ECEBF3; background: #fff; font-size: 13px; font-weight: 600; color: #14121F; cursor: pointer; }
.template-btn:hover { background: #F6F5FB; }
.icon-green { color: #1FAE5C; }
.icon-orange { color: #E08A00; }

@media (max-width: 860px) { .layout-grid { grid-template-columns: 1fr; } }
</style>