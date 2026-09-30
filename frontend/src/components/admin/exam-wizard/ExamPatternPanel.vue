<template>
  <div class="wizard-panel">
    <h2 class="panel-title">Exam Pattern</h2>
    <p class="panel-sub">Configure the pattern for this exam.</p>

    <div class="pattern-grid">
      <div class="summary-card">
        <p class="summary-card-title" style="justify-content:flex-start">Pattern Summary</p>
        <div class="summary-row"><span class="summary-label">Total Questions</span><span class="summary-value">{{ totalQuestions }}</span></div>
        <div class="summary-row"><span class="summary-label">Total Marks</span><span class="summary-value">{{ totalMarks }}</span></div>
        <div class="summary-row"><span class="summary-label">Duration</span><span class="summary-value">{{ totalDuration }} Minutes</span></div>
        <div class="summary-row"><span class="summary-label">Negative Marking</span><span class="summary-value">{{ form.examPattern.negativeMarking }}</span></div>
        <div class="summary-row"><span class="summary-label">Marking Scheme</span><span class="summary-value">{{ form.examPattern.markingScheme }}</span></div>
        <div class="summary-row"><span class="summary-label">Unattempted</span><span class="summary-value">{{ form.examPattern.unattempted }}</span></div>
      </div>

      <div class="section-table-wrap">
        <p class="table-heading">Section Details</p>
        <table class="section-table">
          <thead>
            <tr><th>Section</th><th>Questions</th><th>Marks</th><th>Duration</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="(s, i) in form.examPattern.sections" :key="i">
              <td>
                <!-- FIXED: was plain text ({{ s.name }}) typed independently
                     of Syllabus, risking mismatches like "Physics" vs
                     "Physcis" between the two screens. Syllabus now runs
                     before Exam Pattern (Step 3, before Step 4), so section
                     names are picked from the subjects already entered
                     there instead of being retyped. -->
                <select v-model="s.name" class="section-name-select">
                  <option v-for="subj in subjectOptions" :key="subj" :value="subj">{{ subj }}</option>
                </select>
              </td>
              <td>{{ s.questions }}</td>
              <td>{{ s.marks }}</td>
              <td>{{ s.duration }}</td>
              <td class="row-actions">
                <button class="icon-btn" @click="editSection(i)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
                <button class="icon-btn danger" @click="removeSection(i)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!subjectOptions.length" class="no-subjects-hint">
          Add subjects in the Syllabus step first, then come back here to build sections from them.
        </p>
        <button class="btn btn-ghost add-section-btn" :disabled="!subjectOptions.length" @click="addSection">+ Add Section</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ form: any }>()

const totalQuestions = computed(() =>
  props.form.examPattern.sections.reduce((sum: number, s: any) => sum + Number(s.questions || 0), 0),
)
const totalMarks = computed(() =>
  props.form.examPattern.sections.reduce((sum: number, s: any) => sum + Number(s.marks || 0), 0),
)
const totalDuration = computed(() =>
  props.form.examPattern.sections.reduce((sum: number, s: any) => sum + parseInt(s.duration) || 0, 0),
)

// FIXED: section names now come from the subjects set up in the Syllabus
// step (props.form.syllabus), which now runs before this panel — instead
// of being free text disconnected from the syllabus.
const subjectOptions = computed(() => props.form.syllabus.map((s: any) => s.subject))

function addSection() {
  if (!subjectOptions.value.length) return
  // Default to the first subject that doesn't already have a section.
  const used = new Set(props.form.examPattern.sections.map((s: any) => s.name))
  const nextSubject = subjectOptions.value.find((s: string) => !used.has(s)) || subjectOptions.value[0]
  props.form.examPattern.sections.push({ name: nextSubject, questions: 0, marks: 0, duration: '0 Min' })
}
function removeSection(i: number) {
  props.form.examPattern.sections.splice(i, 1)
}
function editSection(i: number) {
  // Hook up an inline edit or modal here.
  console.log('Edit section', i)
}
</script>

<style scoped>
@import './wizard-panel.css';

.panel-sub { font-size: 12px; color: #9CA3AF; margin: -14px 0 18px; }

.pattern-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 20px;
}

.table-heading { font-size: 13px; font-weight: 700; color: #111827; margin: 0 0 10px; }
.section-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.section-table th {
  text-align: left;
  color: #9CA3AF;
  font-weight: 600;
  padding: 8px 10px;
  border-bottom: 1px solid #F3F4F6;
  text-transform: uppercase;
  font-size: 10px;
}
.section-table td {
  padding: 10px;
  border-bottom: 1px solid #F3F4F6;
  color: #374151;
}
.row-actions { display: flex; gap: 6px; }
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
}
.icon-btn:hover { background: #F3F4F6; }
.icon-btn.danger:hover { background: #FEF2F2; }
.add-section-btn { margin-top: 12px; width: 100%; justify-content: center; }
.add-section-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.section-name-select {
  font-size: 12px;
  color: #374151;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 5px 8px;
  background: #fff;
}
.no-subjects-hint {
  font-size: 12px;
  color: #9CA3AF;
  margin: 10px 0 0;
}
</style>