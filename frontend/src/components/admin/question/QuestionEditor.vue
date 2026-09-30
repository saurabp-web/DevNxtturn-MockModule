<template>
  <div class="step-content">
    <h2 class="step-title">2. Question Details</h2>
    <p class="step-subtitle">Enter the question text. You can format the text and add images if required.</p>

    <!-- Rich Text Editor -->
    <div class="form-group">
      <label class="form-label">Question <span class="required">*</span></label>
      <div class="editor-wrapper">
        <div class="editor-toolbar">
          <button class="toolbar-btn" title="Bold" @click="execCommand('bold')" type="button">
            <strong>B</strong>
          </button>
          <button class="toolbar-btn italic" title="Italic" @click="execCommand('italic')" type="button">
            <em>I</em>
          </button>
          <button class="toolbar-btn underline" title="Underline" @click="execCommand('underline')" type="button">
            <u>U</u>
          </button>
          <div class="toolbar-divider" />
          <button class="toolbar-btn" title="Bullet List" @click="execCommand('insertUnorderedList')" type="button">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="1" y="3" width="2" height="2" rx="1"/>
              <rect x="5" y="3" width="10" height="2" rx="1"/>
              <rect x="1" y="7" width="2" height="2" rx="1"/>
              <rect x="5" y="7" width="10" height="2" rx="1"/>
              <rect x="1" y="11" width="2" height="2" rx="1"/>
              <rect x="5" y="11" width="10" height="2" rx="1"/>
            </svg>
          </button>
          <button class="toolbar-btn" title="Align Left" type="button">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="1" y="3" width="14" height="2" rx="1"/>
              <rect x="1" y="7" width="10" height="2" rx="1"/>
              <rect x="1" y="11" width="14" height="2" rx="1"/>
            </svg>
          </button>
          <button class="toolbar-btn" title="Align Center" type="button">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="1" y="3" width="14" height="2" rx="1"/>
              <rect x="3" y="7" width="10" height="2" rx="1"/>
              <rect x="1" y="11" width="14" height="2" rx="1"/>
            </svg>
          </button>
          <div class="toolbar-divider" />
          <button class="toolbar-btn formula-btn" title="Subscript" @click="execCommand('subscript')" type="button">
            X<sub>2</sub>
          </button>
          <button class="toolbar-btn formula-btn" title="Superscript" @click="execCommand('superscript')" type="button">
            X<sup>2</sup>
          </button>
          <div class="toolbar-divider" />
          <button class="toolbar-btn" title="Insert Link" type="button">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M6 10.5l4-5" stroke-linecap="round"/>
              <path d="M5 8.5a2.5 2.5 0 0 1 0-3.5l1-1a2.5 2.5 0 0 1 3.5 3.5" stroke-linecap="round"/>
              <path d="M11 7.5a2.5 2.5 0 0 1 0 3.5l-1 1a2.5 2.5 0 0 1-3.5-3.5" stroke-linecap="round"/>
            </svg>
          </button>
          <button class="toolbar-btn" title="Insert Image" type="button">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="1" y="2" width="14" height="12" rx="2"/>
              <circle cx="5.5" cy="6" r="1.5"/>
              <path d="M1 11l4-4 3 3 2-2 5 5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>

        <div
          ref="editorRef"
          class="editor-body"
          contenteditable="true"
          :data-placeholder="'Enter your question here...'"
          @input="onEditorInput"
        />

        <div class="editor-footer">
          <span class="char-count">{{ charCount }}/5000</span>
        </div>
      </div>
    </div>

    <!-- Image Upload -->
    <div class="form-group mt-24">
      <label class="form-label">Add Image <span class="optional">(Optional)</span></label>
      <div
        class="drop-zone"
        :class="{ 'drop-zone--dragover': isDragging, 'drop-zone--has-file': previewUrl }"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <template v-if="!previewUrl">
          <div class="drop-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" fill="#ede9fe" />
              <path d="M20 12v12M14 18l6-6 6 6" stroke="#4f46e5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M13 28h14" stroke="#4f46e5" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <p class="drop-text">
            <span class="drop-link" @click.stop="triggerFileInput">Click to upload</span>
            or drag and drop
          </p>
          <p class="drop-hint">JPG, PNG, WEBP up to 5MB</p>
        </template>
        <template v-else>
          <img :src="previewUrl" class="image-preview" alt="Uploaded preview" />
          <button class="remove-image" @click.stop="removeImage" type="button">✕ Remove</button>
        </template>
      </div>
      <input
        ref="fileInputRef"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        class="hidden-input"
        @change="handleFileChange"
      />
    </div>

    <div class="step-footer">
      <button class="btn btn--secondary" @click="$emit('prev')" type="button">
        ← Previous Step
      </button>
      <button class="btn btn--primary" @click="handleNext" :disabled="!isValid || isChecking" type="button">
        {{ isChecking ? 'Checking...' : 'Next Step →' }}
      </button>
    </div>

    <!-- Duplicate Question Modal -->
    <Transition name="modal-fade">
      <div v-if="showDuplicateModal" class="modal-overlay" @click.self="cancelDuplicate">
        <div class="modal-card">
          <div class="modal-header">
            <div class="modal-header-left">
              <span class="modal-warning-icon">!</span>
              <h3 class="modal-title">Question Already Added</h3>
            </div>
            <button class="modal-close" @click="cancelDuplicate" type="button">✕</button>
          </div>

          <p class="modal-text">This question has already been added for one exam.</p>
          <p class="modal-text">Do you want to map this question for another exam/year?</p>

          <div class="modal-info-box">
            <p class="modal-info-title">Already Added In</p>
            <ul class="modal-info-list">
              <li v-if="duplicateMatch.exam_name"><strong>Current Exam:</strong> {{ duplicateMatch.exam_name }}</li>
              <li v-if="duplicateMatch.pyq_exam_name"><strong>PYQ Source Exam:</strong> {{ duplicateMatch.pyq_exam_name }}</li>
              <li v-if="duplicateMatch.year"><strong>Year:</strong> {{ duplicateMatch.year }}</li>
              <li v-if="duplicateMatch.session"><strong>Session/Shift:</strong> {{ duplicateMatch.session }}</li>
            </ul>
          </div>

          <div class="modal-actions">
            <button class="btn btn--secondary" @click="cancelDuplicate" type="button">No, Cancel</button>
            <button class="btn btn--primary" @click="confirmMapAnotherExam" type="button">
              Yes, Map for Another Exam
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { checkDuplicateQuestion } from '@/services/questionAdminApi'

const emit = defineEmits(['next', 'prev', 'update:modelValue'])

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  // Passed from AddQuestion.vue as formData.step1.chapter — scopes the
  // duplicate-question check to the chapter already chosen in Step 1,
  // so the same question text under a different chapter isn't flagged.
  chapterId: {
    type: [Number, String],
    default: null
  }
})

const editorRef = ref(null)
const fileInputRef = ref(null)
const isDragging = ref(false)
const previewUrl = ref(props.modelValue?.imagePreview || null)
const charCount = ref(0)

// The actual File object for the selected image (not just its data-URL
// preview) — this is what AddQuestion.vue needs to send to the backend
// as multipart/form-data. It's kept outside the emitted plain object
// since File instances shouldn't be spread/cloned through reactive state.
let imageFile = props.modelValue?.imageFile || null

const isValid = computed(() => charCount.value > 0)

// ── Duplicate question detection ───────────────────────────────
const isChecking = ref(false)
const showDuplicateModal = ref(false)
const duplicateMatch = ref({ exam_name: null, pyq_exam_name: null, year: null, session: null })
const duplicateQuestionId = ref(null)
// Set once a duplicate is confirmed and the admin chooses to proceed
// anyway ("Yes, Map for Another Exam") — carried into the emitted
// modelValue so AddQuestion.vue/backend can log which question this was
// mapped from, and so we don't re-prompt for the same text+chapter pair
// again on this step.
const mappedFromQuestionId = ref(null)
let lastCheckedText = null

function execCommand(cmd) {
  document.execCommand(cmd, false, null)
  editorRef.value?.focus()
}

function onEditorInput() {
  charCount.value = editorRef.value?.innerText?.length || 0
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) loadPreview(file)
}

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) loadPreview(file)
}

function loadPreview(file) {
  imageFile = file
  const reader = new FileReader()
  reader.onload = (ev) => {
    previewUrl.value = ev.target.result
  }
  reader.readAsDataURL(file)
}

function removeImage() {
  previewUrl.value = null
  imageFile = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function emitUpdate() {
  emit('update:modelValue', {
    html: editorRef.value?.innerHTML || '',
    text: editorRef.value?.innerText || '',
    imagePreview: previewUrl.value,
    imageFile,
    mappedFromQuestionId: mappedFromQuestionId.value,
  })
}

async function handleNext() {
  const text = editorRef.value?.innerText?.trim() || ''

  // Re-run the check only if the text actually changed since the last
  // check (or on the very first attempt) — avoids a redundant network
  // call if the admin clicks "Next Step" again right after cancelling.
  if (text && text !== lastCheckedText) {
    isChecking.value = true
    try {
      const result = await checkDuplicateQuestion(text, props.chapterId)
      lastCheckedText = text
      if (result.duplicate) {
        duplicateMatch.value = result.existing || { exam_name: null, pyq_exam_name: null, year: null, session: null }
        duplicateQuestionId.value = result.question_id ?? null
        showDuplicateModal.value = true
        return
      }
    } catch (err) {
      // Fail open: if the duplicate-check call itself fails (network
      // issue, endpoint down), don't block the admin from proceeding —
      // the backend's create-question validation is the real source of
      // truth and will still run on final submit.
      console.error('Duplicate question check failed:', err)
    } finally {
      isChecking.value = false
    }
  }

  emitUpdate()
  emit('next')
}

function cancelDuplicate() {
  showDuplicateModal.value = false
  // Force a re-check next time, in case the admin edits the text.
  lastCheckedText = null
}

function confirmMapAnotherExam() {
  mappedFromQuestionId.value = duplicateQuestionId.value
  showDuplicateModal.value = false
  emitUpdate()
  emit('next')
}

// Re-hydrate the editor's contenteditable body when coming back to this
// step (e.g. after clicking "Previous Step" from step 3), since
// contenteditable content isn't part of Vue's reactive template state.
onMounted(async () => {
  await nextTick()
  if (editorRef.value && props.modelValue?.html) {
    editorRef.value.innerHTML = props.modelValue.html
    onEditorInput()
  }
})
</script>

<style scoped>
.step-content {
  padding: 0;
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mt-24 {
  margin-top: 24px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.required { color: #ef4444; }
.optional { color: #9ca3af; font-weight: 400; }

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
  padding: 8px 10px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-wrap: wrap;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  transition: background 0.12s;
}

.toolbar-btn:hover {
  background: #e5e7eb;
}

.formula-btn {
  font-size: 12px;
  width: auto;
  padding: 0 6px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: #e5e7eb;
  margin: 0 4px;
}

.editor-body {
  min-height: 120px;
  padding: 12px 14px;
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
  padding: 6px 12px;
  border-top: 1px solid #e5e7eb;
}

.char-count {
  font-size: 12px;
  color: #9ca3af;
}

/* Drop Zone */
.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  background: #fafafa;
  position: relative;
}

.drop-zone:hover,
.drop-zone--dragover {
  border-color: #4f46e5;
  background: #f5f3ff;
}

.drop-zone--has-file {
  padding: 16px;
  border-style: solid;
  border-color: #4f46e5;
}

.drop-icon {
  margin-bottom: 12px;
}

.drop-text {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 4px;
}

.drop-link {
  color: #4f46e5;
  text-decoration: underline;
  cursor: pointer;
}

.drop-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.image-preview {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: 6px;
}

.remove-image {
  display: block;
  margin: 10px auto 0;
  padding: 4px 12px;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.hidden-input {
  display: none;
}

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

.btn--primary {
  background: #4f46e5;
  color: #fff;
}
.btn--primary:hover:not(:disabled) { background: #4338ca; }
.btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn--secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}
.btn--secondary:hover { background: #e5e7eb; }

/* Duplicate Question Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 16px;
}

.modal-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px 28px 28px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #fef3c7;
  color: #d97706;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}

.modal-title {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.modal-close {
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 16px;
  cursor: pointer;
  line-height: 1;
  padding: 4px;
}
.modal-close:hover { color: #374151; }

.modal-text {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 4px;
  line-height: 1.5;
}

.modal-info-box {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px 16px;
  margin: 16px 0 20px;
}

.modal-info-title {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px;
}

.modal-info-list {
  list-style: disc;
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.modal-info-list li {
  font-size: 13px;
  color: #374151;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.15s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>