<template>
  <div class="prep-page">

    <!-- Loading state -->
    <div v-if="preparing" class="prep-box">
      <div class="prep-illustration">
        <div class="prep-icon">📋</div>
        <div class="prep-rings">
          <div class="ring ring1"></div>
          <div class="ring ring2"></div>
          <div class="ring ring3"></div>
        </div>
      </div>
      <h2 class="prep-title">Preparing your practice session...</h2>
      <p class="prep-sub">We are setting up your complete syllabus practice.<br>This will just take a moment.</p>
      <div class="dots">
        <span class="dot" :class="{ active: dot >= 1 }"></span>
        <span class="dot" :class="{ active: dot >= 2 }"></span>
        <span class="dot" :class="{ active: dot >= 3 }"></span>
      </div>
      <div v-if="error" class="prep-error">
        {{ error }}
        <button class="retry-btn" @click="prepare">Retry</button>
      </div>
    </div>

    <!-- Summary before starting -->
    <div v-else class="summary-box">
      <div class="sum-icon">✅</div>
      <h2 class="sum-title">Ready to start!</h2>
      <p class="sum-sub">Your complete syllabus practice session is ready.</p>

      <div class="sum-stats">
        <div class="sum-stat">
          <span class="sum-stat-label">Subject</span>
          <span class="sum-stat-val">{{ store.subject?.label }}</span>
        </div>
        <div class="sum-stat">
          <span class="sum-stat-label">Scope</span>
          <span class="sum-stat-val">Complete Syllabus</span>
        </div>
        <div class="sum-stat">
          <span class="sum-stat-label">Questions</span>
          <span class="sum-stat-val">{{ questionCount }}</span>
        </div>
        <div class="sum-stat">
          <span class="sum-stat-label">Mode</span>
          <span class="sum-stat-val">Practice Mode</span>
        </div>
      </div>

      <div class="sum-footer">
        <button class="back-btn" @click="router.push({ name: 'practice-scope' })">&larr; Back</button>
        <button class="start-btn" @click="startTest">Start Practice &rarr;</button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/axiosInstance'
import { usePracticeTestStore } from '@/stores/practiceTest'

const router    = useRouter()
const store     = usePracticeTestStore()
const preparing = ref(true)
const error     = ref('')
const dot       = ref(0)
const questionCount = ref(0)

let dotInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (!store.subject) { router.replace({ name: 'practice-subject' }); return }
  prepare()
  dotInterval = setInterval(() => { dot.value = (dot.value % 3) + 1 }, 600)
})

onUnmounted(() => { if (dotInterval) clearInterval(dotInterval) })

async function prepare(): Promise<void> {
  preparing.value = true
  error.value     = ''
  try {
    // Fetch a preview count of available questions for this subject
    const res = await api.get('/questions/', {
      params: {
        subject_id: store.subject?.id,
        scope:      'full',
        mode:       'practice',
        count_only: true,           // backend returns { count: N }
      }
    })
    questionCount.value = res.data.count ?? res.data.questions?.length ?? 10
    preparing.value = false
  } catch {
    // Fallback — just proceed with default count
    questionCount.value = 10
    preparing.value = false
  }
}

function startTest(): void {
  // Mark scope as full syllabus so TestAttemptView knows to fetch by subject_id
  store.setScope('full')
  store.setMode('practice')
  router.push({ name: 'practice-test' })
}
</script>

<style scoped>
.prep-page {
  max-width: 560px;
  margin: 60px auto 0;
  padding: 0 16px;
  display: flex;
  justify-content: center;
}

/* ── Preparing state ─────────────────────────────────────────────── */
.prep-box {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.prep-illustration {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.prep-icon {
  font-size: 44px;
  z-index: 2;
  position: relative;
}

.prep-rings { position: absolute; inset: 0; }
.ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid #7c3aed;
  opacity: 0;
  animation: ripple 1.8s ease-out infinite;
}
.ring1 { inset: 20px; animation-delay: 0s; }
.ring2 { inset: 8px;  animation-delay: 0.6s; }
.ring3 { inset: -4px; animation-delay: 1.2s; }

@keyframes ripple {
  0%   { transform: scale(0.8); opacity: 0.6; }
  100% { transform: scale(1.2); opacity: 0; }
}

.prep-title { font-size: 18px; font-weight: 800; color: #1e2536; margin: 0; }
.prep-sub   { font-size: 13px; color: #6b7280; margin: 0; line-height: 1.6; }

.dots { display: flex; gap: 8px; }
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #e5e7eb; transition: background 0.3s;
}
.dot.active { background: #7c3aed; }

.prep-error { color: #ef4444; font-size: 13px; }
.retry-btn {
  margin-left: 8px; background: none; border: 1px solid #ef4444;
  color: #ef4444; border-radius: 6px; padding: 4px 10px; cursor: pointer;user-select: none; font-size: 12px;
}

/* ── Summary / Ready state ───────────────────────────────────────── */
.summary-box {
  width: 100%;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.sum-icon  { font-size: 48px; }
.sum-title { font-size: 20px; font-weight: 800; color: #1e2536; margin: 0; }
.sum-sub   { font-size: 13px; color: #6b7280; margin: 0; }

.sum-stats {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 8px 0;
}

.sum-stat {
  background: #f9fafb;
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}
.sum-stat-label { font-size: 11px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.sum-stat-val   { font-size: 14px; font-weight: 700; color: #1e2536; }

.sum-footer {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 8px;
}

.back-btn {
  background: #fff; border: 1px solid #e5e7eb; color: #1e2536;
  font-weight: 600; font-size: 13px; padding: 10px 18px; border-radius: 9px; cursor: pointer;
  user-select: none;
}
.start-btn {
  background: #7c3aed; border: none; color: #fff;
  font-weight: 700; font-size: 13px; padding: 10px 22px; border-radius: 9px; cursor: pointer;
  user-select: none;
}
</style>