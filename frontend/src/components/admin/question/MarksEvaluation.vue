<template>
  <div class="step-content">
    <div class="main-columns">
      <!-- Left: Marks Form -->
      <div class="marks-column">
        <h2 class="step-title">4. Marks &amp; Evaluation</h2>
        <p class="step-subtitle">Set marks for correct answer and negative marking (if applicable).</p>

        <div class="marks-row">
          <div class="form-group">
            <label class="form-label">Marks for Correct Answer <span class="required">*</span></label>
            <input
              v-model.number="form.correctMarks"
              type="number"
              class="marks-input"
              min="0"
              step="0.5"
              placeholder="e.g. 4"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Negative Marks <span class="required">*</span></label>
            <input
              v-model.number="form.negativeMarks"
              type="number"
              class="marks-input"
              min="0"
              step="0.25"
              placeholder="e.g. 1"
              :disabled="!form.enableNegative"
            />
          </div>
        </div>

        <div class="toggle-row">
          <label class="toggle-label">
            <input
              type="checkbox"
              v-model="form.enableNegative"
              class="toggle-checkbox"
            />
            <span class="toggle-track">
              <span class="toggle-thumb" />
            </span>
            <span class="toggle-text">Enable Negative Marking</span>
          </label>
          <p class="toggle-hint">Deduct marks for incorrect attempts.</p>
        </div>

        <!-- Explanation -->
        <div class="form-group mt-24">
          <label class="form-label">
            Explanation / Solution
            <span class="optional">(Optional)</span>
          </label>
          <div class="editor-wrapper">
            <div class="editor-toolbar">
              <button class="toolbar-btn" title="Bold" @click="execCommand('bold')" type="button"><strong>B</strong></button>
              <button class="toolbar-btn" title="Italic" @click="execCommand('italic')" type="button"><em>I</em></button>
              <button class="toolbar-btn" title="Underline" @click="execCommand('underline')" type="button"><u>U</u></button>
              <div class="toolbar-divider" />
              <button class="toolbar-btn" title="Bullet List" @click="execCommand('insertUnorderedList')" type="button">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
                  <rect x="1" y="2" width="2" height="2" rx="1"/><rect x="5" y="2" width="9" height="2" rx="1"/>
                  <rect x="1" y="6" width="2" height="2" rx="1"/><rect x="5" y="6" width="9" height="2" rx="1"/>
                  <rect x="1" y="10" width="2" height="2" rx="1"/><rect x="5" y="10" width="9" height="2" rx="1"/>
                </svg>
              </button>
              <button class="toolbar-btn" title="Align left" type="button">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
                  <rect x="1" y="2" width="13" height="2" rx="1"/><rect x="1" y="6" width="9" height="2" rx="1"/>
                  <rect x="1" y="10" width="13" height="2" rx="1"/>
                </svg>
              </button>
              <button class="toolbar-btn" title="Align center" type="button">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">
                  <rect x="1" y="2" width="13" height="2" rx="1"/><rect x="3" y="6" width="9" height="2" rx="1"/>
                  <rect x="1" y="10" width="13" height="2" rx="1"/>
                </svg>
              </button>
              <div class="toolbar-divider" />
              <button class="toolbar-btn formula-btn" title="Subscript" @click="execCommand('subscript')" type="button">X<sub>2</sub></button>
              <button class="toolbar-btn formula-btn" title="Superscript" @click="execCommand('superscript')" type="button">X<sup>2</sup></button>
              <div class="toolbar-divider" />
              <button class="toolbar-btn" title="Insert Link" type="button">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M5.5 9.5l4-5" stroke-linecap="round"/>
                  <path d="M4.5 7.5a2 2 0 0 1 0-3l1-1a2 2 0 0 1 3 3" stroke-linecap="round"/>
                  <path d="M10.5 7.5a2 2 0 0 1 0 3l-1 1a2 2 0 0 1-3-3" stroke-linecap="round"/>
                </svg>
              </button>
              <button class="toolbar-btn" title="Insert Image" type="button">
                <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="1" y="2" width="13" height="11" rx="2"/>
                  <circle cx="5" cy="5.5" r="1.2"/>
                  <path d="M1 10.5l3.5-3.5 2.5 2.5 2-2 4.5 4.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>

            <div
              ref="explanationRef"
              class="editor-body"
              contenteditable="true"
              data-placeholder="Enter explanation or solution here..."
              @input="onExplanationInput"
            />

            <div class="editor-footer">
              <span class="char-count">{{ explanationCount }}/5000</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Quick Summary -->
      <div class="summary-column">
        <div class="summary-card">
          <h3 class="summary-title">Quick Summary</h3>
          <div class="summary-rows">
            <div class="summary-row" v-for="item in summaryItems" :key="item.label">
              <span class="summary-label">{{ item.label }}</span>
              <span class="summary-value" :class="item.valueClass">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="step-footer">
      <button class="btn btn--secondary" @click="$emit('prev')" type="button">
        ← Previous Step
      </button>
      <button
        class="btn btn--primary"
        @click="handleNext"
        :disabled="!isValid || submitting"
        type="button"
      >
        {{ submitting ? 'Saving...' : 'Save Question →' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'

const emit = defineEmits(['next', 'prev', 'update:modelValue'])

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  questionSummary: {
    type: Object,
    default: () => ({})
  },
  submitting: {
    type: Boolean,
    default: false
  }
})

const explanationRef = ref(null)
const explanationCount = ref(0)

const form = reactive({
  correctMarks: props.modelValue?.correctMarks ?? 4,
  negativeMarks: props.modelValue?.negativeMarks ?? 1,
  enableNegative: props.modelValue?.enableNegative ?? true,
  explanation: props.modelValue?.explanation ?? '',
  explanationHtml: props.modelValue?.explanationHtml ?? ''
})

const summaryItems = computed(() => [
  { label: 'Exam', value: props.questionSummary?.exam || 'JEE Main' },
  { label: 'Subject', value: props.questionSummary?.subject || 'Physics' },
  { label: 'Chapter', value: props.questionSummary?.chapter || 'Current Electricity' },
  { label: 'Topic', value: props.questionSummary?.topic || "Ohm's Law" },
  { label: 'Type', value: props.questionSummary?.type || 'Single Correct' },
  { label: 'Difficulty', value: props.questionSummary?.difficulty || 'Easy', valueClass: 'badge badge--easy' },
  { label: 'Total Options', value: props.questionSummary?.totalOptions ?? 4 },
  { label: 'Marks (Correct)', value: form.correctMarks },
  { label: 'Negative Marks', value: form.enableNegative ? form.negativeMarks : '—' }
])

const isValid = computed(() => form.correctMarks > 0)

function execCommand(cmd) {
  document.execCommand(cmd, false, null)
  explanationRef.value?.focus()
}

function onExplanationInput() {
  explanationCount.value = explanationRef.value?.innerText?.length || 0
}

function handleNext() {
  form.explanation = explanationRef.value?.innerText || ''
  form.explanationHtml = explanationRef.value?.innerHTML || ''
  emit('update:modelValue', { ...form })
  emit('next')
}

// Re-hydrate the explanation editor when coming back to this step.
onMounted(async () => {
  await nextTick()
  if (explanationRef.value && props.modelValue?.explanationHtml) {
    explanationRef.value.innerHTML = props.modelValue.explanationHtml
    onExplanationInput()
  }
})
</script>

<style scoped>
.step-content {
  padding: 0;
}

.main-columns {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 32px;
  align-items: start;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  color: #4f46e5;
  margin: 0 0 4px;
}

.step-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 24px;
}

.marks-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mt-24 { margin-top: 24px; }

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.required { color: #ef4444; }
.optional { color: #9ca3af; font-weight: 400; }

.marks-input {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}

.marks-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
}

.marks-input:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

/* Toggle */
.toggle-row {
  margin-bottom: 8px;
}

.toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.toggle-checkbox {
  display: none;
}

.toggle-track {
  position: relative;
  width: 38px;
  height: 20px;
  background: #d1d5db;
  border-radius: 100px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-checkbox:checked + .toggle-track {
  background: #4f46e5;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  transition: left 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle-checkbox:checked + .toggle-track .toggle-thumb {
  left: 20px;
}

.toggle-text {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.toggle-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 4px 0 0 48px;
}

/* Editor */
.editor-wrapper {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  transition: border-color 0.15s;
}
.editor-wrapper:focus-within {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 10px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-wrap: wrap;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 26px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  transition: background 0.12s;
}
.toolbar-btn:hover { background: #e5e7eb; }
.formula-btn { width: auto; padding: 0 5px; font-size: 11px; }

.toolbar-divider {
  width: 1px;
  height: 18px;
  background: #e5e7eb;
  margin: 0 3px;
}

.editor-body {
  min-height: 100px;
  padding: 10px 14px;
  font-size: 14px;
  color: #111827;
  outline: none;
  line-height: 1.6;
}
.editor-body:empty::before {
  content: attr(data-placeholder);
  color: #9ca3af;
  pointer-events: none;
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  padding: 4px 12px;
  border-top: 1px solid #e5e7eb;
}
.char-count { font-size: 12px; color: #9ca3af; }

/* Summary Card */
.summary-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  position: sticky;
  top: 20px;
}

.summary-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 14px;
}

.summary-rows {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.summary-label { color: #6b7280; }
.summary-value { color: #111827; font-weight: 500; text-align: right; max-width: 140px; }

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
.badge--easy { background: #dcfce7; color: #16a34a; }
.badge--medium { background: #fef3c7; color: #d97706; }
.badge--hard { background: #fee2e2; color: #dc2626; }

/* Footer */
.step-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.btn--primary { background: #4f46e5; color: #fff; }
.btn--primary:hover:not(:disabled) { background: #4338ca; }
.btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn--secondary { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
.btn--secondary:hover { background: #e5e7eb; }
</style>