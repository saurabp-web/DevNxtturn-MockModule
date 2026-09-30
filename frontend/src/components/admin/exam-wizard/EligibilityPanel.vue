<template>
  <div class="wizard-panel">
    <h2 class="panel-title">Eligibility</h2>
    <p class="panel-sub">Define the eligibility criteria for this exam.</p>

    <div class="field">
      <label>Educational Qualification <span class="req">*</span></label>
      <textarea
        v-model="form.eligibility.educationalQualification"
        rows="3"
        maxlength="500"
        placeholder="Candidate must have passed 10+2 or equivalent examination..."
      />
      <span class="char-count">{{ form.eligibility.educationalQualification.length }} / 500</span>
    </div>

    <div class="field">
      <label>Minimum Marks (%)</label>
      <textarea
        v-model="form.eligibility.minimumMarks"
        rows="2"
        maxlength="500"
        placeholder="Enter minimum percentage"
      />
      <span class="char-count">{{ form.eligibility.minimumMarks.length }} / 500</span>
    </div>

    <div class="panel-grid" style="margin-top:6px">
      <div class="field">
        <label>Age Criteria (if any)</label>
        <input v-model="form.eligibility.ageCriteria" type="text" placeholder="Enter age criteria" />
      </div>
      <div class="field">
        <label>Other Conditions</label>
        <input v-model="form.eligibility.otherConditions" type="text" placeholder="Enter other conditions" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ form: any }>()
</script>

<style scoped>
@import './wizard-panel.css';
.panel-sub { font-size: 12px; color: #9CA3AF; margin: -14px 0 18px; }
</style>