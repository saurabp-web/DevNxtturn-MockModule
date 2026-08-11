<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Practice Test', to: { name: 'practice-start' } },
        { label: 'Select Subject', to: { name: 'practice-subject' } },
        { label: 'Choose Chapter' },
      ]"
      :active-index="2"
    />

    <div class="pt-title-wrap">
      <h2 class="pt-title">Select Chapter</h2>
      <div class="pt-title-bar"></div>
    </div>
    <p class="pt-subtitle">Choose a chapter to start your practice test</p>

    <!-- TEMPORARY DEBUG — remove once we've confirmed testType is propagating correctly -->
    <!-- <p style="background:#fee2e2;color:#991b1b;font-weight:800;padding:8px 12px;border-radius:8px;display:inline-block;margin-bottom:12px;">
      DEBUG — store.testType = "{{ store.testType }}" | store.mode = "{{ store.mode }}" | store.customConfig = {{ store.customConfig ? 'SET' : 'null' }}
    </p> -->

    <div v-if="loading" class="center-box">
      <div class="spinner"></div>
      <p>Loading chapters…</p>
    </div>

    <div v-else-if="loadError" class="center-box error-box">
      <p>{{ loadError }}</p>
      <button class="btn-primary" @click="loadChapters">Retry</button>
    </div>

    <div v-else class="chapter-layout">
      <div class="chapter-list-card">
        <div class="clc-header">
          <span>{{ store.subject?.label }} Chapters</span>
        </div>

        <div v-if="chapters.length === 0" class="empty-msg">No chapters found for this subject yet.</div>

        <div
          v-for="(chapter, index) in chapters"
          :key="chapter.id"
          class="chapter-row"
          :class="{ selected: store.chapter?.id === chapter.id }"
          @click="store.setChapter(chapter)"
        >
          <div class="chapter-row-left">
            <span class="chapter-name">{{ chapter.label }}</span>
          </div>
          <div class="chapter-row-right">
            <span class="chapter-count">({{ chapter.questionCount }})</span>
            <span class="chapter-chevron">›</span>
          </div>
          <div v-if="index < chapters.length - 1" class="chapter-divider"></div>
        </div>

        <div class="total-row">Total Chapters: {{ chapters.length }}</div>
      </div>

      <div class="chapter-details-card">
        <span class="cdc-label">Chapter Details</span>
        <template v-if="store.chapter">
          <h4>{{ store.chapter.label }}</h4>
          <p>This chapter covers key topics relevant to {{ store.chapter?.label }} in {{ store.subject?.label }}.</p>
          <div class="cdc-stats">
            <div class="cdc-stat">
              <strong>{{ store.chapter.questionCount }}</strong>
              <span>Questions Available</span>
            </div>
          </div>
        </template>
        <div v-else class="cdc-empty-state">
          <div class="cdc-book-wrap">
            <span class="cdc-book-icon">📖</span>
          </div>
          <h4 class="cdc-empty-title">Select a chapter</h4>
          <p class="cdc-empty-sub">Choose a chapter from the list to see its details, topics covered, and question overview.</p>
        </div>
      </div>
    </div>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'practice-subject' })">&larr; Back</button>
      <button class="continue-btn" :disabled="!store.chapter" @click="goNext">
        Start Practice &rarr;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import api from '@/services/axiosInstance'
import { usePracticeTestStore, type PracticeChapter } from '../../stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

onMounted(() => {
  if (!store.subject) { router.replace({ name: 'practice-subject' }); return }
  loadChapters()
})

const chapters   = ref<PracticeChapter[]>([])
const loading    = ref(true)
const loadError  = ref('')

async function loadChapters(): Promise<void> {
  const subjectId = store.subject?.id
  if (!subjectId) return

  loading.value = true
  loadError.value = ''
  try {
    const res = await api.get('/chapters/', { params: { subject_id: subjectId } })
    const raw: { id: number; label: string; question_count: number }[] = res.data.chapters

    // Defensive de-dupe by chapter name within this subject (mirrors the
    // same safeguard on the Select Subject screen) — should be a no-op if
    // the backend data is clean, but prevents duplicate rows in the list
    // if a chapter ever gets created twice for the same subject.
    const seen = new Set<string>()
    const deduped = raw.filter((c) => {
      const key = c.label.trim().toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })

    chapters.value = deduped.map((c) => ({
      id: String(c.id),
      label: c.label,
      questionCount: c.question_count,
    }))
  } catch {
    loadError.value = 'Failed to load chapters. Please try again.'
  } finally {
    loading.value = false
  }
}

function goNext(): void {
  if (!store.chapter) return
  store.setMode('practice')
  router.push({ name: 'practice-test' })
}
</script>

<style scoped>
.pt-page { max-width: 980px; margin: 0 auto; }

/* Title with purple underline */
.pt-title-wrap { margin-bottom: 4px; display: inline-block; }
.pt-title { font-size: 22px; font-weight: 800; color: #1e2536; margin: 0; }
.pt-title-bar { height: 3px; width: 48px; background: #7c3aed; border-radius: 2px; margin-top: 6px; }

.pt-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 20px; }

.center-box {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 200px; gap: 14px; color: #6b7280;
}
.error-box { color: #ef4444; }
.spinner {
  width: 36px; height: 36px; border: 4px solid #e5e7eb;
  border-top-color: #7c3aed; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.btn-primary {
  background: #7c3aed; color: #fff; border: none; font-weight: 700;
  font-size: 13px; padding: 9px 18px; border-radius: 8px; cursor: pointer;
  user-select: none;
}

.empty-msg { font-size: 13px; color: #9ca3af; padding: 10px 0; }

.chapter-layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
  align-items: start;
}
@media (max-width: 760px) { .chapter-layout { grid-template-columns: 1fr; } }

/* Left panel */
.chapter-list-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px;
  max-height: 520px;
  overflow-y: auto;
}

.clc-header {
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.chapter-row {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 6px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
  border-radius: 6px;
}
.chapter-row:hover { background: #f9fafb; }
.chapter-row.selected { background: #f5f3ff; }
.chapter-row.selected .chapter-name { color: #7c3aed; font-weight: 700; }
.chapter-row.selected .chapter-chevron { color: #7c3aed; }

.chapter-row-left { flex: 1; min-width: 0; }
.chapter-row-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.chapter-name { font-size: 13px; color: #374151; }
.chapter-count { font-size: 12px; color: #9ca3af; }
.chapter-chevron { font-size: 18px; color: #9ca3af; line-height: 1; }

.chapter-divider {
  position: absolute;
  bottom: 0; left: 6px; right: 6px;
  height: 1px; background: #f3f4f6;
}

.total-row {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
  font-size: 12px;
  font-weight: 700;
  color: #6b7280;
}

/* Right panel */
.chapter-details-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px;
  min-height: 300px;
}

.cdc-label {
  font-size: 14px;
  font-weight: 700;
  color: #1e2536;
  display: block;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.chapter-details-card h4 {
  font-size: 15px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 8px;
}

.chapter-details-card > template > p {
  font-size: 12.5px;
  color: #6b7280;
  margin: 0 0 16px;
  line-height: 1.5;
}

.cdc-stats { display: grid; grid-template-columns: 1fr; gap: 12px; }
.cdc-stat {
  background: #f9fafb; border-radius: 10px;
  padding: 12px; text-align: center;
}
.cdc-stat strong { display: block; font-size: 18px; font-weight: 800; color: #7c3aed; }
.cdc-stat span   { font-size: 11px; color: #6b7280; }

/* Empty state in right panel */
.cdc-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 30px 16px;
  gap: 12px;
}

.cdc-book-wrap {
  width: 80px; height: 80px; border-radius: 50%;
  background: #ede9fe;
  display: flex; align-items: center; justify-content: center;
  font-size: 36px;
  margin-bottom: 4px;
}

.cdc-empty-title {
  font-size: 16px; font-weight: 700; color: #1e2536; margin: 0;
}

.cdc-empty-sub {
  font-size: 13px; color: #6b7280; margin: 0; line-height: 1.6;
  max-width: 240px;
}

/* Footer */
.pt-footer { display: flex; justify-content: space-between; align-items: center; }
.back-btn {
  background: #fff; border: 1px solid #e5e7eb; color: #1e2536;
  font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
.continue-btn {
  background: #7c3aed; border: none; color: #fff;
  font-weight: 700; font-size: 13px; padding: 10px 20px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
.continue-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>