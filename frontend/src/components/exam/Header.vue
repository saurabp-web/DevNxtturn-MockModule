<template>
  <div class="portal-header">
    <h1 class="portal-title">EXAM PREPARATION PORTAL</h1>
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="tab"
        :class="{ active: modelValue === tab.value }"
        @click="$emit('update:modelValue', tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: 'all' },
})
defineEmits(['update:modelValue'])

// NOTE: your Exam model doesn't currently have a "category" field,
// so these tabs aren't wired to a filter yet. Hook this up once
// exam_category (or similar) exists on the backend.
const tabs = [
  { label: 'All Tests', value: 'all' },
  { label: 'Previous Year Papers', value: 'previous' },
  { label: 'Practice Tests', value: 'practice' },
  { label: 'Mock Tests', value: 'mock' },
]
</script>
