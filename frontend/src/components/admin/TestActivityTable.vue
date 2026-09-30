<template>
  <div class="table-card">
    <div class="table-header">
      <h3 class="table-title">Recent Test Activity</h3>
      <button class="view-all-btn">View All</button>
    </div>

    <!-- Skeleton rows -->
    <template v-if="loading">
      <div v-for="i in 5" :key="i" class="skeleton-row" />
    </template>

    <!-- Live table -->
    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>TEST NAME</th><th>EXAM</th><th>TYPE</th>
            <th>QUESTIONS</th><th>DURATION</th><th>STATUS</th>
            <th>UPDATED ON</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!tests.length">
            <td colspan="8" class="empty">No recent test activity found.</td>
          </tr>
          <tr v-for="test in tests" :key="test.name + test.updatedOn">
            <td class="test-name">{{ test.name }}</td>
            <td class="muted">{{ test.exam }}</td>
            <td class="muted">{{ test.type }}</td>
            <td class="center">{{ test.questions }}</td>
            <td class="muted">{{ test.duration }}</td>
            <td><span class="status-badge" :class="statusClass(test.status)">{{ test.status }}</span></td>
            <td class="muted">{{ test.updatedOn }}</td>
            <td>
              <button class="more-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RecentTest } from '@/services/adminApi'

defineProps<{
  tests: RecentTest[]
  loading?: boolean
}>()

function statusClass(status: string) {
  const s = status.toLowerCase()
  if (s === 'published') return 'status-published'
  if (s === 'draft')     return 'status-draft'
  return 'status-review'
}
</script>

<style scoped>
.table-card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px 0 0;
}
.table-header {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 0 24px 16px;
}
.table-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0; }
.view-all-btn {
  border: 1px solid #E5E7EB; background: #fff;
  border-radius: 6px; padding: 5px 12px;
  font-size: 12px; color: #374151; cursor: pointer; font-weight: 500;
}
.view-all-btn:hover { background: #F9FAFB; }

.skeleton-row {
  height: 44px; margin: 0 16px 6px;
  border-radius: 6px; background: #F3F4F6;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.table-wrap  { overflow-x: auto; }
.data-table  { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; font-size: 11px; font-weight: 600;
  color: #9CA3AF; letter-spacing: .05em;
  padding: 8px 16px; border-bottom: 1px solid #F3F4F6; white-space: nowrap;
}
.data-table td {
  padding: 12px 16px; border-bottom: 1px solid #F9FAFB; font-size: 13px;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: #FAFAFA; }

.test-name { font-weight: 600; color: #111827; white-space: nowrap; }
.muted     { color: #6B7280; white-space: nowrap; }
.center    { color: #374151; text-align: center; }
.empty     { text-align: center; color: #9CA3AF; padding: 24px; }

.status-badge {
  display: inline-block; padding: 3px 10px;
  border-radius: 20px; font-size: 11px; font-weight: 600;
}
.status-published { color: #059669; background: #D1FAE5; }
.status-review    { color: #D97706; background: #FEF3C7; }
.status-draft     { color: #6B7280; background: #F3F4F6; }

.more-btn {
  background: none; border: none; cursor: pointer;
  color: #9CA3AF; padding: 2px; border-radius: 4px;
}
.more-btn:hover { background: #F3F4F6; color: #374151; }
</style>