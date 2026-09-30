<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const progress = ref(60)
const totalPages = 32
const questionsFound = 90
const mcqCount = 75
const nonMcqCount = 15
const extractedCount = ref(54)

onMounted(() => {
  const timer = setInterval(() => {
    if (progress.value < 100) {
      progress.value += 10
      extractedCount.value = Math.round((progress.value / 100) * questionsFound)
    } else {
      clearInterval(timer)
    }
  }, 500)
})

function goNext() {
  router.push({ name: 'admin-tests-previous-map-questions' })
}
</script>

<template>
      <div class="p-6 max-w-3xl">
        <div class="flex items-center gap-2 text-xs text-gray-400 mb-5">
          <span class="flex items-center gap-1 font-medium text-[#6C4CF1]">
            <span class="flex h-4 w-4 items-center justify-center rounded-full bg-[#6C4CF1] text-[10px] text-white">1</span>
            Extract Questions
          </span>
          <span>&rarr;</span>
          <span class="flex items-center gap-1">
            <span class="flex h-4 w-4 items-center justify-center rounded-full bg-gray-200 text-[10px] text-gray-500">2</span>
            Map Questions
          </span>
          <span>&rarr;</span>
          <span class="flex items-center gap-1">
            <span class="flex h-4 w-4 items-center justify-center rounded-full bg-gray-200 text-[10px] text-gray-500">3</span>
            Review
          </span>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-6">
          <div class="mb-5 flex items-start gap-2 rounded-lg bg-violet-50 px-3 py-2.5 text-xs text-violet-800">
            <span>ℹ️</span>
            <span>We are extracting questions from your PDF. This may take a few minutes.</span>
          </div>

          <p class="mb-2 text-xs font-semibold text-gray-600">Extraction Progress</p>
          <div class="h-2 w-full overflow-hidden rounded-full bg-gray-100">
            <div class="h-full rounded-full bg-[#6C4CF1] transition-all" :style="{ width: progress + '%' }" />
          </div>
          <p class="mt-1.5 text-[11px] text-gray-400">Extracted {{ extractedCount }} of {{ questionsFound }} questions...</p>

          <div class="mt-6 grid grid-cols-3 gap-4">
            <div class="rounded-lg border border-gray-100 p-4 text-center">
              <p class="text-xl font-semibold text-gray-800">{{ totalPages }}</p>
              <p class="text-[11px] text-gray-400 mt-1">Total Pages</p>
            </div>
            <div class="rounded-lg border border-gray-100 p-4 text-center">
              <p class="text-xl font-semibold text-gray-800">{{ questionsFound }}</p>
              <p class="text-[11px] text-gray-400 mt-1">Questions Found</p>
            </div>
            <div class="rounded-lg border border-gray-100 p-4 text-center">
              <p class="text-xl font-semibold text-gray-800">{{ mcqCount }}</p>
              <p class="text-[11px] text-gray-400 mt-1">MCQ Questions</p>
            </div>
          </div>
          <div class="mt-4 grid grid-cols-3 gap-4">
            <div class="rounded-lg border border-gray-100 p-4 text-center">
              <p class="text-xl font-semibold text-gray-800">{{ nonMcqCount }}</p>
              <p class="text-[11px] text-gray-400 mt-1">Non-MCQ Questions</p>
            </div>
          </div>

          <p v-if="progress >= 100" class="mt-4 text-[11px] text-emerald-500">
            ⓘ You can continue once extraction is completed.
          </p>
        </div>

        <div class="mt-6 flex justify-end">
          <button @click="goNext" class="rounded-lg bg-[#6C4CF1] px-4 py-2 text-xs font-semibold text-white hover:bg-[#5B3EE0]">
            Next: Map Questions →
          </button>
        </div>
      </div>
</template>