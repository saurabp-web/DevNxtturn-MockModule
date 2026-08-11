<template>
  <div class="test-row">
    <div class="test-logo-circle" :class="exam.logo ? '' : logoClass">
      <img
        v-if="exam.logo"
        :src="exam.logo"
        :alt="exam.exam_name"
        class="logo-img"
        @error="onImgError"
      />
      <template v-else>
        <span class="logo-mark">{{ logoEmoji }}</span>
        <span class="logo-label">{{ shortLabel }}</span>
      </template>
    </div>

    <div class="test-row-info">
      <h4 class="test-row-title">{{ exam.exam_name }}</h4>
      <div class="test-row-meta">
        Full Length Test
        <span v-if="exam.question_count"> &bull; {{ exam.question_count }} Questions</span>
        <span v-if="exam.duration_minutes"> &bull; {{ formattedDuration }}</span>
      </div>
      <div class="test-row-badges">
        <span class="badge" :class="difficultyClass">{{ difficultyLabel }}</span>
        <span class="badge badge-language">{{ languageLabel }}</span>
      </div>
    </div>

    <div class="test-row-actions">
      <button class="view-details-btn" @click="$emit('take', exam)">View Details</button>
      <button
        class="bookmark-btn"
        :class="{ saved: exam.is_bookmarked }"
        @click="$emit('bookmark', exam)"
        aria-label="Bookmark"
      >
        <svg viewBox="0 0 24 24" :fill="exam.is_bookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
          <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Exam } from '../../types/exam'

// logo may come from the scraped JSON via ExamView's ScrapedExam type
const props = defineProps<{ exam: Exam & { logo?: string | null } }>()

function onImgError(e: Event): void {
  // If the logo URL fails to load, hide the img so the fallback emoji shows
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
  const circle = img.parentElement
  if (circle) {
    circle.classList.add(logoClass.value)
    const mark = document.createElement('span')
    mark.className = 'logo-mark'
    mark.textContent = logoEmoji.value
    const label = document.createElement('span')
    label.className = 'logo-label'
    label.textContent = shortLabel.value
    circle.appendChild(mark)
    circle.appendChild(label)
  }
}

defineEmits<{
  (e: 'take', exam: Exam): void
  (e: 'bookmark', exam: Exam): void
}>()

const shortLabel = computed(() => (props.exam.exam_category || props.exam.conducting_body || 'EXAM').toUpperCase().slice(0, 6))
const logoEmoji = computed(() => '🏛️')

const logoClass = computed(() => {
  const cat = (props.exam.exam_category || '').toUpperCase()
  if (cat === 'SSC') return 'logo-ssc'
  if (cat === 'BANKING') return 'logo-banking'
  if (cat === 'RAILWAY') return 'logo-railway'
  if (cat === 'STATE_PSC') return 'logo-state'
  return 'logo-upsc'
})

const difficultyLabel = computed(() => {
  const d = props.exam.difficulty || 'medium'
  return d.charAt(0).toUpperCase() + d.slice(1)
})

const difficultyClass = computed(() => `badge-${props.exam.difficulty || 'medium'}`)

const languageLabel = computed(() => props.exam.language || 'English')

const formattedDuration = computed(() => {
  const mins = props.exam.duration_minutes || 0
  if (mins >= 60 && mins % 60 === 0) return `${mins / 60} Hours`
  return `${mins} Minutes`
})
</script>

<style scoped>
.test-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.test-logo-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #fafafa;
}

.logo-img {
  width: 52px;
  height: 52px;
  object-fit: contain;
  border-radius: 4px;
}

.logo-mark {
  font-size: 16px;
  line-height: 1;
}

.logo-label {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.3px;
  color: #4b5563;
  margin-top: 2px;
}

.logo-ssc .logo-label { color: #b91c1c; }
.logo-banking .logo-label { color: #1d4ed8; }
.logo-railway .logo-label { color: #047857; }
.logo-state .logo-label { color: #7c3aed; }

.test-row-info {
  flex: 1;
  min-width: 0;
}

.test-row-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 4px;
}

.test-row-meta {
  font-size: 12.5px;
  color: #6b7280;
  margin-bottom: 10px;
}

.test-row-badges {
  display: flex;
  gap: 8px;
}

.badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}

.badge-easy {
  background: #d1fae5;
  color: #047857;
}

.badge-medium {
  background: #fef3c7;
  color: #b45309;
}

.badge-hard {
  background: #fee2e2;
  color: #b91c1c;
}

.badge-language {
  background: #ede9fe;
  color: #6d28d9;
}

.test-row-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.view-details-btn {
  background: #fff;
  border: 1px solid #7c3aed;
  color: #7c3aed;
  font-weight: 700;
  font-size: 13px;
  padding: 9px 16px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
}

.view-details-btn:hover {
  background: #f5f3ff;
}

.bookmark-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.bookmark-btn svg {
  width: 16px;
  height: 16px;
}

.bookmark-btn.saved {
  color: #7c3aed;
  border-color: #c4b5fd;
}
</style>