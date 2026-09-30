<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">
        Exam Trend <span class="chart-sub">(Last {{ days }} Days)</span>
      </h3>
      <select class="period-select" v-model="days" @change="$emit('changeDays', days)">
        <option :value="7">Last 7 Days</option>
        <option :value="30">Last 30 Days</option>
        <option :value="90">Last 90 Days</option>
      </select>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="skeleton-chart" />

    <!-- Live SVG chart -->
    <div v-else class="chart-body">
      <svg :viewBox="`0 0 ${svgW} ${svgH}`" preserveAspectRatio="none" class="trend-svg">
        <!-- Grid lines + Y labels -->
        <line v-for="(y, i) in yGridPositions" :key="i"
          x1="40" :y1="y" x2="680" :y2="y"
          stroke="#F3F4F6" stroke-width="1"/>
        <text v-for="(label, i) in yLabels" :key="'yl'+i"
          x="32" :y="yGridPositions[i] + 4"
          text-anchor="end" font-size="11" fill="#9CA3AF">{{ label }}</text>

        <!-- X labels -->
        <text v-for="(point, i) in data" :key="'xl'+i"
          :x="xPos(i)" :y="svgH - 4"
          text-anchor="middle" font-size="11" fill="#9CA3AF">{{ point.date }}</text>

        <!-- Area fill -->
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stop-color="#7C3AED" stop-opacity="0.15"/>
            <stop offset="100%" stop-color="#7C3AED" stop-opacity="0.01"/>
          </linearGradient>
        </defs>
        <path v-if="data.length" :d="areaPath" fill="url(#areaGrad)"/>
        <path v-if="data.length" :d="linePath"
          fill="none" stroke="#7C3AED" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"/>

        <!-- Dots -->
        <circle v-for="(point, i) in data" :key="'dot'+i"
          :cx="xPos(i)" :cy="yPos(point.count)"
          r="4" fill="#fff" stroke="#7C3AED" stroke-width="2"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ExamTrendPoint } from '@/services/adminApi'

const props = defineProps<{
  data: ExamTrendPoint[]
  loading?: boolean
}>()

const emit = defineEmits<{ (e: 'changeDays', days: number): void }>()

const days = ref(7)

const svgW = 700
const svgH = 220
const padL = 40, padR = 20, padT = 10, padB = 30

const maxVal = computed(() => Math.max(...props.data.map(d => d.count), 10))

const ySteps = computed(() => {
  const m = maxVal.value
  const step = Math.ceil(m / 4 / 5) * 5 || 5
  return [step * 4, step * 3, step * 2, step, 0]
})

const yLabels = computed(() => ySteps.value.map(String))
const yGridPositions = computed(() => ySteps.value.map(v => yPos(v)))

function yPos(val: number) {
  return padT + ((maxVal.value - val) / maxVal.value) * (svgH - padT - padB)
}
function xPos(i: number) {
  const n = props.data.length
  return padL + (n <= 1 ? 0 : i / (n - 1)) * (svgW - padL - padR)
}

const linePath = computed(() =>
  props.data.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xPos(i)} ${yPos(p.count)}`).join(' ')
)
const areaPath = computed(() => {
  const n = props.data.length
  if (!n) return ''
  const line  = props.data.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xPos(i)} ${yPos(p.count)}`).join(' ')
  const close = `L ${xPos(n - 1)} ${svgH - padB} L ${xPos(0)} ${svgH - padB} Z`
  return line + ' ' + close
})
</script>

<style scoped>
.chart-card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px 24px;
}
.chart-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.chart-title  { font-size: 15px; font-weight: 600; color: #111827; margin: 0; }
.chart-sub    { color: #6B7280; font-weight: 400; font-size: 13px; }

.period-select {
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  color: #374151;
  background: #fff;
  outline: none;
  cursor: pointer;
}

.skeleton-chart {
  height: 180px;
  border-radius: 8px;
  background: #F3F4F6;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.chart-body { overflow-x: auto; }
.trend-svg  { width: 100%; height: auto; display: block; }
</style>