<template>
  <div class="stats-card">
    <div class="stats-icon" :style="{ background: iconBg }">
      <span v-html="iconSvg" :style="{ color: color }"></span>
    </div>
    <div class="stats-body">
      <div class="stats-label">{{ label }}</div>
      <div class="stats-value">{{ formattedValue }}</div>
      <div class="stats-trend">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
        </svg>
        <span>{{ trend }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: number
  trend: string
  icon: string
  color: string
}>()

const iconBg = computed(() => props.color + '18')

const formattedValue = computed(() =>
  props.value >= 1000 ? props.value.toLocaleString() : String(props.value)
)

const iconSvg = computed(() => {
  const icons: Record<string, string> = {
    graduation: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`,
    'file-check': `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 15 11 17 15 13"/></svg>`,
    pencil: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>`,
    clock: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    book: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
    question: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  }
  return icons[props.icon] || icons['question']
})
</script>

<style scoped>
.stats-card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  flex: 1;
  min-width: 150px;
  transition: box-shadow 0.2s;
}
.stats-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.07); }

.stats-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stats-body { flex: 1; }
.stats-label { font-size: 12px; color: #6B7280; font-weight: 500; margin-bottom: 4px; }
.stats-value { font-size: 26px; font-weight: 700; color: #111827; line-height: 1; margin-bottom: 6px; }
.stats-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #10B981;
  font-weight: 500;
}
</style>