// src/services/adminApi.ts
//
// Uses the SAME axiosInstance as the rest of the app (Knox Token auth,
// baseURL '/api') — no new auth setup needed. Every request automatically
// carries the Authorization: Token <knox_token> header that axiosInstance
// already sets in auth.ts → setToken().

import axiosInstance from '@/services/axiosInstance'

// ─────────────────────────────────────────────
// Types — mirror the exact shapes Django sends
// ─────────────────────────────────────────────

export interface StatCard {
  label: string
  value: number
  trend: string
  icon: string
  color: string
}

export interface RecentExam {
  name: string
  type: string
  category: string
  status: string
  updatedOn: string
}

export interface ExamDistributionItem {
  label: string
  count: number
  percent: number
  color: string
}

export interface ExamTrendPoint {
  date: string
  count: number
}

export interface RecentTest {
  name: string
  exam: string
  type: string
  questions: number
  duration: string
  status: string
  updatedOn: string
}

// ─────────────────────────────────────────────
// API calls — each maps to one Django URL
// ─────────────────────────────────────────────

export const adminApi = {
  /**
   * GET /api/dashboard/stats/
   * Returns the 6 StatCard objects (mirrors adminDummyData.statsData shape).
   */
  getStats(): Promise<StatCard[]> {
    return axiosInstance.get('/dashboard/stats/').then(r => r.data)
  },

  /**
   * GET /api/dashboard/recent-exams/?limit=5
   * Returns last N exams (mirrors adminDummyData.recentExams shape).
   */
  getRecentExams(limit = 5): Promise<RecentExam[]> {
    return axiosInstance.get(`/dashboard/recent-exams/?limit=${limit}`).then(r => r.data)
  },

  /**
   * GET /api/dashboard/exam-distribution/
   * Returns exam counts by type for donut chart (mirrors examDistribution shape).
   */
  getExamDistribution(): Promise<ExamDistributionItem[]> {
    return axiosInstance.get('/dashboard/exam-distribution/').then(r => r.data)
  },

  /**
   * GET /api/dashboard/exam-trend/?days=7
   * Returns daily exam counts for line chart (mirrors examTrend shape).
   */
  getExamTrend(days = 7): Promise<ExamTrendPoint[]> {
    return axiosInstance.get(`/dashboard/exam-trend/?days=${days}`).then(r => r.data)
  },

  /**
   * GET /api/dashboard/recent-tests/?limit=5
   * Returns last N test definitions (mirrors recentTestActivity shape).
   */
  getRecentTests(limit = 5): Promise<RecentTest[]> {
    return axiosInstance.get(`/dashboard/recent-tests/?limit=${limit}`).then(r => r.data)
  },
}