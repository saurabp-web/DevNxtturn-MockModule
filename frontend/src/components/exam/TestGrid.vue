<template>
  <section class="panel test-list-panel">
    <h3 class="section-title">Upcoming Exams</h3>

    <div v-if="loading" class="loading">Loading exams...</div>

    <div v-else-if="!exams.length" class="empty-state">No exams match your filters.</div>

    <div v-else class="test-list">
      <TestCard
        v-for="exam in exams"
        :key="exam.exam_id"
        :exam="exam"
        @take="$emit('take', $event)"
        @bookmark="$emit('bookmark', $event)"
      />
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button
        v-for="page in pageNumbers"
        :key="page"
        class="page-btn"
        :class="{ active: page === currentPage, ellipsis: page === '...' }"
        :disabled="page === '...'"
        @click="page !== '...' && $emit('page-change', page as number)"
      >
        {{ page }}
      </button>
      <button
        class="page-btn next"
        :disabled="currentPage >= totalPages"
        @click="$emit('page-change', currentPage + 1)"
      >
        &rsaquo;
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TestCard from './TestCard.vue'
import type { Exam } from '../../types/exam'

const props = defineProps<{
  exams: Exam[]
  loading: boolean
  currentPage: number
  totalPages: number
}>()

defineEmits<{
  (e: 'page-change', page: number): void
  (e: 'take', exam: Exam): void
  (e: 'bookmark', exam: Exam): void
}>()

// Builds a compact page list like: 1 2 3 ... 10
const pageNumbers = computed<(number | string)[]>(() => {
  const total = props.totalPages
  const current = props.currentPage
  if (total <= 5) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | string)[] = [1, 2, 3]
  if (current > 4) pages.push('...')
  if (total > 3) pages.push(total)
  return pages
})
</script>

<style scoped>
.test-list-panel {
  background: #fff;
  padding: 18px;
}

.test-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 22px;
}

.page-btn {
  border: 1px solid #e5e7eb;
  background: #fff;
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: #1e2536;
}

.page-btn.active {
  background: #7c3aed;
  border-color: #7c3aed;
  color: #fff;
}

.page-btn.ellipsis {
  border: none;
  cursor: default;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}
</style>