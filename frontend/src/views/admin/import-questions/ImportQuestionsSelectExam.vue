<template>
  <div class="import-page">
    <!-- Page title -->
    <div class="page-header">
      <h1 class="page-title">Select Exam to Import Questions</h1>
      <p class="page-subtitle">Choose the exam for which you want to import questions.</p>
    </div>

    <!-- Stepper -->
    <ImportWizardHeader
      :steps="['Select Exam', 'Upload File', 'Validate & Preview', 'Import Valid Questions']"
      :current-step="0"
      :allow-change-exam="false"
    />

    <!-- Card -->
    <div class="card">
      <div class="layout-grid">
        <!-- Left: Exam selector -->
        <div class="select-panel">
          <label class="field-label">Select Exam <span class="req">*</span></label>

          <div class="combo" ref="comboRef">
            <button type="button" class="combo-trigger" @click="open = !open">
              <span :class="{ placeholder: !selectedExam }">
                {{ selectedExam ? selectedExam.exam_name : 'Select an exam' }}
              </span>
              <ChevronIcon :class="{ flipped: open }" />
            </button>

            <div v-if="open" class="combo-panel">
              <div class="combo-search">
                <SearchIcon />
                <input
                  v-model="query"
                  type="text"
                  placeholder="Search exam..."
                  @click.stop
                />
              </div>

              <p v-if="loading" class="combo-hint">Loading exams…</p>
              <p v-else-if="loadError" class="combo-hint error">{{ loadError }}</p>
              <p v-else-if="filteredExams.length === 0" class="combo-hint">No exams match "{{ query }}".</p>

              <ul v-else class="combo-list">
                <li
                  v-for="exam in filteredExams"
                  :key="exam.exam_id"
                  class="combo-option"
                  @click="selectExam(exam)"
                >
                  {{ exam.exam_name }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Right: Import Process panel -->
        <div class="process-panel">
          <div class="process-icon-wrap"><ClipboardIcon /></div>
          <h3 class="process-title">Import Process</h3>
          <ol class="process-list">
            <li v-for="(s, i) in processSteps" :key="i" class="process-row">
              <span class="process-num">{{ i + 1 }}</span>
              <span>{{ s }}</span>
            </li>
          </ol>
        </div>
      </div>

      <div class="footer-actions">
        <button class="next-btn" :disabled="!selectedExam" @click="$emit('exam-selected', selectedExam)">
          Next
          <ArrowRightIcon />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import ImportWizardHeader from './ImportWizardHeader.vue'

defineEmits(['exam-selected'])

const exams = ref([])
const selectedExam = ref(null)
const loading = ref(true)
const loadError = ref('')
const open = ref(false)
const query = ref('')
const comboRef = ref(null)

const processSteps = [
  'Select the exam',
  'Upload your question file (Excel or CSV)',
  'Validate & preview the questions',
  'Import valid questions to the exam',
]

const filteredExams = computed(() => {
  if (!query.value.trim()) return exams.value
  const q = query.value.trim().toLowerCase()
  return exams.value.filter((e) => e.exam_name.toLowerCase().includes(q))
})

function selectExam(exam) {
  selectedExam.value = exam
  open.value = false
  query.value = ''
}

function onClickOutside(e) {
  if (comboRef.value && !comboRef.value.contains(e.target)) open.value = false
}

onMounted(async () => {
  document.addEventListener('click', onClickOutside)
  try {
    const res = await fetch('/api/exams/')
    const data = await res.json().catch(() => ({}))
    if (!res.ok) { loadError.value = data.error || 'Could not load the exam list.'; return }
    exams.value = Array.isArray(data) ? data : (data.results || [])
  } catch {
    loadError.value = 'Could not reach the server while loading exams.'
  } finally {
    loading.value = false
  }
})
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))

const ChevronIcon    = { template: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>` }
const SearchIcon     = { template: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>` }
const ClipboardIcon  = { template: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M9 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-3"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="14" y2="15"/></svg>` }
const ArrowRightIcon = { template: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>` }
</script>

<style scoped>
* { box-sizing: border-box; }
.import-page {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  max-width: 1100px; margin: 0 auto; padding: 28px 24px;
}

/* Page header */
.page-header { margin-bottom: 24px; }
.page-title { font-size: 20px; font-weight: 700; color: #14121F; margin: 0 0 4px; }
.page-subtitle { font-size: 13px; color: #8A879C; margin: 0; }

/* Card */
.card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #ECEBF3;
  padding: 28px;
}

/* Two-column layout */
.layout-grid {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 28px;
  align-items: start;
}

/* Exam selector */
.field-label { display: block; font-size: 13.5px; font-weight: 600; color: #14121F; margin-bottom: 8px; }
.req { color: #D64545; }

.combo { position: relative; }
.combo-trigger {
  width: 100%;
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 14px;
  border-radius: 9px; border: 1px solid #D8D5E8;
  background: #fff; font-size: 14px; color: #14121F; cursor: pointer;
  text-align: left;
}
.combo-trigger .placeholder { color: #A6A4B4; }
.combo-trigger svg { color: #A6A4B4; transition: transform 0.15s; flex-shrink: 0; }
.combo-trigger svg.flipped { transform: rotate(180deg); }

.combo-panel {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: #fff; border: 1px solid #ECEBF3; border-radius: 10px;
  box-shadow: 0 8px 24px rgba(20,18,31,.10); z-index: 20; padding: 8px;
}
.combo-search {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border: 1px solid #ECEBF3; border-radius: 8px;
  margin-bottom: 6px; color: #A6A4B4;
}
.combo-search input { border: none; outline: none; font-size: 13.5px; flex: 1; color: #14121F; background: transparent; }
.combo-hint { font-size: 12.5px; color: #A6A4B4; padding: 8px 10px; margin: 0; }
.combo-hint.error { color: #B3261E; }
.combo-list { list-style: none; margin: 0; padding: 0; max-height: 220px; overflow-y: auto; }
.combo-option { padding: 10px; border-radius: 8px; font-size: 13.5px; color: #14121F; cursor: pointer; }
.combo-option:hover { background: #F5F2FF; color: #6C4CF1; }

/* Process panel */
.process-panel {
  border: 1px solid #ECEBF3; border-radius: 14px;
  padding: 22px; background: #FAFAFD;
}
.process-icon-wrap {
  width: 48px; height: 48px; border-radius: 50%;
  background: #F1EDFF; color: #6C4CF1;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
}
.process-title { font-size: 15px; font-weight: 700; color: #14121F; margin: 0 0 16px; }
.process-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.process-row {
  display: flex; align-items: flex-start; gap: 10px;
  font-size: 13px; color: #524F6B; line-height: 1.5;
}
.process-num {
  width: 20px; height: 20px; border-radius: 50%;
  background: #fff; border: 1.5px solid #D8D5E8;
  color: #6C4CF1; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

/* Footer */
.footer-actions { display: flex; justify-content: flex-end; margin-top: 28px; }
.next-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 11px 24px; border-radius: 9px;
  background: #6C4CF1; color: #fff;
  font-size: 13.5px; font-weight: 600; cursor: pointer; border: none;
}
.next-btn:hover:not(:disabled) { background: #5B3EE0; }
.next-btn:disabled { background: #D8D5E8; cursor: not-allowed; }

@media (max-width: 860px) {
  .layout-grid { grid-template-columns: 1fr; }
}
</style>