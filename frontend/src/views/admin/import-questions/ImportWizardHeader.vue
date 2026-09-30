<template>
  <div class="wizard-header">
    <!-- Stepper -->
    <div class="stepper">
      <template v-for="(label, i) in steps" :key="label">
        <div class="step-item">
          <div class="step-circle" :class="circleClass(i)">
            <CheckIcon v-if="i < currentStep" />
            <span v-else>{{ i + 1 }}</span>
          </div>
          <span class="step-label" :class="labelClass(i)">{{ label }}</span>
        </div>
        <div v-if="i < steps.length - 1" class="step-line" :class="{ done: i < currentStep }" />
      </template>
    </div>

    <!-- Selected Exam Banner -->
    <div v-if="examName" class="exam-banner">
      <div class="exam-info">
        <p class="exam-banner-label">Selected Exam</p>
        <p class="exam-banner-name">{{ examName }}</p>
      </div>
      <button v-if="allowChangeExam" class="change-exam-btn" @click="$emit('change-exam')">
        Change Exam
        <EditIcon />
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  steps: { type: Array, required: true },
  currentStep: { type: Number, required: true }, // 0-based
  examName: { type: String, default: '' },
  allowChangeExam: { type: Boolean, default: true },
})
defineEmits(['change-exam'])

function circleClass(i) {
  if (i < props.currentStep) return 'done'
  if (i === props.currentStep) return 'active'
  return ''
}
function labelClass(i) {
  if (i < props.currentStep) return 'done'
  if (i === props.currentStep) return 'active'
  return ''
}

const CheckIcon = { template: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>` }
const EditIcon = { template: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>` }
</script>

<style scoped>
* { box-sizing: border-box; }
.wizard-header {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  margin-bottom: 20px;
}

/* ── Stepper ── */
.stepper {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  row-gap: 12px;
}
.step-item { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.step-circle {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  background: #F3F2F9; color: #A6A4B4;
  border: 1.5px solid #E4E2ED;
  flex-shrink: 0;
  transition: background 0.2s, color 0.2s;
}
.step-circle.active {
  background: #6C4CF1; color: #fff; border-color: #6C4CF1;
}
.step-circle.done {
  background: #1FAE5C; color: #fff; border-color: #1FAE5C;
}

.step-label {
  font-size: 13px; font-weight: 600; color: #A6A4B4; white-space: nowrap;
}
.step-label.active { color: #14121F; }
.step-label.done  { color: #1FAE5C; }

.step-line {
  width: 64px; height: 2px;
  background: #E4E2ED;
  margin: 0 8px; flex-shrink: 0;
  transition: background 0.2s;
}
.step-line.done { background: #1FAE5C; }

/* ── Exam Banner ── */
.exam-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px;
  border-radius: 12px;
  background: #F5F2FF;
  border: 1px solid #E4DBFF;
}
.exam-info {}
.exam-banner-label {
  font-size: 11.5px; font-weight: 600; color: #6C4CF1; margin: 0 0 2px;
}
.exam-banner-name {
  font-size: 15px; font-weight: 700; color: #14121F; margin: 0;
}
.change-exam-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid #D8D5E8;
  background: #fff;
  color: #524F6B;
  font-size: 12.5px; font-weight: 600;
  cursor: pointer; white-space: nowrap;
}
.change-exam-btn:hover { background: #F6F5FB; }

@media (max-width: 860px) {
  .step-line { width: 28px; }
}
</style>