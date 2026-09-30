<template>
  <!-- CHANGED: no longer wrapped in <AdminLayout>...</AdminLayout>.
       AdminLayout is the parent ROUTE component (see router/index.ts)
       and now renders its children via <router-view /> instead of a
       <slot />, so this view's content goes directly there. Wrapping
       it in <AdminLayout> here would have created a second, nested
       sidebar/topbar — this fragment (or a single root div) is all
       that's needed. -->
  <div>
    <div v-if="loadError" class="load-error-banner">
      ⚠️ Could not load live data ({{ loadError }}) — showing sample data instead.
    </div>

    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-sub">Welcome back, Saurabh! Here's what's happening with your exam platform.</p>
      </div>
      <div class="date-range">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span>May 12 – May 18, 2025</span>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <StatsCard
        v-for="stat in statsData"
        :key="stat.label"
        :label="stat.label"
        :value="stat.value"
        :trend="stat.trend"
        :icon="stat.icon"
        :color="stat.color"
      />
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <div class="chart-col-left">
        <ExamDistributionChart :data="examDistribution" />
      </div>
      <div class="chart-col-right">
        <RecentExamsTable :exams="recentExams" />
      </div>
    </div>

    <!-- Trend + Quick Actions Row -->
    <div class="mid-row">
      <div class="trend-col">
        <ExamTrendChart :data="examTrend" />
      </div>
      <div class="qa-col">
        <QuickActions />
      </div>
    </div>

    <!-- Test Activity -->
    <div class="bottom-row">
      <TestActivityTable :tests="recentTestActivity" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StatsCard from '@/components/admin/StatsCard.vue'
import ExamDistributionChart from '@/components/admin/ExamDistributionChart.vue'
import RecentExamsTable from '@/components/admin/RecentExamsTable.vue'
import ExamTrendChart from '@/components/admin/ExamTrendChart.vue'
import QuickActions from '@/components/admin/QuickActions.vue'
import TestActivityTable from '@/components/admin/TestActivityTable.vue'
import {
  adminApi,
  type StatCard,
  type RecentExam,
  type ExamDistributionItem,
  type ExamTrendPoint,
  type RecentTest,
} from '@/services/adminApi'
import {
  statsData as dummyStats,
  recentExams as dummyExams,
  examDistribution as dummyDistribution,
  examTrend as dummyTrend,
  recentTestActivity as dummyTests,
} from '@/data/adminDummyData'

// Same variable names/shapes as adminDummyData.ts — child components
// need no changes, only these values now come from Django (via
// adminApi.ts, which already carries Knox token auth) instead of the
// static file. Seeded with dummy data up front so the page never
// renders fully blank while the API call is in flight or if it fails.
const statsData = ref<StatCard[]>(dummyStats)
const recentExams = ref<RecentExam[]>(dummyExams)
const examDistribution = ref<ExamDistributionItem[]>(dummyDistribution)
const examTrend = ref<ExamTrendPoint[]>(dummyTrend)
const recentTestActivity = ref<RecentTest[]>(dummyTests)
const loadError = ref<string | null>(null)

onMounted(async () => {
  try {
    const [stats, exams, distribution, trend, tests] = await Promise.all([
      adminApi.getStats(),
      adminApi.getRecentExams(5),
      adminApi.getExamDistribution(),
      adminApi.getExamTrend(7),
      adminApi.getRecentTests(5),
    ])
    statsData.value = stats
    recentExams.value = exams
    examDistribution.value = distribution
    examTrend.value = trend
    recentTestActivity.value = tests
  } catch (err: any) {
    // Falls back to the dummy data already seeded above — page stays
    // visible instead of going blank. Check the browser console for
    // this exact message to see what actually failed (CORS, 401, 404, etc).
    loadError.value = err?.message || 'Failed to load dashboard data'
    console.error('[DashboardView] Failed to load live dashboard data, showing dummy data instead:', err)
  }
})
</script>

<style scoped>
.load-error-banner {
  background: #FEF3C7;
  border: 1px solid #F59E0B;
  color: #92400E;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}
.page-title { font-size: 22px; font-weight: 700; color: #111827; margin: 0 0 4px; }
.page-sub { font-size: 13px; color: #6B7280; margin: 0; }

.date-range {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  white-space: nowrap;
}

/* Stats */
.stats-row {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

/* Charts row */
.charts-row {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

/* Mid row */
.mid-row {
  display: grid;
  grid-template-columns: 1fr 480px;
  gap: 16px;
  margin-bottom: 16px;
}

/* Bottom */
.bottom-row { margin-bottom: 24px; }

@media (max-width: 1100px) {
  .charts-row { grid-template-columns: 1fr; }
  .mid-row { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .stats-row { gap: 10px; }
}
</style>