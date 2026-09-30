<template>
  <div class="panel-card">
    <div class="panel-head">
      <span class="panel-icon"><ShieldCheck :size="18" /></span>
      <div>
        <h2 class="panel-title">Review & Confirm</h2>
        <p class="panel-sub">Please review the details below. Click "Save Subject" to create it.</p>
      </div>
    </div>

    <div class="review-list">
      <div class="review-row">
        <span class="review-icon"><GraduationCap :size="16" /></span>
        <div class="review-content">
          <p class="review-label">Exam</p>
          <div class="review-value-row">
            <span class="review-value">{{ selectedExam?.name ?? '—' }}</span>
            <span v-if="selectedExam?.code" class="exam-code-chip">{{ selectedExam.code }}</span>
          </div>
        </div>
      </div>

      <div class="review-row">
        <span class="review-icon"><BookOpen :size="16" /></span>
        <div class="review-content">
          <p class="review-label">Subject Name</p>
          <p class="review-value">{{ form.subjectName || '—' }}</p>
        </div>
      </div>

      <div class="review-row">
        <span class="review-icon"><Hash :size="16" /></span>
        <div class="review-content">
          <p class="review-label">Subject Code</p>
          <p class="review-value">{{ form.subjectCode || '—' }}</p>
        </div>
      </div>

      <div class="review-row last">
        <span class="review-icon"><CheckCircle2 :size="16" /></span>
        <div class="review-content">
          <p class="review-label">Status</p>
          <span class="status-chip" :class="{ inactive: !form.active }">
            <span class="status-dot" />
            {{ form.active ? 'Active' : 'Inactive' }}
          </span>
          <p class="status-note">
            {{ form.active
              ? 'This subject will be visible and available for use in the system.'
              : 'This subject will be hidden until it is activated.' }}
          </p>
        </div>
      </div>
    </div>

    <div class="info-banner">
      <Info :size="16" />
      <div>
        <p class="info-title">What happens next?</p>
        <p class="info-text">
          Once you save, this subject will be added to the selected exam and you will be able to manage chapters, topics and questions under this subject.
        </p>
      </div>
    </div>

    <div class="panel-actions">
      <button class="btn btn-ghost" :disabled="saving" @click="$emit('back')">
        <ArrowLeft :size="15" />
        Back to Edit
      </button>
      <div class="actions-right">
        <button class="btn btn-outline" :disabled="saving" @click="$emit('save-draft')">
          <Save :size="15" />
          Save as Draft
        </button>
        <button class="btn btn-primary" :disabled="saving" @click="$emit('save')">
          <Loader2 v-if="saving" :size="15" class="spin" />
          <Save v-else :size="15" />
          {{ saving ? 'Saving…' : 'Save Subject' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'
import {
  ShieldCheck, GraduationCap, BookOpen, Hash, CheckCircle2,
  Info, ArrowLeft, Save, Loader2,
} from 'lucide-vue-next'
import type { SubjectForm, ExamOption } from './AddSubjectView.vue'

// CHANGED: same withDefaults/runtime-default bug as the other two
// files — switched to plain runtime prop declarations.
const props = defineProps({
  form: {
    type: Object as PropType<SubjectForm>,
    required: true,
  },
  examOptions: {
    type: Array as PropType<ExamOption[]>,
    default: () => [],
  },
  saving: {
    type: Boolean,
    default: false,
  },
})

defineEmits<{
  (e: 'back'): void
  (e: 'save-draft'): void
  (e: 'save'): void
}>()

const selectedExam = computed(
  () => (props.examOptions ?? []).find(e => e.id === props.form.examId) ?? null
)
</script>

<style scoped>
.panel-card {
  background: #fff;
  border: 1px solid #F0F0F2;
  border-radius: 14px;
  padding: 26px 28px;
}

.panel-head { display: flex; gap: 12px; margin-bottom: 22px; }
.panel-icon {
  width: 38px; height: 38px; border-radius: 10px;
  background: #F5F3FF; color: #7C3AED;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.panel-title { font-size: 16px; font-weight: 800; margin: 0; color: #111827; }
.panel-sub { font-size: 12.5px; color: #6B7280; margin: 3px 0 0; }

.review-list {
  border: 1px solid #F0F0F2;
  border-radius: 12px;
  overflow: hidden;
}
.review-row {
  display: flex; gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px dashed #E5E7EB;
}
.review-row.last { border-bottom: none; }
.review-icon {
  width: 32px; height: 32px; border-radius: 9px;
  background: #F5F3FF; color: #7C3AED;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.review-content { flex: 1; }
.review-label { font-size: 13px; font-weight: 700; color: #111827; margin: 0 0 5px; }
.review-value-row { display: flex; align-items: center; gap: 10px; }
.review-value { font-size: 13.5px; color: #374151; margin: 0; }
.exam-code-chip {
  background: #EDE9FE; color: #6D28D9;
  font-size: 11px; font-weight: 700;
  padding: 2px 10px; border-radius: 999px;
}

.status-chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: #ECFDF5; color: #059669;
  font-size: 12px; font-weight: 700;
  padding: 4px 12px; border-radius: 999px;
  margin-bottom: 6px;
}
.status-chip.inactive { background: #F3F4F6; color: #6B7280; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.status-note { font-size: 12px; color: #9CA3AF; margin: 4px 0 0; }

.info-banner {
  display: flex; gap: 12px;
  background: #F5F3FF; color: #4C1D95;
  border-radius: 12px; padding: 16px 18px;
  margin-top: 20px;
}
.info-banner svg { flex-shrink: 0; margin-top: 1px; color: #7C3AED; }
.info-title { font-size: 13px; font-weight: 700; margin: 0 0 3px; color: #4C1D95; }
.info-text { font-size: 12.5px; color: #6D28D9; margin: 0; line-height: 1.6; }

.panel-actions {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 24px; padding-top: 20px; border-top: 1px solid #F0F0F2;
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
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.7s linear infinite; }
</style>