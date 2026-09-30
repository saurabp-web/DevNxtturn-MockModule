<template>
  <div class="wizard-panel">
    <h2 class="panel-title">1. Basic Information</h2>
    <div class="panel-grid">
      <div class="col">
        <div class="field">
          <label>Exam Name <span class="req">*</span></label>
          <input v-model="form.basicInfo.examName" type="text" placeholder="Enter exam name" />
        </div>
        <div class="field">
          <label>Short Name <span class="req">*</span></label>
          <input v-model="form.basicInfo.shortName" type="text" placeholder="Enter short name (e.g. JEE)" />
        </div>
        <div class="field">
          <label>Full Form</label>
          <input v-model="form.basicInfo.fullForm" type="text" placeholder="Enter full form of the exam" />
        </div>
        <div class="field">
          <label>Description</label>
          <textarea
            v-model="form.basicInfo.description"
            maxlength="1000"
            rows="5"
            placeholder="Enter detailed description about the exam"
          />
          <span class="char-count">{{ form.basicInfo.description.length }} / 1000</span>
        </div>
      </div>

      <div class="col">
        <div class="field">
          <label>Exam Logo <span class="req">*</span></label>
          <FileDropZone v-model="form.basicInfo.examLogo" hint="PNG, JPG or SVG (Max. 2MB)" />
        </div>
        <div class="field">
          <label>Banner Image</label>
          <FileDropZone v-model="form.basicInfo.bannerImage" hint="PNG, JPG or SVG (Max. 5MB)" tall />
        </div>
      </div>
    </div>

    <div class="panel-actions">
      <button class="btn btn-ghost">Cancel</button>
      <button class="btn btn-primary" @click="$emit('next')">
        Next
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import FileDropZone from './FileDropZone.vue'

defineProps<{ form: any }>()
defineEmits(['next', 'back'])
</script>

<style scoped>
@import './wizard-panel.css';
</style>