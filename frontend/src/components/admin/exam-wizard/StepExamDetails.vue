<template>
  <div>
    <!-- 4. General exam details -->
    <div class="wizard-panel">
      <h2 class="panel-title">4. Exam Details</h2>

      <!-- FIXED: this used to also have a freeform "Eligibility" textarea
           here, duplicating 4D's structured Eligibility panel below.
           Removed — 4D is now the single place eligibility is entered. -->
      <div class="panel-grid">
        <div class="col">
          <div class="field">
            <label>Duration</label>
            <input v-model="form.examDetails.duration" type="text" placeholder="Enter duration (e.g. 180 min)" />
          </div>
          <div class="field">
            <label>Total Marks</label>
            <input v-model="form.examDetails.totalMarks" type="text" placeholder="Enter total marks" />
          </div>
          <div class="field">
            <label>Age Limit (if any)</label>
            <input v-model="form.examDetails.ageLimit" type="text" placeholder="Enter age limit" />
          </div>
        </div>

        <div class="col">
          <div class="field">
            <label>Negative Marking</label>
            <select v-model="form.examDetails.negativeMarking">
              <option value="" disabled>Select negative marking</option>
              <option>Yes</option>
              <option>No</option>
            </select>
          </div>
          <div class="field">
            <label>Exam Mode</label>
            <select v-model="form.examDetails.examMode">
              <option value="" disabled>Select exam mode</option>
              <option>Computer Based</option>
              <option>Pen &amp; Paper</option>
            </select>
          </div>
          <div class="field">
            <label>Official Website</label>
            <input v-model="form.examDetails.officialWebsite" type="text" placeholder="Enter official website URL" />
          </div>
        </div>
      </div>

      <!-- FIXED: Application Mode / Exam Frequency / Helpline-Contact
           demoted from required top-level fields to an optional,
           collapsed section — most admins don't have or need this at
           exam-creation time, and it no longer blocks Next. -->
      <div class="optional-section">
        <button type="button" class="optional-toggle" @click="showOptional = !showOptional">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ transform: showOptional ? 'rotate(90deg)' : 'none' }">
            <polyline points="9 18 15 12 9 6" />
          </svg>
          Additional Details <span class="optional-tag">Optional</span>
        </button>
        <div v-if="showOptional" class="panel-grid optional-grid">
          <div class="field">
            <label>Application Mode</label>
            <select v-model="form.examDetails.applicationMode">
              <option value="" disabled>Select application mode</option>
              <option>Online</option>
              <option>Offline</option>
              <option>Both</option>
            </select>
          </div>
          <div class="field">
            <label>Exam Frequency</label>
            <select v-model="form.examDetails.examFrequency">
              <option value="" disabled>Select frequency</option>
              <option>Annual</option>
              <option>Bi-Annual</option>
              <option>Quarterly</option>
            </select>
          </div>
          <div class="field">
            <label>Helpline / Contact</label>
            <input v-model="form.examDetails.helplineContact" type="text" placeholder="Enter helpline or contact info" />
          </div>
        </div>
      </div>

      <div class="panel-actions">
        <button class="btn btn-ghost" @click="$emit('back')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
          Back
        </button>
        <button class="btn btn-primary" @click="$emit('next')">
          Next
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </button>
      </div>
    </div>

    <!-- FIXED: sub-tabs removed. Tabs hid two of three required panels
         at a time, making it easy to forget "Important Dates" or
         "Eligibility" since they weren't visible unless clicked into.
         All three now render stacked, always visible, each in its own
         labeled card — nothing required is hidden behind a click. -->
    <ExamPatternPanel :form="form" />
    <ImportantDatesPanel :form="form" />
    <EligibilityPanel :form="form" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ExamPatternPanel from './ExamPatternPanel.vue'
import ImportantDatesPanel from './ImportantDatesPanel.vue'
import EligibilityPanel from './EligibilityPanel.vue'

defineProps<{ form: any }>()
defineEmits(['next', 'back'])

const showOptional = ref(false)
</script>

<style scoped>
@import './wizard-panel.css';

.optional-section {
  margin-top: 6px;
  border-top: 1px dashed #E5E7EB;
  padding-top: 14px;
}
.optional-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  padding: 0;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
}
.optional-toggle svg { transition: transform 0.15s ease; color: #9CA3AF; }
.optional-tag {
  font-size: 10px;
  font-weight: 600;
  color: #9CA3AF;
  background: #F3F4F6;
  border-radius: 999px;
  padding: 2px 8px;
  margin-left: 4px;
}
.optional-grid { margin-top: 14px; }

/* Spacing between the stacked sub-panels below the main Exam Details card */
:deep(.wizard-panel + .wizard-panel) {
  margin-top: 20px;
}
</style>