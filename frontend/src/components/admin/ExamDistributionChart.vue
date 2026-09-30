<template>
  <div class="chart-card">
    <h3 class="chart-title">Exam Distribution by Type</h3>

    <!-- Skeleton -->
    <div v-if="loading" class="skeleton-body">
      <div class="skeleton-circle" />
      <div class="skeleton-legend">
        <div v-for="i in 3" :key="i" class="skeleton-line" />
      </div>
    </div>

    <!-- Live chart -->
    <div v-else class="chart-body">
      <div class="donut-wrap">
        <svg width="180" height="180" viewBox="0 0 180 180">
          <circle cx="90" cy="90" r="70" fill="none" stroke="#F3F4F6" stroke-width="28"/>
          <circle
            v-for="(seg, i) in segments"
            :key="i"
            cx="90" cy="90" r="70"
            fill="none"
            :stroke="seg.color"
            stroke-width="28"
            :stroke-dasharray="`${seg.dash} ${seg.gap}`"
            :stroke-dashoffset="seg.offset"
            stroke-linecap="butt"
          />
        </svg>
        <div class="donut-center">
          <span class="donut-total">{{ total }}</span>
          <span class="donut-sub">Total Exams</span>
        </div>
      </div>

      <div class="chart-legend">
        <div v-for="item in data" :key="item.label" class="legend-item">
          <span class="legend-dot" :style="{ background: item.color }"></span>
          <span class="legend-label">{{ item.label }}</span>
          <span class="legend-count">{{ item.count }} ({{ item.percent }}%)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ExamDistributionItem } from '@/services/adminApi'

const props = defineProps<{
  data: ExamDistributionItem[]
  loading?: boolean
}>()

const circumference = 2 * Math.PI * 70

const total = computed(() => props.data.reduce((s, d) => s + d.count, 0))

const segments = computed(() => {
  let offset = circumference * 0.25
  return props.data.map(item => {
    const dash = (item.percent / 100) * circumference
    const gap  = circumference - dash
    const seg  = { color: item.color, dash, gap, offset: -offset + circumference }
    offset += dash
    return seg
  })
})
</script>

<style scoped>
.chart-card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px 24px;
}
.chart-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 20px; }

/* Skeleton */
.skeleton-body   { display: flex; gap: 32px; align-items: center; }
.skeleton-circle { width: 180px; height: 180px; border-radius: 50%; background: #F3F4F6; flex-shrink: 0; animation: shimmer 1.4s infinite; }
.skeleton-legend { display: flex; flex-direction: column; gap: 14px; flex: 1; }
.skeleton-line   { height: 18px; border-radius: 6px; background: #F3F4F6; animation: shimmer 1.4s infinite; }
.skeleton-line:nth-child(2) { width: 75%; }
.skeleton-line:nth-child(3) { width: 60%; }

@keyframes shimmer {
  0%, 100% { opacity: 1; } 50% { opacity: 0.5; }
}

/* Chart */
.chart-body { display: flex; align-items: center; gap: 32px; flex-wrap: wrap; }

.donut-wrap { position: relative; width: 180px; height: 180px; flex-shrink: 0; }
.donut-wrap svg { transform: rotate(-90deg); }
.donut-center {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.donut-total { font-size: 28px; font-weight: 800; color: #111827; }
.donut-sub   { font-size: 11px; color: #6B7280; font-weight: 500; }

.chart-legend { display: flex; flex-direction: column; gap: 14px; }
.legend-item  { display: flex; align-items: center; gap: 10px; }
.legend-dot   { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.legend-label { font-size: 13px; color: #374151; font-weight: 500; flex: 1; }
.legend-count { font-size: 13px; color: #6B7280; }
</style>