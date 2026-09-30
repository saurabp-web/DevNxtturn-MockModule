<template>
  <div class="wizard-panel">
    <h2 class="panel-title">5. Review &amp; Publish</h2>
    <p class="panel-sub">Review all information before publishing the exam.</p>

    <div class="review-grid">
      <ReviewCard title="Basic Information">
        <ReviewRow label="Exam Name" :value="form.basicInfo.examName" />
        <ReviewRow label="Short Name" :value="form.basicInfo.shortName" />
        <ReviewRow label="Full Form" :value="form.basicInfo.fullForm" />
        <ReviewRow label="Logo" value="Uploaded" v-if="form.basicInfo.examLogo" />
        <ReviewRow label="Banner" value="Uploaded" v-if="form.basicInfo.bannerImage" />
      </ReviewCard>

      <ReviewCard title="Classification &amp; Academic Mapping">
        <ReviewRow label="Exam Type" :value="form.classification.examType" />
        <ReviewRow label="Category" :value="form.classification.examCategory" />
        <ReviewRow label="Exam Level" :value="form.classification.examLevel" />
        <ReviewRow label="Conducting Body" :value="form.classification.conductingBody" />
        <ReviewRow label="Education Level" :value="form.academicMapping.educationLevel" />
        <ReviewRow label="Stream" :value="form.academicMapping.stream" />
        <ReviewRow label="Field" :value="form.academicMapping.field" />
      </ReviewCard>

      <ReviewCard title="Exam Details">
        <ReviewRow label="Duration" :value="form.examDetails.duration" />
        <ReviewRow label="Total Marks" :value="form.examDetails.totalMarks" />
        <ReviewRow label="Exam Mode" :value="form.examDetails.examMode" />
        <ReviewRow label="Negative Marking" :value="form.examDetails.negativeMarking" />
        <ReviewRow label="Frequency" :value="form.examDetails.examFrequency" />
      </ReviewCard>

      <ReviewCard title="Syllabus Summary">
        <ReviewRow label="Total Subjects" :value="String(form.syllabus.length)" />
        <ReviewRow label="Total Chapters" :value="String(totalChapters)" />
        <ReviewRow label="Total Topics" :value="String(totalTopics)" />
      </ReviewCard>

      <ReviewCard title="Important Dates">
        <ReviewRow label="Application Start" :value="form.importantDates.applicationStart" />
        <ReviewRow label="Application End" :value="form.importantDates.applicationEnd" />
        <ReviewRow label="Exam Date" :value="form.importantDates.examDate" />
        <ReviewRow label="Result Date" :value="form.importantDates.resultDate" />
      </ReviewCard>

      <ReviewCard title="Status &amp; Visibility">
        <ReviewRow label="Visibility" value="Public" />
        <ReviewRow label="Status" value="Draft" />
        <ReviewRow label="Show in Listing" value="Yes" />
      </ReviewCard>
    </div>

    <div class="panel-actions spread">
      <button class="btn btn-ghost" @click="$emit('back')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
        Back
      </button>
      <div style="display:flex; gap:10px">
        <button class="btn btn-ghost" @click="$emit('save-draft')">Save as Draft</button>
        <button class="btn btn-success" @click="$emit('publish')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4 20-7z"/></svg>
          Publish Exam
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, defineComponent } from 'vue'

const props = defineProps<{ form: any }>()
defineEmits(['back', 'save-draft', 'publish'])

const totalChapters = computed(() =>
  props.form.syllabus.reduce((sum: number, s: any) => sum + s.chapters.length, 0),
)
const totalTopics = computed(() =>
  props.form.syllabus.reduce(
    (sum: number, s: any) => sum + s.chapters.reduce((c: number, ch: any) => c + ch.topics.length, 0),
    0,
  ),
)

// Small local presentational components — kept inline since they're
// only used on this review screen.
const ReviewCard = defineComponent({
  props: { title: String },
  setup(props, { slots }) {
    return () =>
      h('div', { class: 'review-card' }, [
        h('div', { class: 'review-card-head' }, [
          h('span', props.title),
          h('button', { class: 'edit-link' }, 'Edit'),
        ]),
        h('div', { class: 'review-card-body' }, slots.default?.()),
      ])
  },
})

const ReviewRow = defineComponent({
  // CHANGED: was `value: String` — but Academic Mapping fields
  // (Education Level, Stream, Field, Sub Field) now come from live
  // API dropdowns that return numeric IDs (e.g. 2, 12) instead of the
  // old dummy string labels, which triggered a Vue prop-type warning.
  props: { label: String, value: [String, Number] },
  setup(props) {
    return () =>
      h('div', { class: 'review-row' }, [
        h('span', { class: 'review-label' }, props.label),
        h('span', { class: 'review-value' }, props.value ?? '—'),
      ])
  },
})
</script>

<style scoped>
@import './wizard-panel.css';
.panel-sub { font-size: 12px; color: #9CA3AF; margin: -14px 0 18px; }

.review-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

:deep(.review-card) {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 14px 16px;
}
:deep(.review-card-head) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 10px;
}
:deep(.edit-link) {
  background: none;
  border: none;
  color: #7C3AED;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}
:deep(.review-row) {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  margin-bottom: 8px;
}
:deep(.review-row:last-child) { margin-bottom: 0; }
:deep(.review-label) { color: #9CA3AF; }
:deep(.review-value) { color: #111827; font-weight: 600; text-align: right; }

@media (max-width: 900px) {
  .review-grid { grid-template-columns: 1fr 1fr; }
}
</style>