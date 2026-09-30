<template>
  <label class="dropzone" :class="{ tall }">
    <input type="file" accept="image/*" class="hidden-input" @change="onChange" />
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="1.5">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
    <span class="dz-label">{{ modelValue ? modelValue.name : uploadLabel }}</span>
    <span class="dz-hint">{{ hint }}</span>
  </label>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: File | null
  hint: string
  tall?: boolean
}>()
const emit = defineEmits(['update:modelValue'])

const uploadLabel = 'Upload Logo'

function onChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] || null
  emit('update:modelValue', file)
}
</script>

<style scoped>
.dropzone {
  border: 1.5px dashed #D1D5DB;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 28px 12px;
  cursor: pointer;
  background: #FAFAFA;
  text-align: center;
}
.dropzone.tall { padding: 40px 12px; }
.dropzone:hover { border-color: #7C3AED; background: #F5F3FF; }
.hidden-input { display: none; }
.dz-label { font-size: 13px; font-weight: 600; color: #374151; }
.dz-hint { font-size: 11px; color: #9CA3AF; }
</style>