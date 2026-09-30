<template>
  <div class="import-page">
    <!-- Stepper + Exam Banner -->
    <ImportWizardHeader
      :steps="['Select Exam', 'Upload File', 'Validate & Preview', 'Import Valid Questions']"
      :current-step="1"
      :exam-name="examName"
      @change-exam="$emit('change-exam')"
    />

    <!-- Card -->
    <div class="card">
      <div class="layout-grid">
        <!-- Left: Dropzone -->
        <div class="drop-panel">
          <div
            class="dropzone"
            :class="{ dragging: isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <template v-if="submitting">
              <div class="dz-icon spin"><UploadCloudIcon /></div>
              <p class="dz-title">Validating your file…</p>
              <p class="dz-sub">This won't take long.</p>
            </template>
            <template v-else>
              <div class="dz-icon"><UploadCloudIcon /></div>
              <p class="dz-title">Drag &amp; drop your file here</p>
              <p class="dz-or">or</p>
              <label class="choose-btn">
                Choose File
                <input type="file" accept=".xlsx,.xls,.csv" hidden @change="onFileSelected" />
              </label>
              <p class="dz-note">Supports: .xlsx, .xls, .csv</p>
              <p class="dz-note">Maximum file size: 10MB</p>
            </template>
          </div>

          <p v-if="error" class="error-banner">{{ error }}</p>
        </div>

        <!-- Right: Guidelines -->
        <div class="info-panel">
          <h3 class="panel-title">Guidelines</h3>
          <ul class="guideline-list">
            <li>First row must contain column headers.</li>
            <li>Each row will be treated as a separate question.</li>
            <li>Empty rows will be skipped.</li>
            <li>Duplicate questions will be ignored.</li>
            <li>Only valid questions will be imported.</li>
          </ul>
          <button class="download-btn" @click="$emit('download-template')">
            <DownloadIcon />
            Download Template
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="footer-actions">
        <button class="back-btn" @click="$emit('back')">
          <ArrowLeftIcon /> Back
        </button>
        <!-- "Next" is auto-triggered on file pick; no manual next needed -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ImportWizardHeader from './ImportWizardHeader.vue'

defineProps({
  error:      { type: String,  default: '' },
  submitting: { type: Boolean, default: false },
  examName:   { type: String,  default: '' },
})
const emit = defineEmits(['file-selected', 'back', 'change-exam', 'download-template'])

const isDragging = ref(false)

function onDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) emit('file-selected', file)
}
function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (file) emit('file-selected', file)
  e.target.value = ''
}

const ArrowLeftIcon  = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>` }
const UploadCloudIcon = { template: `<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>` }
const DownloadIcon   = { template: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>` }
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

.layout-grid {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
}

/* Dropzone */
.drop-panel { display: flex; flex-direction: column; }
.dropzone {
  flex: 1;
  border: 2px dashed #D8D5E8;
  border-radius: 14px;
  background: #FAFAFD;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 52px 24px;
  transition: border-color 0.15s, background 0.15s;
}
.dropzone.dragging { border-color: #6C4CF1; background: #F5F2FF; }

.dz-icon {
  width: 60px; height: 60px; border-radius: 50%;
  background: #F1EDFF; color: #6C4CF1;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.dz-icon.spin svg { animation: spin 1.2s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.dz-title { font-size: 15px; font-weight: 600; color: #14121F; margin: 0 0 8px; }
.dz-or { font-size: 12.5px; color: #A6A4B4; margin: 0 0 14px; }
.dz-note { font-size: 12px; color: #A6A4B4; margin: 4px 0 0; }

.choose-btn {
  padding: 10px 24px;
  border-radius: 9px;
  background: #6C4CF1; color: #fff;
  font-size: 13.5px; font-weight: 600;
  cursor: pointer; border: none;
  margin-bottom: 12px;
}
.choose-btn:hover { background: #5B3EE0; }

/* Guidelines */
.info-panel {
  border: 1px solid #ECEBF3;
  border-radius: 14px;
  padding: 22px;
  background: #FAFAFD;
  display: flex; flex-direction: column;
}
.panel-title { font-size: 15px; font-weight: 700; color: #14121F; margin: 0 0 14px; }
.guideline-list {
  margin: 0 0 20px; padding-left: 18px;
  color: #524F6B; font-size: 13px; line-height: 2;
  flex: 1;
}
.download-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  width: 100%; padding: 10px 16px;
  border-radius: 9px;
  background: #fff; border: 1px solid #ECEBF3;
  color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer;
}
.download-btn:hover { background: #F6F5FB; }

/* Error */
.error-banner {
  margin-top: 12px; padding: 12px 16px;
  border-radius: 10px; background: #FDE9E8;
  border: 1px solid #F6C6C3; color: #B3261E;
  font-size: 13px; font-weight: 600;
}

/* Footer */
.footer-actions { display: flex; justify-content: space-between; margin-top: 24px; }
.back-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 9px;
  border: 1px solid #ECEBF3; background: #fff;
  color: #524F6B; font-size: 13px; font-weight: 600; cursor: pointer;
}
.back-btn:hover { background: #F6F5FB; }

@media (max-width: 860px) {
  .layout-grid { grid-template-columns: 1fr; }
}
</style>