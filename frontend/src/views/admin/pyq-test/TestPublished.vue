<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const testDetails = [
  { label: 'Exam', value: 'JEE Main' },
  { label: 'Year', value: '2024' },
  { label: 'Subject', value: 'Physics' },
  { label: 'Total Questions', value: '90' },
  { label: 'Total Marks', value: '300' },
  { label: 'Status', value: 'Published', isBadge: true },
]

function goToTests() {
  router.push({ name: 'admin-tests-previous' })
}
</script>

<template>
      <div class="p-6 max-w-2xl mx-auto text-center">
        <div class="rounded-xl border border-gray-200 bg-white p-10">
          <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 text-emerald-500 text-3xl">
            ✓
          </div>
          <h2 class="text-lg font-semibold text-gray-800">Test Published Successfully!</h2>
          <p class="mt-1 text-xs text-gray-500">
            JEE Main 2024 (Paper 1) is now published and available for candidates.
          </p>

          <div class="mt-6 rounded-xl border border-gray-100 bg-gray-50 p-5 text-left">
            <p class="mb-3 text-xs font-semibold text-gray-600">Test Details</p>
            <div class="grid grid-cols-2 gap-y-3 text-xs">
              <template v-for="d in testDetails" :key="d.label">
                <span class="text-gray-400">{{ d.label }}</span>
                <span v-if="!d.isBadge" class="font-medium text-gray-700">{{ d.value }}</span>
                <span v-else>
                  <span class="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-600">
                    {{ d.value }}
                  </span>
                </span>
              </template>
            </div>
          </div>

          <button
            @click="goToTests"
            class="mt-6 rounded-lg bg-[#6C4CF1] px-5 py-2.5 text-xs font-semibold text-white hover:bg-[#5B3EE0]"
          >
            Go to PYQ Tests →
          </button>
        </div>
      </div>
</template>