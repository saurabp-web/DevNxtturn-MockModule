// src/stores/adminDashboard.ts
//
// Fetches all 5 dashboard endpoints in parallel and stores the results.
// Components just import this store and read the refs — no axios code
// inside any component.

import { ref } from 'vue'
import { defineStore } from 'pinia'
import { adminApi } from '@/services/adminApi'
import type {
  StatCard, RecentExam, ExamDistributionItem,
  ExamTrendPoint, RecentTest,
} from '@/services/adminApi'

export const useAdminDashboardStore = defineStore('adminDashboard', () => {

  // ── state ──────────────────────────────────────────────────────────────
  const stats            = ref<StatCard[]>([])
  const recentExams      = ref<RecentExam[]>([])
  const examDistribution = ref<ExamDistributionItem[]>([])
  const examTrend        = ref<ExamTrendPoint[]>([])
  const recentTests      = ref<RecentTest[]>([])

  const loading = ref(false)
  const error   = ref<string | null>(null)

  // ── actions ─────────────────────────────────────────────────────────────

  /**
   * Load all dashboard data in one parallel burst.
   * Safe to call multiple times — shows loading state while fetching.
   */
  async function fetchAll() {
    loading.value = true
    error.value   = null

    try {
      const [s, re, ed, et, rt] = await Promise.all([
        adminApi.getStats(),
        adminApi.getRecentExams(5),
        adminApi.getExamDistribution(),
        adminApi.getExamTrend(7),
        adminApi.getRecentTests(5),
      ])

      stats.value            = s
      recentExams.value      = re
      examDistribution.value = ed
      examTrend.value        = et
      recentTests.value      = rt

    } catch (e: any) {
      // axios wraps HTTP errors — pull out the most useful message
      error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load dashboard'
      console.error('[adminDashboard] fetchAll failed:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    stats, recentExams, examDistribution, examTrend, recentTests,
    loading, error,
    fetchAll,
  }
})