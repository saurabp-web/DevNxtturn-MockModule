<template>
  <div class="wizard-panel">
    <h2 class="panel-title">3. Syllabus Structure</h2>
    <p class="panel-sub">Add subjects and build the syllabus hierarchy.</p>

    <div class="syllabus-grid">
      <!-- Left: subjects already added to this exam -->
      <div class="subject-list">
        <button
          v-for="(s, i) in form.syllabus"
          :key="s.subjectId"
          class="subject-item"
          :class="{ active: activeSubject === i }"
          @click="activeSubject = i"
        >
          <span class="dot" />
          {{ s.subjectName }}
        </button>

        <!-- FIXED: subjects used to be created client-side as a hardcoded
             "New Subject" placeholder. They now come from the backend
             (Subjects master list) — clicking opens a picker of subjects
             not already added, instead of inventing one locally. -->
        <div class="add-subject-wrap">
          <button class="btn btn-ghost add-subject-btn" @click="showSubjectPicker = !showSubjectPicker">
            + Add Subject
          </button>
          <div v-if="showSubjectPicker" class="picker-dropdown">
            <p v-if="loadingSubjects" class="picker-empty">Loading subjects…</p>
            <p v-else-if="!availableSubjects.length" class="picker-empty">
              {{ subjectOptions.length ? 'All subjects added.' : 'No subjects found. Add one under Syllabus → Subjects first.' }}
            </p>
            <button
              v-for="subj in availableSubjects"
              :key="subj.id"
              class="picker-option"
              @click="pickSubject(subj)"
            >
              {{ subj.name }}
            </button>
          </div>
        </div>
        <p v-if="loadError" class="load-error-text">{{ loadError }}</p>
      </div>

      <!-- Right: chapter/topic tree for the selected subject -->
      <div class="chapter-tree">
        <div class="tree-head">
          <p class="tree-title">{{ currentSubject?.subjectName || 'Select a subject' }}</p>
          <div class="tree-head-actions">
            <button class="btn btn-ghost sm" :disabled="!currentSubject" @click="showChapterPicker = !showChapterPicker">
              + Add Chapter
            </button>
          </div>
        </div>

        <!-- FIXED: "Add Chapter" used to push a hardcoded "New Chapter"
             string per click. It's now a dropdown of chapters fetched
             from the backend for the current subject, with a checkbox
             per chapter so several can be selected and added at once. -->
        <div v-if="showChapterPicker" class="chapter-picker">
          <p v-if="loadingChapters" class="picker-empty">Loading chapters…</p>
          <p v-else-if="!availableChapters.length" class="picker-empty">
            No more chapters available for {{ currentSubject?.subjectName }}.
          </p>
          <label v-for="ch in availableChapters" :key="ch.id" class="chapter-checkbox-row">
            <input type="checkbox" :value="ch.id" v-model="checkedChapterIds" />
            {{ ch.name }}
          </label>
          <div class="chapter-picker-actions">
            <button class="btn btn-ghost sm" @click="closeChapterPicker">Cancel</button>
            <button class="btn btn-primary sm" :disabled="!checkedChapterIds.length" @click="applyChapterSelection">
              Add {{ checkedChapterIds.length || '' }} Chapter{{ checkedChapterIds.length === 1 ? '' : 's' }}
            </button>
          </div>
        </div>

        <div v-for="(ch, ci) in currentSubject?.chapters" :key="ch.chapterId" class="chapter-node">
          <div class="chapter-row">
            <span class="chapter-index">{{ ci + 1 }}.</span>
            <span class="chapter-name">{{ ch.name }}</span>
            <span class="node-actions">
              <button class="icon-btn danger" @click="removeChapter(ci)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
              </button>
            </span>
          </div>
          <div v-for="topic in ch.topics" :key="topic" class="topic-row">
            <span class="topic-name">{{ topic }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="panel-actions">
      <button class="btn btn-ghost" @click="$emit('back')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
        Back
      </button>
      <button class="btn btn-primary" @click="$emit('next')">
        Next
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { fetchSubjects, fetchChapters, type Option } from '@/services/filtersApi'

const props = defineProps<{ form: any }>()
defineEmits(['next', 'back'])

const activeSubject = ref(0)
const currentSubject = computed(() => props.form.syllabus[activeSubject.value])

// ── Subjects (backend-driven) ──────────────────────────────
const subjectOptions = ref<Option[]>([])
const loadingSubjects = ref(false)
const showSubjectPicker = ref(false)
const loadError = ref('')

const availableSubjects = computed(() => {
  const usedIds = new Set(props.form.syllabus.map((s: any) => s.subjectId))
  return subjectOptions.value.filter((s) => !usedIds.has(s.id))
})

function pickSubject(subj: Option) {
  props.form.syllabus.push({ subjectId: subj.id, subjectName: subj.name, chapters: [] })
  activeSubject.value = props.form.syllabus.length - 1
  showSubjectPicker.value = false
}

// ── Chapters (backend-driven, multi-select checkboxes) ─────
const chapterOptions = ref<Option[]>([])
const loadingChapters = ref(false)
const showChapterPicker = ref(false)
const checkedChapterIds = ref<(number | string)[]>([])

const availableChapters = computed(() => {
  const usedIds = new Set((currentSubject.value?.chapters || []).map((c: any) => c.chapterId))
  return chapterOptions.value.filter((c) => !usedIds.has(c.id))
})

async function loadChaptersForCurrentSubject() {
  if (!currentSubject.value) {
    chapterOptions.value = []
    return
  }
  loadingChapters.value = true
  try {
    chapterOptions.value = await fetchChapters(currentSubject.value.subjectId)
  } catch (err: any) {
    loadError.value = err.message || 'Failed to load chapters.'
  } finally {
    loadingChapters.value = false
  }
}

function closeChapterPicker() {
  showChapterPicker.value = false
  checkedChapterIds.value = []
}

function applyChapterSelection() {
  const picked = chapterOptions.value.filter((c) => checkedChapterIds.value.includes(c.id))
  for (const c of picked) {
    currentSubject.value.chapters.push({ chapterId: c.id, name: c.name, topics: [] })
  }
  closeChapterPicker()
}

function removeChapter(ci: number) {
  currentSubject.value?.chapters.splice(ci, 1)
}

// Reload the chapter list whenever the picker opens or the active
// subject changes, so it always reflects the currently selected subject.
watch(showChapterPicker, (open) => {
  if (open) loadChaptersForCurrentSubject()
})
watch(activeSubject, () => {
  checkedChapterIds.value = []
  if (showChapterPicker.value) loadChaptersForCurrentSubject()
})

onMounted(async () => {
  // FIXED: fetchSubjects requires an exam_id — subjects belong to an
  // existing Exam row on the backend, not a global catalog. This reads
  // form.examId, set once CreateExamView creates/saves a draft exam.
  // If form.examId isn't populated yet at this step, this call will
  // fail — see the note in filtersApi.ts.
  if (!props.form.examId) {
    loadError.value = 'This exam has not been saved yet, so subjects cannot be loaded.'
    loadingSubjects.value = false
    return
  }
  loadingSubjects.value = true
  try {
    subjectOptions.value = await fetchSubjects(props.form.examId)
  } catch (err: any) {
    loadError.value = err.message || 'Failed to load subjects.'
  } finally {
    loadingSubjects.value = false
  }
})
</script>

<style scoped>
@import './wizard-panel.css';
.panel-sub { font-size: 12px; color: #9CA3AF; margin: -14px 0 18px; }

.syllabus-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
}

.subject-list { display: flex; flex-direction: column; gap: 6px; position: relative; }
.subject-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: none;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  text-align: left;
}
.subject-item.active { background: #F5F3FF; color: #7C3AED; font-weight: 600; }
.subject-item:hover:not(.active) { background: #F9FAFB; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #A78BFA; flex-shrink: 0; }

.add-subject-wrap { position: relative; margin-top: 8px; }
.add-subject-btn { width: 100%; justify-content: center; }

.picker-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 6px;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  z-index: 10;
  max-height: 220px;
  overflow-y: auto;
  padding: 6px;
}
.picker-option {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border-radius: 6px;
  background: none;
  border: none;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
}
.picker-option:hover { background: #F5F3FF; color: #7C3AED; }
.picker-empty { font-size: 12px; color: #9CA3AF; padding: 8px 10px; margin: 0; }
.load-error-text { font-size: 12px; color: #DC2626; margin-top: 8px; }

.chapter-tree {
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 16px;
  position: relative;
}
.tree-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.tree-title { font-size: 14px; font-weight: 700; color: #111827; margin: 0; }
.tree-head-actions { display: flex; gap: 8px; }
.btn.sm { padding: 6px 12px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.chapter-picker {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 14px;
  background: #FAFAFF;
}
.chapter-checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #374151;
  padding: 6px 4px;
  cursor: pointer;
}
.chapter-picker-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #E5E7EB;
}

.chapter-node { margin-bottom: 10px; }
.chapter-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  padding: 6px 4px;
}
.chapter-index { color: #9CA3AF; }
.chapter-name { flex: 1; }
.node-actions { display: flex; gap: 4px; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 3px; border-radius: 5px; display: flex; }
.icon-btn:hover { background: #F3F4F6; }
.icon-btn.danger:hover { background: #FEF2F2; }

.topic-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #6B7280;
  padding: 5px 4px 5px 22px;
}
</style>