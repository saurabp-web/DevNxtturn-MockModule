<template>
  <div class="panel-card">
    <div class="panel-head">
      <span class="panel-icon"><BookOpen :size="18" /></span>
      <div>
        <h2 class="panel-title">Subject Information</h2>
        <p class="panel-sub">Fill in the details below to create a new subject.</p>
      </div>
    </div>

    <div class="form-grid">
      <!-- Left: form fields -->
      <div class="form-fields">
        <div class="field">
          <label class="field-label">Select Exam <span class="required">*</span></label>
          <div class="select-wrap">
            <select v-model="local.examId" :disabled="!examOptions.length">
              <option :value="null" disabled>
                {{ examOptions.length ? 'Choose an exam' : 'No exams available' }}
              </option>
              <option v-for="e in examOptions" :key="e.id" :value="e.id">{{ e.name }}</option>
            </select>
            <ChevronDown :size="15" class="select-caret" />
          </div>
          <div class="info-banner">
            <Info :size="15" />
            <span>The subject will be created under the selected exam.</span>
          </div>
        </div>

        <div class="field">
          <label class="field-label">Subject Name <span class="required">*</span></label>
          <input v-model="local.subjectName" type="text" placeholder="Enter subject name" />
          <p class="field-hint">Enter the name of the subject (e.g., Physics, Mathematics)</p>
        </div>

        <div class="field">
          <label class="field-label">Subject Code (Optional)</label>
          <input v-model="local.subjectCode" type="text" placeholder="Enter subject code" />
          <p class="field-hint">A short code for internal reference (e.g., PHY, MATH)</p>
        </div>

        <div class="field toggle-field">
          <button
            type="button"
            class="toggle"
            :class="{ on: local.active }"
            @click="local.active = !local.active"
          >
            <span class="toggle-knob" />
          </button>
          <div>
            <p class="toggle-label">Active</p>
            <p class="field-hint">Active subjects will be visible in the system.</p>
          </div>
        </div>
      </div>

      <!-- Right: live preview -->
      <div class="preview-card">
        <div class="preview-head">
          <span class="preview-icon"><BookOpen :size="15" /></span>
          <div>
            <p class="preview-title">Subject Preview</p>
            <p class="preview-sub">This is how the subject will appear.</p>
          </div>
        </div>

        <div class="preview-body">
          <div class="preview-avatar"><BookOpen :size="26" /></div>
          <p class="preview-name">{{ local.subjectName || 'Subject Name' }}</p>
          <span class="preview-exam-chip">Under {{ selectedExamName || 'Exam Name' }}</span>
          <span class="preview-status-chip" :class="{ inactive: !local.active }">
            {{ local.active ? 'Active' : 'Inactive' }}
          </span>
        </div>

        <div class="preview-footer">
          <div class="preview-meta">
            <p class="meta-label">Code</p>
            <p class="meta-value">{{ local.subjectCode || 'SUB001' }}</p>
          </div>
          <div class="preview-meta">
            <p class="meta-label">Status</p>
            <p class="meta-value status-value">
              <span class="status-dot" :class="{ inactive: !local.active }" />
              {{ local.active ? 'Active' : 'Inactive' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="panel-actions">
      <button class="btn btn-ghost" @click="$emit('cancel')">
        <X :size="15" />
        Cancel
      </button>
      <div class="actions-right">
        <button class="btn btn-outline" @click="saveAndAddAnother">
          <FileText :size="15" />
          Save & Add Another
        </button>
        <button class="btn btn-primary" :disabled="!canContinue" @click="$emit('continue')">
          Save & Continue
          <ArrowRight :size="15" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, type PropType } from 'vue'
import { BookOpen, Info, ChevronDown, X, FileText, ArrowRight } from 'lucide-vue-next'
import type { SubjectForm, ExamOption } from './AddSubjectView.vue'

// CHANGED: same withDefaults/runtime-default bug as AddSubjectView.vue
// and SubjectsListView.vue — switched to plain runtime prop
// declarations so the `examOptions` default reliably applies.
const props = defineProps({
  modelValue: {
    type: Object as PropType<SubjectForm>,
    required: true,
  },
  examOptions: {
    type: Array as PropType<ExamOption[]>,
    default: () => [],
  },
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: SubjectForm): void
  (e: 'cancel'): void
  (e: 'continue'): void
  (e: 'save-and-add-another'): void
}>()

const local = reactive<SubjectForm>({ ...props.modelValue })

watch(local, () => emit('update:modelValue', { ...local }), { deep: true })

const selectedExamName = computed(
  () => (props.examOptions ?? []).find(e => e.id === local.examId)?.name ?? ''
)

const canContinue = computed(() => !!local.examId && local.subjectName.trim().length > 0)

function saveAndAddAnother() {
  emit('save-and-add-another')
}
</script>

<style scoped>
.panel-card {
  background: #fff;
  border: 1px solid #F0F0F2;
  border-radius: 14px;
  padding: 26px 28px;
}

.panel-head { display: flex; gap: 12px; margin-bottom: 24px; }
.panel-icon {
  width: 38px; height: 38px; border-radius: 10px;
  background: #F5F3FF; color: #7C3AED;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.panel-title { font-size: 16px; font-weight: 800; margin: 0; color: #111827; }
.panel-sub { font-size: 12.5px; color: #6B7280; margin: 3px 0 0; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 28px;
}

.form-fields { display: flex; flex-direction: column; gap: 20px; }
.field { display: flex; flex-direction: column; }
.field-label { font-size: 13px; font-weight: 700; color: #374151; margin-bottom: 8px; }
.required { color: #DC2626; }

.field input {
  padding: 10px 12px;
  border: 1px solid #E5E7EB;
  border-radius: 9px;
  font-size: 13.5px;
  color: #111827;
}
.field input:focus { outline: none; border-color: #A78BFA; box-shadow: 0 0 0 3px #EDE9FE; }
.field-hint { font-size: 11.5px; color: #9CA3AF; margin: 6px 0 0; }

.select-wrap { position: relative; }
.select-wrap select {
  width: 100%;
  appearance: none;
  padding: 10px 34px 10px 12px;
  border: 1px solid #E5E7EB;
  border-radius: 9px;
  font-size: 13.5px;
  color: #111827;
  background: #fff;
}
.select-wrap select:focus { outline: none; border-color: #A78BFA; box-shadow: 0 0 0 3px #EDE9FE; }
.select-caret { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); color: #9CA3AF; pointer-events: none; }

.info-banner {
  display: flex; align-items: center; gap: 8px;
  background: #F5F3FF; color: #6D28D9;
  border-radius: 8px; padding: 10px 12px;
  font-size: 12.5px; margin-top: 10px;
}

.toggle-field { flex-direction: row; align-items: flex-start; gap: 12px; }
.toggle {
  width: 40px; height: 22px; border-radius: 999px;
  background: #E5E7EB; border: none; cursor: pointer;
  position: relative; flex-shrink: 0; margin-top: 2px;
  transition: background 0.15s;
}
.toggle.on { background: #7C3AED; }
.toggle-knob {
  position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px; border-radius: 50%;
  background: #fff; transition: transform 0.15s;
}
.toggle.on .toggle-knob { transform: translateX(18px); }
.toggle-label { font-size: 13.5px; font-weight: 700; color: #111827; margin: 0 0 2px; }

/* Preview card */
.preview-card {
  background: #FAFAFF;
  border: 1px solid #EDE9FE;
  border-radius: 14px;
  overflow: hidden;
  align-self: start;
}
.preview-head {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 16px 18px 0;
}
.preview-icon {
  width: 26px; height: 26px; border-radius: 7px;
  background: #EDE9FE; color: #7C3AED;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.preview-title { font-size: 13px; font-weight: 700; margin: 0; color: #111827; }
.preview-sub { font-size: 11px; color: #9CA3AF; margin: 2px 0 0; }

.preview-body {
  display: flex; flex-direction: column; align-items: center;
  text-align: center; padding: 22px 18px 18px;
  gap: 8px;
}
.preview-avatar {
  width: 60px; height: 60px; border-radius: 50%;
  background: #EDE9FE; color: #7C3AED;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 4px;
}
.preview-name { font-size: 16px; font-weight: 800; margin: 0; color: #111827; }
.preview-exam-chip {
  background: #EDE9FE; color: #6D28D9;
  font-size: 11.5px; font-weight: 700;
  padding: 3px 12px; border-radius: 999px;
}
.preview-status-chip {
  background: #D1FAE5; color: #059669;
  font-size: 11px; font-weight: 700;
  padding: 3px 10px; border-radius: 999px;
}
.preview-status-chip.inactive { background: #F3F4F6; color: #6B7280; }

.preview-footer {
  display: grid; grid-template-columns: 1fr 1fr;
  border-top: 1px solid #EDE9FE;
  padding: 14px 18px;
}
.preview-meta:first-child { border-right: 1px solid #EDE9FE; }
.meta-label { font-size: 11px; color: #9CA3AF; margin: 0 0 3px; text-align: center; }
.meta-value { font-size: 13px; font-weight: 700; color: #111827; margin: 0; text-align: center; }
.status-value { display: flex; align-items: center; justify-content: center; gap: 6px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #059669; }
.status-dot.inactive { background: #9CA3AF; }

/* Actions */
.panel-actions {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 28px; padding-top: 20px; border-top: 1px solid #F0F0F2;
}
.actions-right { display: flex; gap: 10px; }
.btn {
  display: inline-flex; align-items: center; gap: 7px;
  border-radius: 9px; font-size: 13px; font-weight: 700;
  padding: 10px 18px; cursor: pointer; border: 1px solid transparent;
}
.btn-ghost { background: #fff; color: #374151; border-color: #E5E7EB; }
.btn-ghost:hover { background: #F9FAFB; }
.btn-outline { background: #fff; color: #374151; border-color: #E5E7EB; }
.btn-outline:hover { background: #F9FAFB; }
.btn-primary { background: #7C3AED; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #6D28D9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 900px) {
  .form-grid { grid-template-columns: 1fr; }
}
</style>