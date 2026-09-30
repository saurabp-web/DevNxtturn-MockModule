<template>
  <div class="mb-6 flex items-center gap-3 text-xs">
    <template v-for="(label, i) in steps" :key="label">
      <span class="flex items-center gap-1.5" :class="labelClass(i)">
        <span class="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold" :class="circleClass(i)">
          <svg v-if="i < currentStep - 1" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <template v-else>{{ i + 1 }}</template>
        </span>
        {{ label }}
      </span>
      <span v-if="i < steps.length - 1" class="h-px w-10 bg-gray-200" />
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  // 1-based: 1 = Upload PDF, 2 = Map Paper Details, 3 = Review Questions, 4 = Create Test
  currentStep: { type: Number, required: true },
  steps: {
    type: Array,
    default: () => ['Upload PDF', 'Map Paper Details', 'Review Questions', 'Create Test'],
  },
})

function circleClass(i) {
  if (i < props.currentStep - 1) return 'bg-emerald-500 text-white'
  if (i === props.currentStep - 1) return 'bg-[#6C4CF1] text-white'
  return 'bg-gray-200 text-gray-500'
}
function labelClass(i) {
  if (i < props.currentStep - 1) return 'font-medium text-emerald-500'
  if (i === props.currentStep - 1) return 'font-semibold text-[#6C4CF1]'
  return 'text-gray-400'
}
</script>