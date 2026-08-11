<template>
  <div class="cct-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Practice Test', to: { name: 'practice-start' } },
        { label: 'Create Custom Test' },
      ]"
      :active-index="1"
    />

    <h2 class="cct-title">Create Custom Test</h2>
    <p class="cct-subtitle">Set your preferences and start a test tailored to your needs</p>

    <div class="cct-layout">
      <!-- Left: builder -->
      <div class="cct-builder">

        <!-- Step 1: Subjects & Chapters -->
        <section v-show="pageStep === 1" class="cct-step cct-step--plain">
          <div v-if="loadingSubjects" class="inline-loading">Loading subjects…</div>
          <div v-else-if="subjectError" class="inline-error">
            {{ subjectError }}
          </div>

          <div v-else class="subj-body">
            <!-- Mode toggle -->
            <div class="mode-grid">
              <button
                type="button"
                class="mode-card"
                :class="{ selected: subjectMode === 'all' }"
                @click="setSubjectMode('all')"
              >
                <span class="mode-radio" :class="{ checked: subjectMode === 'all' }"></span>
                <span class="mode-text">
                  <strong>All Subjects</strong>
                  <small>Include all available subjects in the test</small>
                </span>
              </button>

              <button
                type="button"
                class="mode-card"
                :class="{ selected: subjectMode === 'select' }"
                @click="setSubjectMode('select')"
              >
                <span class="mode-radio" :class="{ checked: subjectMode === 'select' }"></span>
                <span class="mode-text">
                  <strong>Select Subjects</strong>
                  <small>Choose specific subjects for your test</small>
                </span>
              </button>
            </div>

            <div v-if="subjectMode === 'all'" class="all-subjects-note">
              &#9989; All subjects and chapters are included by default. Uncheck any chapter below to leave it out.
            </div>

            <template v-if="subjectMode === 'select'">
              <!-- Subject multi-select -->
              <div class="field-block">
                <label class="field-label">Select Subjects <span class="req">*</span></label>
                <div class="ms-box" @click="showSubjectDropdown = !showSubjectDropdown">
                  <span v-if="!selectedSubjectsList.length" class="ms-placeholder">Choose subjects…</span>
                  <span v-for="s in selectedSubjectsList" :key="s.id" class="ms-tag">
                    <span class="ms-tag-icon" :class="s.colorClass">{{ s.icon }}</span>
                    {{ s.label }}
                    <button type="button" class="ms-tag-x" @click.stop="toggleSubject(s.id)">&times;</button>
                  </span>
                  <span class="ms-chevron" :class="{ open: showSubjectDropdown }">&#9660;</span>
                </div>

                <div v-if="showSubjectDropdown" class="ms-dropdown">
                  <button
                    v-for="s in subjects"
                    :key="s.id"
                    type="button"
                    class="ms-option"
                    :class="{ picked: selectedSubjectIds.has(s.id) }"
                    @click="toggleSubject(s.id)"
                  >
                    <span class="ms-tag-icon" :class="s.colorClass">{{ s.icon }}</span>
                    {{ s.label }}
                    <span v-if="selectedSubjectIds.has(s.id)" class="ms-check">&#10003;</span>
                  </button>
                </div>
              </div>
            </template>

            <!-- Chapters: all subjects in 'all' mode, chosen subjects in 'select' mode -->
            <div class="field-block" v-if="chaptersPanelSubjects.length">
              <label class="field-label">
                Select Chapters <span v-if="subjectMode === 'select'" class="req">*</span>
              </label>
              <p class="field-hint">
                {{ subjectMode === 'all'
                  ? 'Every chapter is checked by default — uncheck any you want to leave out.'
                  : 'Choose chapters from the selected subjects' }}
              </p>

              <div class="chapters-panel">
                <div
                  v-for="s in chaptersPanelSubjects"
                  :key="s.id"
                  class="chap-subject"
                  :class="{ open: expandedSubjects.has(s.id) }"
                >
                  <button type="button" class="chap-subject-head" @click="toggleExpand(s.id)">
                    <span class="chip-icon" :class="s.colorClass">{{ s.icon }}</span>
                    <span class="chap-subject-name">{{ s.label }}</span>
                    <span class="chap-count-pill">{{ selectedChapterCount(s.id) }} Selected</span>
                    <span class="chap-chevron" :class="{ open: expandedSubjects.has(s.id) }">&#9660;</span>
                  </button>

                  <div v-if="expandedSubjects.has(s.id)" class="chap-subject-body">
                    <div class="chap-search">
                      <input type="text" v-model="chapterFilters[s.id]" placeholder="Select chapters" />
                      <span class="chap-search-chevron">&#9660;</span>
                    </div>

                    <div v-if="loadingChapters[s.id]" class="inline-loading small">Loading chapters…</div>
                    <div v-else-if="chapterErrors[s.id]" class="inline-error small">{{ chapterErrors[s.id] }}</div>
                    <template v-else>
                      <label v-if="filteredChapters(s.id).length" class="chap-item chap-select-all">
                        <input
                          type="checkbox"
                          :checked="areAllChaptersSelected(s.id)"
                          :indeterminate.prop="isChapterSelectionIndeterminate(s.id)"
                          @change="toggleSelectAllChapters(s.id)"
                        />
                        <span>Select All</span>
                      </label>
                      <ul class="chap-list">
                        <li v-for="c in filteredChapters(s.id)" :key="c.id">
                          <label class="chap-item">
                            <input
                              type="checkbox"
                              :checked="isChapterSelected(s.id, c.id)"
                              @change="toggleChapter(s.id, c.id)"
                            />
                            <span>{{ c.orderLabel }}. {{ c.label }}</span>
                          </label>
                        </li>
                        <li v-if="!filteredChapters(s.id).length" class="chap-empty">No chapters found.</li>
                      </ul>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Page 2 -->
        <template v-if="pageStep === 2">
        <!-- Step 1: Marks & Questions -->
        <section class="cct-step">
          <div class="step-head">
            <span class="step-num">1</span>
            <div>
              <h3>Set Marks &amp; Questions</h3>
              <p>Configure marks and number of questions</p>
            </div>
          </div>

          <div class="mq-grid">
            <div class="mq-field">
              <label>Number of Questions</label>
              <div class="stepper">
                <button @click="adjustQuestions(-5)">&minus;</button>
                <span>{{ numQuestions ?? '—' }}</span>
                <button @click="adjustQuestions(5)">+</button>
              </div>
            </div>

            <div class="mq-field">
              <label>Marks per Question</label>
              <div class="stepper">
                <button @click="adjustMarksPerQuestion(-1)">&minus;</button>
                <span>{{ marksPerQuestion ?? '—' }}</span>
                <button @click="adjustMarksPerQuestion(1)">+</button>
              </div>
            </div>

            <div class="mq-field">
              <label>Total Marks</label>
              <div class="stepper">
                <button @click="adjustTotalMarks(-(marksPerQuestion ?? 1))">&minus;</button>
                <span>{{ totalMarks ?? '—' }}</span>
                <button @click="adjustTotalMarks(marksPerQuestion ?? 1)">+</button>
              </div>
            </div>
          </div>

          <div class="formula-note">
            &#8505; Total Marks = Number of Questions &times; Marks per Question
          </div>

          <div class="neg-mark-row">
            <div class="neg-mark-text">
              <strong>Negative Marking</strong>
              <small>Deduct marks for incorrect answers</small>
            </div>

            <div class="neg-mark-controls">
              <div v-if="negativeMarking" class="stepper stepper--compact">
                <button @click="adjustNegativeMarks(-1)">&minus;</button>
                <span>{{ negativeMarksPerQuestion ?? '—' }}</span>
                <button @click="adjustNegativeMarks(1)">+</button>
              </div>

              <button
                type="button"
                class="toggle-switch"
                :class="{ on: negativeMarking }"
                role="switch"
                :aria-checked="negativeMarking"
                @click="negativeMarking = !negativeMarking"
              >
                <span class="toggle-knob"></span>
              </button>
            </div>
          </div>
        </section>

        <!-- Step 2: Difficulty -->
        <section class="cct-step">
          <div class="step-head">
            <span class="step-num">2</span>
            <div>
              <h3>Select Difficulty Level</h3>
              <p>Choose the difficulty level of questions</p>
            </div>
          </div>

          <div class="difficulty-grid">
            <button
              v-for="opt in difficultyOptions"
              :key="opt.value"
              class="difficulty-chip"
              :class="[opt.value, { selected: difficulty === opt.value }]"
              @click="difficulty = opt.value"
            >
              <span>{{ opt.icon }}</span> {{ opt.label }}
              <span v-if="difficulty === opt.value" class="check-badge">&#10003;</span>
            </button>
          </div>
        </section>

        <!-- Step 3: Duration -->
        <section class="cct-step">
          <div class="step-head">
            <span class="step-num">3</span>
            <div>
              <h3>Select Duration</h3>
              <p>Set the total time for your test</p>
            </div>
          </div>

          <div class="duration-grid">
            <button
              v-for="d in durationPresets"
              :key="d"
              class="duration-chip"
              :class="{ selected: !customDurationMode && duration === d }"
              @click="pickDuration(d)"
            >
              <span class="clock-icon">&#128337;</span> {{ d }} mins
              <span v-if="!customDurationMode && duration === d" class="check-badge">&#10003;</span>
            </button>

            <button
              class="duration-chip custom-chip"
              :class="{ selected: customDurationMode }"
              @click="customDurationMode = true"
            >
              <span class="pencil-icon">&#9998;</span> Custom
            </button>
          </div>

          <div v-if="customDurationMode" class="custom-duration-input">
            <input
              type="number"
              min="5"
              step="5"
              v-model.number="duration"
              placeholder="Enter minutes"
            />
            <span>mins</span>
          </div>
        </section>
        </template>
      </div>

      <!-- Right: summary -->
      <aside class="cct-summary">
        <template v-if="pageStep === 1">
        <div class="crit-card">
          <div class="summary-head">
            <span class="summary-icon">&#128203;</span>
            <h3>Selected Chapters Criteria</h3>
          </div>

          <template v-if="subjectsWithSelections.length">
            <div class="crit-stats">
              <div class="crit-stat">
                <span>Total Subjects</span>
                <strong>{{ subjectsWithSelections.length }}</strong>
              </div>
              <div class="crit-stat">
                <span>Total Chapters</span>
                <strong>{{ totalSelectedChaptersAll }}</strong>
              </div>
            </div>

            <div class="crit-summary-title">Selection Summary</div>

            <div v-for="s in subjectsWithSelections" :key="s.id" class="crit-subject-card">
              <div class="crit-subject-head">
                <span class="chip-icon" :class="s.colorClass">{{ s.icon }}</span>
                <strong>{{ s.label }}</strong>
                <span class="crit-count-pill">{{ selectedChapterCount(s.id) }} Chapters</span>
              </div>
              <ul class="crit-chapter-list">
                <li v-for="c in selectedChaptersFor(s.id)" :key="c.id">{{ c.orderLabel }}. {{ c.label }}</li>
              </ul>
              <button type="button" class="crit-remove" @click="removeSubjectSelection(s.id)">Remove</button>
            </div>

            <div class="crit-total-box">
              <div>
                <span>Total Chapters</span>
                <strong>{{ totalSelectedChaptersAll }}</strong>
              </div>
              <div>
                <span>Total Marks (To be set)</span>
                <strong>{{ totalMarks ?? '--' }}</strong>
              </div>
            </div>

            <div class="crit-info-note">
              &#8505;&#65039; You can review your selections or remove any chapter before proceeding.
            </div>
          </template>

          <div v-else class="all-subjects-note">
            {{ subjectMode === 'all'
              ? '✅ All subjects and all chapters will be included in this test.'
              : 'Tick chapters above to build your selection.' }}
          </div>
        </div>
        </template>

        <template v-if="pageStep === 2">
        <div class="summary-head">
          <span class="summary-icon">&#128203;</span>
          <h3>Test Summary</h3>
        </div>

        <div v-if="!canStart" class="summary-pending">
          Complete all the steps on the left to see your test summary.
        </div>

        <template v-else>
          <div class="summary-row">
            <span>&#128193; Subjects</span>
            <strong>{{ subjectSummaryLabel }}</strong>
          </div>
          <div class="summary-row">
            <span>&#128337; Duration</span>
            <strong>{{ duration }} mins</strong>
          </div>
          <div class="summary-row">
            <span>&#9878;&#65039; Difficulty Level</span>
            <strong class="cap">{{ difficulty }}</strong>
          </div>
          <div class="summary-row"><span>&#128203; Number of Questions</span><strong>{{ numQuestions }}</strong></div>
          <div class="summary-row"><span>&#9999;&#65039; Marks per Question</span><strong>{{ marksPerQuestion }}</strong></div>
          <div class="summary-row"><span>&#128221; Total Marks</span><strong>{{ totalMarks }}</strong></div>
          <div class="summary-row">
            <span>&#10071; Negative Marking</span>
            <strong v-if="negativeMarking">Yes (&minus;{{ negativeMarksPerQuestion }} / wrong)</strong>
            <strong v-else class="unset">Disabled</strong>
          </div>
        </template>

        <div class="notes-box">
          <div class="notes-head"><span>&#8505;&#65039;</span> Important Notes</div>
          <ul>
            <li>Once the test is started, the timer will begin.</li>
            <li>You cannot pause or reset the test.</li>
            <li>Make sure you have a stable internet connection.</li>
            <li>All the best!</li>
          </ul>
        </div>
        </template>
      </aside>
    </div>

    <div class="cct-footer">
      <button
        class="back-btn"
        @click="pageStep === 1 ? router.push({ name: 'practice-start' }) : (pageStep = 1)"
      >
        &larr; Back
      </button>

      <button
        v-if="pageStep === 1"
        class="start-btn"
        :disabled="!canProceedStep1"
        @click="pageStep = 2"
      >
        Continue to Next &rarr;
      </button>
      <button
        v-else
        class="start-btn"
        :disabled="!canStart"
        @click="openModeModal"
      >
        Start Test &rarr;
      </button>
    </div>

    <!-- Test Mode / Practice Mode picker -->
    <div v-if="showModeModal" class="modal-overlay" @click.self="closeModeModal">
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <h3>Choose How to Start</h3>
            <p class="modal-subtitle">Pick the mode you'd like to attempt this test in</p>
          </div>
          <button type="button" class="modal-close" @click="closeModeModal">&times;</button>
        </div>

        <div class="mode-modal-grid">
          <button type="button" class="mode-modal-card mode-modal-card--test" @click="confirmStartTest('test')">
            <span class="mode-modal-badge">Exam-like</span>
            <span class="mode-modal-icon">&#9203;</span>
            <strong>Test Mode</strong>
            <small>Timed and continuous, just like the real exam. Results are shown only at the end.</small>
            <span class="mode-modal-cta">Start in Test Mode &rarr;</span>
          </button>

          <button type="button" class="mode-modal-card mode-modal-card--practice" @click="confirmStartTest('practice')">
            <span class="mode-modal-badge">Learn as you go</span>
            <span class="mode-modal-icon">&#128161;</span>
            <strong>Practice Mode</strong>
            <small>Check each answer and its explanation right after you attempt it.</small>
            <span class="mode-modal-cta">Start in Practice Mode &rarr;</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '../../components/practice/PracticeBreadcrumb.vue'
import api from '@/services/axiosInstance'
import { usePracticeTestStore } from '../../stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

// ── Wizard step (1 = Subjects & Chapters, 2 = Duration/Difficulty/Marks) ──
const pageStep = ref<1 | 2>(1)

// ── Subjects ───────────────────────────────────────────────────────
interface DisplaySubject { id: string; label: string; icon: string; colorClass: string }

const ICON_MAP: Record<string, { icon: string; colorClass: string }> = {
  'physics':     { icon: '⚡', colorClass: 'c-blue' },
  'chemistry':   { icon: '🧪', colorClass: 'c-green' },
  'mathematics': { icon: '📐', colorClass: 'c-purple' },
  'biology':     { icon: '🧬', colorClass: 'c-pink' },
}
const DEFAULT_ICON = { icon: '📘', colorClass: 'c-indigo' }

const subjects          = ref<DisplaySubject[]>([])
const loadingSubjects   = ref(true)
const subjectError      = ref('')
const selectedSubjectIds = ref<Set<string>>(new Set())

// 'all' = every subject/chapter included, 'select' = user picks specific subjects+chapters
type SubjectMode = 'all' | 'select'
const subjectMode        = ref<SubjectMode>('all')
const showSubjectDropdown = ref(false)

// ── Chapters ───────────────────────────────────────────────────────
interface ChapterOption { id: string; label: string; orderLabel: number }

const expandedSubjects  = ref<Set<string>>(new Set())
const chaptersBySubject = ref<Record<string, ChapterOption[]>>({})
const loadingChapters   = ref<Record<string, boolean>>({})
const chapterErrors     = ref<Record<string, string>>({})
const selectedChapterIds = ref<Record<string, Set<string>>>({})
const chapterFilters    = ref<Record<string, string>>({})

// NOTE: adjust this endpoint/response shape to match the real chapters API
// (mirrors the /subjects/ pattern above — swap in whatever your backend exposes).
async function loadChaptersFor(subjectId: string): Promise<void> {
  loadingChapters.value[subjectId] = true
  chapterErrors.value[subjectId] = ''
  try {
    const res = await api.get('/chapters/', { params: { subject_id: subjectId } })
    const list = (res.data.chapters ?? res.data) as Array<{ id: number | string; label: string; order?: number }>
    chaptersBySubject.value[subjectId] = list.map((c, idx) => ({
      id: String(c.id),
      label: c.label,
      orderLabel: c.order ?? idx + 1,
    }))
    // All-Subjects mode: every chapter starts checked — the candidate
    // unchecks the ones they want to exclude. Select-Subjects mode keeps
    // the opt-in default (nothing checked until picked).
    if (subjectMode.value === 'all') {
      selectedChapterIds.value[subjectId] = new Set(chaptersBySubject.value[subjectId].map(c => c.id))
    }
  } catch (err: unknown) {
    const message = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
    chapterErrors.value[subjectId] = message
      ? `Couldn't load chapters: ${message}`
      : 'Failed to load chapters. Please try again.'
  } finally {
    loadingChapters.value[subjectId] = false
  }
}

// Fetches (and, per the rule above, fully-checks) chapters for every subject
// that hasn't been loaded yet — called on mount and whenever the candidate
// switches into All-Subjects mode, so counts/checkboxes are correct even
// before a subject's accordion is expanded.
function ensureAllChaptersLoaded(): void {
  subjects.value.forEach(s => {
    if (!chaptersBySubject.value[s.id] && !loadingChapters.value[s.id]) {
      loadChaptersFor(s.id)
    }
  })
}

function toggleExpand(subjectId: string): void {
  if (expandedSubjects.value.has(subjectId)) {
    expandedSubjects.value.delete(subjectId)
    return
  }
  expandedSubjects.value.add(subjectId)
  if (!chaptersBySubject.value[subjectId] && !loadingChapters.value[subjectId]) {
    loadChaptersFor(subjectId)
  }
}

function toggleChapter(subjectId: string, chapterId: string): void {
  if (!selectedChapterIds.value[subjectId]) {
    selectedChapterIds.value[subjectId] = new Set()
  }
  const set = selectedChapterIds.value[subjectId]
  if (set.has(chapterId)) set.delete(chapterId)
  else set.add(chapterId)
}

function isChapterSelected(subjectId: string, chapterId: string): boolean {
  return !!selectedChapterIds.value[subjectId]?.has(chapterId)
}

// "Select All" reflects/affects only the currently filtered (searched)
// chapters for that subject — so searching then hitting Select All only
// selects the visible matches, not the whole subject.
function areAllChaptersSelected(subjectId: string): boolean {
  const chapters = filteredChapters(subjectId)
  if (!chapters.length) return false
  return chapters.every(c => isChapterSelected(subjectId, c.id))
}

function isChapterSelectionIndeterminate(subjectId: string): boolean {
  const chapters = filteredChapters(subjectId)
  if (!chapters.length) return false
  const selectedCount = chapters.filter(c => isChapterSelected(subjectId, c.id)).length
  return selectedCount > 0 && selectedCount < chapters.length
}

function toggleSelectAllChapters(subjectId: string): void {
  if (!selectedChapterIds.value[subjectId]) {
    selectedChapterIds.value[subjectId] = new Set()
  }
  const set = selectedChapterIds.value[subjectId]
  const chapters = filteredChapters(subjectId)
  const allSelected = chapters.length > 0 && chapters.every(c => set.has(c.id))

  if (allSelected) {
    chapters.forEach(c => set.delete(c.id))
  } else {
    chapters.forEach(c => set.add(c.id))
  }
}

function selectedChapterCount(subjectId: string): number {
  return selectedChapterIds.value[subjectId]?.size ?? 0
}

function selectedChaptersFor(subjectId: string): ChapterOption[] {
  const chapters = chaptersBySubject.value[subjectId] ?? []
  return chapters.filter(c => isChapterSelected(subjectId, c.id))
}

function filteredChapters(subjectId: string): ChapterOption[] {
  const chapters = chaptersBySubject.value[subjectId] ?? []
  const q = (chapterFilters.value[subjectId] ?? '').trim().toLowerCase()
  if (!q) return chapters
  return chapters.filter(c => c.label.toLowerCase().includes(q))
}

const totalSelectedChapters = computed(() =>
  selectedSubjectsList.value.reduce((sum, s) => sum + selectedChapterCount(s.id), 0)
)

// Which subjects get a chapter accordion: every subject in 'all' mode,
// only the chosen ones in 'select' mode.
const chaptersPanelSubjects = computed(() =>
  subjectMode.value === 'all' ? subjects.value : selectedSubjectsList.value
)

// Chapter selections are tracked per subject regardless of mode, so the
// sidebar can reflect narrowing done while in 'All Subjects' mode too.
const totalSelectedChaptersAll = computed(() =>
  Object.values(selectedChapterIds.value).reduce((sum, set) => sum + set.size, 0)
)
const subjectsWithSelections = computed(() =>
  subjects.value.filter(s => selectedChapterCount(s.id) > 0)
)
function clearSubjectChapters(subjectId: string): void {
  delete selectedChapterIds.value[subjectId]
}

// Sidebar "Remove" link: in Select-Subjects mode this drops the subject
// entirely (chip bar + its chapter accordion both disappear, matching
// toggleSubject's cleanup). In All-Subjects mode there's no subject list
// to remove from, so it just clears that subject's chapter narrowing.
function removeSubjectSelection(subjectId: string): void {
  if (subjectMode.value === 'select') {
    if (selectedSubjectIds.value.has(subjectId)) toggleSubject(subjectId)
  } else {
    clearSubjectChapters(subjectId)
  }
}

async function loadSubjects(): Promise<void> {
  const params = subjectQueryParams()
  if (!params) {
    subjectError.value = 'No exam selected — please go back and pick an exam first.'
    loadingSubjects.value = false
    return
  }
  loadingSubjects.value = true
  subjectError.value = ''
  try {
    const res = await api.get('/subjects/', { params })
    subjects.value = res.data.subjects.map((s: { id: number; label: string }) => {
      const key = s.label.trim().toLowerCase()
      const style = ICON_MAP[key] ?? DEFAULT_ICON
      return { id: String(s.id), label: s.label, ...style }
    })
  } catch (err: unknown) {
    const message = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
    subjectError.value = message
      ? `Couldn't load subjects: ${message}`
      : 'Failed to load subjects. Please try again.'
  } finally {
    loadingSubjects.value = false
    if (subjectMode.value === 'all') ensureAllChaptersLoaded()
  }
}
onMounted(loadSubjects)

// Prefer a real numeric Exam PK (store.examType.id) when available;
// otherwise fall back to category name (e.g. "JEE") via the backend's
// exam_category fallback — same helper used for the custom-test question fetch.
function subjectQueryParams(): Record<string, string> | null {
  const examTypeId = store.examType?.id
  if (examTypeId && /^\d+$/.test(examTypeId)) return { exam_id: examTypeId }
  const examId = store.exam?.id
  if (examId && /^\d+$/.test(examId)) return { exam_id: examId }
  // Use exam.category, not exam.label — the backend's exam_category values
  // are things like "Engineering Entrance Exam", not display labels like
  // "JEE Main". Sending the label here never matched anything.
  if (store.exam?.category) return { exam_category: store.exam.category }
  return null
}

function setSubjectMode(mode: SubjectMode): void {
  subjectMode.value = mode
  showSubjectDropdown.value = false
  expandedSubjects.value.clear()

  if (mode === 'all') {
    selectedSubjectIds.value.clear()
    // Re-assert "everything checked" for every subject, including ones
    // whose chapters were already fetched (e.g. during a prior visit to
    // this mode) — those wouldn't otherwise get re-selected since
    // loadChaptersFor only auto-checks chapters at fetch time.
    subjects.value.forEach(s => {
      const chapters = chaptersBySubject.value[s.id]
      if (chapters) {
        selectedChapterIds.value[s.id] = new Set(chapters.map(c => c.id))
      }
    })
    ensureAllChaptersLoaded()
  } else {
    // Select Subjects always starts from a clean slate — nothing checked
    // until the candidate picks chapters themselves, even if this subject
    // was previously fully-checked while in All Subjects mode.
    selectedChapterIds.value = {}
  }
}

function toggleSubject(id: string): void {
  if (selectedSubjectIds.value.has(id)) {
    selectedSubjectIds.value.delete(id)
    delete selectedChapterIds.value[id]
    delete chapterFilters.value[id]
    expandedSubjects.value.delete(id)
  } else {
    selectedSubjectIds.value.add(id)
  }
}

const selectedSubjectsList = computed(() =>
  subjects.value.filter(s => selectedSubjectIds.value.has(s.id))
)

const subjectSummaryLabel = computed(() => {
  if (subjectMode.value === 'all') return 'All Subjects'
  const labels = selectedSubjectsList.value.map(s => s.label)
  return labels.length ? labels.join(', ') : 'Not selected'
})

// ── Duration ───────────────────────────────────────────────────────
const durationPresets = [30, 60, 90, 120]
const duration = ref<number | null>(null)
const customDurationMode = ref(false)
function pickDuration(d: number): void {
  customDurationMode.value = false
  duration.value = d
}

// ── Difficulty ─────────────────────────────────────────────────────
type Difficulty = 'easy' | 'medium' | 'hard' | 'mixed'
const difficultyOptions: { value: Difficulty; label: string; icon: string }[] = [
  { value: 'easy',   label: 'Easy',   icon: '📈' },
  { value: 'medium', label: 'Medium', icon: '📊' },
  { value: 'hard',   label: 'Hard',   icon: '🔥' },
  { value: 'mixed',  label: 'Mixed',  icon: '🔀' },
]
const difficulty = ref<Difficulty | null>(null)

// ── Marks & Questions ──────────────────────────────────────────────
const numQuestions     = ref<number | null>(null)
const marksPerQuestion = ref<number | null>(4)
const totalMarks = computed(() =>
  numQuestions.value != null && marksPerQuestion.value != null
    ? numQuestions.value * marksPerQuestion.value
    : null
)

function adjustQuestions(delta: number): void {
  numQuestions.value = Math.max(5, (numQuestions.value ?? 0) + delta)
}
function adjustMarksPerQuestion(delta: number): void {
  marksPerQuestion.value = Math.max(1, (marksPerQuestion.value ?? 0) + delta)
}
function adjustTotalMarks(delta: number): void {
  // Total Marks is derived (Questions × Marks/Question); nudging it here
  // adjusts Marks per Question while keeping Number of Questions fixed.
  if (marksPerQuestion.value == null) { marksPerQuestion.value = 1; return }
  const step = delta === 0 ? 0 : delta / Math.abs(delta)
  marksPerQuestion.value = Math.max(1, marksPerQuestion.value + step)
}

// ── Negative Marking ───────────────────────────────────────────────
// Off by default — the candidate has to opt in.
const negativeMarking = ref<boolean>(false)
const negativeMarksPerQuestion = ref<number | null>(1)
function adjustNegativeMarks(delta: number): void {
  negativeMarksPerQuestion.value = Math.max(1, Number(((negativeMarksPerQuestion.value ?? 0) + delta).toFixed(2)))
}

// ── Start Test ─────────────────────────────────────────────────────
type TestMode = 'test' | 'practice'
const showModeModal = ref(false)

function openModeModal(): void {
  if (!canStart.value) return
  showModeModal.value = true
}
function closeModeModal(): void {
  showModeModal.value = false
}
function confirmStartTest(mode: TestMode): void {
  showModeModal.value = false
  startTest(mode)
}

const canProceedStep1 = computed(() => {
  if (subjectMode.value === 'all') return true
  return selectedSubjectIds.value.size > 0 && totalSelectedChapters.value > 0
})

const canStart = computed(() =>
  canProceedStep1.value &&
  !!duration.value && duration.value > 0 &&
  !!difficulty.value &&
  numQuestions.value != null && numQuestions.value > 0 &&
  marksPerQuestion.value != null && marksPerQuestion.value > 0
)

function startTest(mode: TestMode): void {
  if (!canStart.value || !duration.value || !difficulty.value || numQuestions.value == null || marksPerQuestion.value == null) return

  // NOTE: `chapterIds` is a new field — extend usePracticeTestStore's
  // setCustomConfig() type (and whatever reads it downstream) to accept it
  // if per-chapter filtering needs to reach the question-fetch API.
  // Any subject absent from this map (or mapped to an empty array) means
  // "include every chapter of that subject" — that's the default in both modes.
  // `mode` is passed as the second argument so the store actually records
  // Test vs Practice — setCustomConfig() used to hardcode 'test' internally.
  store.setCustomConfig({
    subjectIds: subjectMode.value === 'all' ? 'all' : Array.from(selectedSubjectIds.value),
    subjectLabel: subjectSummaryLabel.value,
    chapterIds: Object.fromEntries(
      Object.entries(selectedChapterIds.value)
        .filter(([, set]) => set.size > 0)
        .map(([sid, set]) => [sid, Array.from(set)])
    ),
    durationMinutes: duration.value,
    difficulty: difficulty.value,
    totalMarks: numQuestions.value * marksPerQuestion.value,
    numQuestions: numQuestions.value,
    marksPerQuestion: marksPerQuestion.value,
    negativeMarking: negativeMarking.value,
    negativeMarksPerQuestion: negativeMarking.value ? negativeMarksPerQuestion.value : 0,
  } as any, mode)

  router.push({ name: 'practice-test' })
}
</script>

<style scoped>
.cct-page { max-width: 1200px; margin: 0 auto; }

.cct-title { font-size: 20px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.cct-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 20px; }

.cct-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  align-items: start;
  margin-bottom: 24px;
}
@media (max-width: 980px) {
  .cct-layout { grid-template-columns: 1fr; }
}

.cct-builder {
  background: #fff;
  border: 1px solid #eef0f4;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 26px;
}

.cct-step { display: flex; flex-direction: column; gap: 12px; }

.step-head { display: flex; gap: 12px; align-items: flex-start; }
.step-num {
  width: 24px; height: 24px; border-radius: 50%; background: #7c3aed; color: #fff;
  font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}
.step-head h3 { font-size: 14.5px; font-weight: 800; color: #1e2536; margin: 0 0 2px; }
.step-head p  { font-size: 12px; color: #6b7280; margin: 0; }

.inline-loading, .inline-error { font-size: 13px; color: #6b7280; padding: 8px 0 8px 36px; }
.inline-error { color: #ef4444; }

.subject-grid, .duration-grid, .difficulty-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding-left: 36px;
}
@media (max-width: 700px) {
  .subject-grid, .duration-grid, .difficulty-grid { grid-template-columns: repeat(2, 1fr); }
}

.subject-chip, .duration-chip, .difficulty-chip {
  position: relative;
  display: flex; align-items: center; gap: 8px;
  border: 1.5px solid #e5e7eb; border-radius: 10px; background: #fff;
  padding: 12px 14px; cursor: pointer; user-select: none; font-size: 13px; font-weight: 600; color: #374151;
  text-align: left;
}
.subject-chip.selected, .duration-chip.selected, .difficulty-chip.selected {
  border-color: #7c3aed; background: #f5f3ff; color: #1e2536;
}

.chip-icon {
  width: 26px; height: 26px; border-radius: 7px; display: flex; align-items: center;
  justify-content: center; font-size: 13px; flex-shrink: 0;
}
.icon-grid { background: #ede9fe; color: #7c3aed; }
.c-blue { background: #dbeafe; }
.c-green { background: #d1fae5; }
.c-purple { background: #ede9fe; }
.c-pink { background: #fce7f3; }
.c-indigo { background: #e0e7ff; }

.check-badge {
  position: absolute; top: -6px; right: -6px;
  width: 18px; height: 18px; border-radius: 50%; background: #7c3aed; color: #fff;
  font-size: 10px; display: flex; align-items: center; justify-content: center;
}

/* ── Step 1: Subjects & Chapters ─────────────────────────────────── */
.subj-body { display: flex; flex-direction: column; gap: 16px; }
.cct-step--plain { gap: 16px; }

.mode-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 700px) { .mode-grid { grid-template-columns: 1fr; } }

.mode-card {
  display: flex; align-items: flex-start; gap: 10px; text-align: left;
  border: 1.5px solid #e5e7eb; border-radius: 10px; background: #fff;
  padding: 14px 16px; cursor: pointer;
  user-select: none;
}
.mode-card.selected { border-color: #7c3aed; background: #f5f3ff; }
.mode-radio {
  width: 18px; height: 18px; border-radius: 50%; border: 2px solid #d1d5db;
  flex-shrink: 0; margin-top: 2px; position: relative; background: #fff;
}
.mode-radio.checked { border-color: #7c3aed; }
.mode-radio.checked::after {
  content: ''; position: absolute; inset: 3px; border-radius: 50%; background: #7c3aed;
}
.mode-text { display: flex; flex-direction: column; gap: 3px; }
.mode-text strong { font-size: 13.5px; font-weight: 700; color: #1e2536; }
.mode-text small { font-size: 12px; color: #6b7280; }

.field-block { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 12.5px; font-weight: 700; color: #7c3aed; }
.field-label .req { color: #ef4444; }
.field-hint { font-size: 12px; color: #6b7280; margin: 0 0 2px; }

.ms-box {
  position: relative;
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  min-height: 46px; border: 1.5px solid #e5e7eb; border-radius: 10px;
  background: #fff; padding: 8px 40px 8px 12px; cursor: pointer;
  user-select: none;
}
.ms-placeholder { font-size: 13px; color: #9ca3af; }
.ms-tag {
  display: flex; align-items: center; gap: 6px;
  background: #f5f3ff; border: 1px solid #ede9fe; color: #1e2536;
  font-size: 12.5px; font-weight: 600; border-radius: 7px; padding: 5px 8px;
}
.ms-tag-icon { font-size: 12px; }
.ms-tag-x {
  border: none; background: none; cursor: pointer; user-select: none; color: #9ca3af;
  font-size: 14px; line-height: 1; padding: 0 0 0 2px;
}
.ms-chevron {
  position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
  font-size: 10px; color: #9ca3af; transition: transform 0.15s;
}
.ms-chevron.open { transform: translateY(-50%) rotate(180deg); }

.ms-dropdown {
  display: flex; flex-direction: column; gap: 2px;
  border: 1.5px solid #e5e7eb; border-radius: 10px; background: #fff;
  padding: 6px; max-height: 220px; overflow-y: auto;
}
.ms-option {
  display: flex; align-items: center; gap: 8px;
  border: none; background: none; text-align: left; cursor: pointer;user-select: none;
  font-size: 13px; font-weight: 600; color: #374151;
  padding: 8px 10px; border-radius: 7px; position: relative;
}
.ms-option:hover { background: #f9fafb; }
.ms-option.picked { background: #f5f3ff; color: #1e2536; }
.ms-check { margin-left: auto; color: #7c3aed; font-size: 12px; }

.chapters-panel { display: flex; flex-direction: column; gap: 10px; }
.chap-subject {
  border: 1.5px solid #e5e7eb; border-radius: 10px; overflow: hidden; background: #fff;
}
.chap-subject.open { border-color: #ddd6fe; }
.chap-subject-head {
  width: 100%; display: flex; align-items: center; gap: 10px;
  border: none; background: #fff; cursor: pointer; user-select: none;
  padding: 12px 14px; text-align: left;
}
.chap-subject-name { font-size: 13.5px; font-weight: 700; color: #1e2536; }
.chap-count-pill {
  margin-left: auto; background: #ede9fe; color: #7c3aed;
  font-size: 11.5px; font-weight: 700; padding: 3px 9px; border-radius: 999px;
}
.chap-chevron { font-size: 10px; color: #9ca3af; transition: transform 0.15s; }
.chap-chevron.open { transform: rotate(180deg); }

.chap-subject-body { padding: 0 14px 14px; display: flex; flex-direction: column; gap: 10px; }
.chap-search {
  position: relative; display: flex; align-items: center;
  border: 1.5px solid #e5e7eb; border-radius: 8px; padding: 8px 34px 8px 10px;
}
.chap-search input { border: none; outline: none; font-size: 13px; width: 100%; }
.chap-search-chevron { position: absolute; right: 12px; font-size: 10px; color: #9ca3af; }

.chap-list {
  list-style: none; margin: 0; padding: 4px 2px;
  max-height: 220px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 2px;
}
.chap-item {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: #374151; cursor: pointer; user-select: none;
  padding: 7px 6px; border-radius: 6px;
}
.chap-item:hover { background: #f9fafb; }
.chap-item input[type="checkbox"] {
  width: 16px; height: 16px; accent-color: #7c3aed; cursor: pointer; user-select: none; flex-shrink: 0;
}
.chap-empty { font-size: 12.5px; color: #9ca3af; padding: 8px 6px; }

.chap-select-all {
  font-weight: 700;
  color: #1e2536;
  border-bottom: 1px solid #e5e7eb;
  margin: 2px 2px 4px;
  padding-bottom: 9px;
}
.chap-select-all:hover { background: transparent; }

.all-subjects-note {
  background: #ecfdf5; color: #047857; font-size: 12.5px; font-weight: 600;
  padding: 12px 14px; border-radius: 8px;
}

/* ── Selected Chapters Criteria (sidebar) ────────────────────────── */
.crit-card { margin-bottom: 18px; padding-bottom: 18px; border-bottom: 1px solid #ede9fe; }

.crit-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
.crit-stat {
  background: #fff; border: 1px solid #ede9fe; border-radius: 10px;
  padding: 10px 12px; display: flex; flex-direction: column; gap: 4px;
}
.crit-stat span { font-size: 11.5px; color: #6b7280; font-weight: 600; }
.crit-stat strong { font-size: 19px; font-weight: 800; color: #1e2536; }

.crit-summary-title { font-size: 12.5px; font-weight: 700; color: #1e2536; margin-bottom: 10px; }

.crit-subject-card {
  background: #fff; border: 1px solid #ede9fe; border-radius: 10px;
  padding: 12px 14px; margin-bottom: 10px;
}
.crit-subject-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.crit-subject-head strong { font-size: 13px; color: #1e2536; }
.crit-count-pill {
  margin-left: auto; background: #ede9fe; color: #7c3aed;
  font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 999px;
}
.crit-chapter-list { list-style: none; margin: 0 0 8px; padding: 0; }
.crit-chapter-list li {
  font-size: 12px; color: #4b5563; padding: 3px 0 3px 14px; position: relative;
}
.crit-chapter-list li::before {
  content: ''; position: absolute; left: 2px; top: 10px;
  width: 4px; height: 4px; border-radius: 50%; background: #c4b5fd;
}
.crit-remove {
  border: none; background: none; cursor: pointer; user-select: none; padding: 0;
  font-size: 12px; font-weight: 700; color: #ef4444;
}

.crit-total-box {
  background: #fff; border: 1px solid #ede9fe; border-radius: 10px;
  padding: 12px 14px; display: flex; justify-content: space-between;
  margin: 4px 0 12px;
}
.crit-total-box > div { display: flex; flex-direction: column; gap: 3px; }
.crit-total-box span { font-size: 11px; color: #6b7280; font-weight: 600; }
.crit-total-box strong { font-size: 15px; font-weight: 800; color: #1e2536; }

.crit-info-note {
  background: #eff6ff; color: #1e40af; font-size: 12px; font-weight: 500;
  padding: 10px 12px; border-radius: 8px; line-height: 1.5;
}

.inline-loading.small, .inline-error.small { padding: 6px 2px; font-size: 12.5px; }

.clock-icon, .pencil-icon { font-size: 13px; }
.custom-chip { color: #7c3aed; border-style: dashed; }

.custom-duration-input {
  display: flex; align-items: center; gap: 8px; padding-left: 36px;
}
.custom-duration-input input {
  border: 1.5px solid #e5e7eb; border-radius: 8px; padding: 8px 10px;
  font-size: 13px; width: 120px;
}
.custom-duration-input span { font-size: 12px; color: #6b7280; }

.difficulty-chip.easy.selected   { border-color: #10b981; background: #ecfdf5; }
.difficulty-chip.medium.selected { border-color: #f59e0b; background: #fef9c3; }
.difficulty-chip.hard.selected   { border-color: #ef4444; background: #fef2f2; }
.difficulty-chip.mixed.selected  { border-color: #7c3aed; background: #f5f3ff; }

.mq-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding-left: 36px;
}
@media (max-width: 700px) {
  .mq-grid { grid-template-columns: 1fr; }
}

.mq-field label { font-size: 12px; font-weight: 700; color: #374151; display: block; margin-bottom: 8px; }
.stepper {
  display: flex; align-items: center; justify-content: space-between;
  border: 1.5px solid #e5e7eb; border-radius: 9px; padding: 6px 10px;
}
.stepper button {
  width: 26px; height: 26px; border-radius: 6px; border: 1px solid #e5e7eb; background: #fafafa;
  font-size: 16px; font-weight: 700; cursor: pointer; user-select: none; color: #374151;
}
.stepper span { font-size: 15px; font-weight: 800; color: #1e2536; }

.formula-note {
  margin-left: 36px;
  background: #eff6ff; color: #1e40af; font-size: 12px;
  padding: 10px 14px; border-radius: 8px;
}

.neg-mark-row {
  margin-left: 36px;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  border: 1.5px solid #e5e7eb; border-radius: 10px;
  padding: 12px 14px;
}
.neg-mark-text { display: flex; flex-direction: column; gap: 2px; }
.neg-mark-text strong { font-size: 13px; font-weight: 700; color: #1e2536; }
.neg-mark-text small { font-size: 12px; color: #6b7280; }

.neg-mark-controls { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }

.stepper--compact { padding: 4px 8px; gap: 10px; }
.stepper--compact button { width: 22px; height: 22px; font-size: 14px; }
.stepper--compact span { font-size: 13px; min-width: 16px; text-align: center; }

.toggle-switch {
  position: relative; flex-shrink: 0;
  width: 40px; height: 22px; border-radius: 999px;
  border: none; background: #d1d5db; cursor: pointer;
  padding: 0; transition: background 0.15s;
}
.toggle-switch.on { background: #7c3aed; }
.toggle-knob {
  position: absolute; top: 2px; left: 2px;
  width: 18px; height: 18px; border-radius: 50%; background: #fff;
  transition: transform 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}
.toggle-switch.on .toggle-knob { transform: translateX(18px); }

.cct-summary {
  background: #f5f3ff;
  border: 1px solid #ede9fe;
  border-radius: 16px;
  padding: 20px;
}

.summary-head { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.summary-icon {
  width: 34px; height: 34px; background: #ede9fe; border-radius: 9px;
  display: flex; align-items: center; justify-content: center; font-size: 15px;
}
.summary-head h3 { font-size: 14.5px; font-weight: 800; color: #1e2536; margin: 0; }

.summary-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12.5px; color: #4b5563; padding: 8px 0; border-bottom: 1px solid #ede9fe;
}
.summary-row strong { color: #1e2536; font-weight: 700; text-align: right; max-width: 60%; }
.summary-row strong.cap { text-transform: capitalize; }
.summary-row strong.unset { color: #9ca3af; font-weight: 600; font-style: italic; }

.summary-pending {
  font-size: 12.5px;
  color: #6b7280;
  font-style: italic;
  padding: 10px 0 4px;
  line-height: 1.6;
}

.notes-box {
  margin-top: 16px;
  background: #eff6ff;
  border-radius: 10px;
  padding: 14px;
}
.notes-head {
  display: flex; align-items: center; gap: 6px;
  font-size: 12.5px; font-weight: 700; color: #1e40af; margin-bottom: 8px;
}
.notes-box ul { margin: 0; padding-left: 18px; font-size: 12px; color: #1e40af; line-height: 1.7; }

.cct-footer { display: flex; justify-content: space-between; align-items: center; }

.back-btn {
  background: #fff; border: 1px solid #e5e7eb; color: #1e2536;
  font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: 8px; cursor: pointer;user-select: none;
}
.start-btn {
  background: #7c3aed; border: none; color: #fff;
  font-weight: 700; font-size: 13px; padding: 10px 22px; border-radius: 8px; cursor: pointer;user-select: none;
}
.start-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Test Mode / Practice Mode modal ─────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(17, 17, 27, 0.55);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.modal-card {
  background: #fff; border-radius: 18px; padding: 26px;
  width: 100%; max-width: 640px;
  box-shadow: 0 24px 60px rgba(17, 17, 27, 0.3);
}
.modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.modal-header h3 { font-size: 17px; font-weight: 800; color: #1e2536; margin: 0; }
.modal-close {
  border: none; background: #f3f4f6; color: #6b7280;
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  font-size: 15px; line-height: 1; cursor: pointer; user-select: none;
  display: flex; align-items: center; justify-content: center;
}
.modal-subtitle { font-size: 12.5px; color: #6b7280; margin: 4px 0 0; }

.mode-modal-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  margin-top: 20px;
}
@media (max-width: 600px) {
  .mode-modal-grid { grid-template-columns: 1fr; }
}

.mode-modal-card {
  position: relative;
  display: flex; flex-direction: column; align-items: flex-start; gap: 6px;
  border: 1.5px solid #e5e7eb; border-radius: 14px; background: #fff;
  padding: 18px 16px 16px; text-align: left; cursor: pointer; user-select: none;
  transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}
.mode-modal-card:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(17, 17, 27, 0.1); }

.mode-modal-badge {
  align-self: flex-start;
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.02em;
  padding: 3px 9px; border-radius: 999px; margin-bottom: 4px;
}
.mode-modal-icon {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; margin-bottom: 2px;
}
.mode-modal-card strong { font-size: 14.5px; font-weight: 800; color: #1e2536; }
.mode-modal-card small { font-size: 12px; color: #6b7280; line-height: 1.55; min-height: 48px; }
.mode-modal-cta {
  margin-top: 8px; font-size: 12px; font-weight: 700;
}

.mode-modal-card--test { border-color: #fed7aa; }
.mode-modal-card--test:hover { border-color: #f97316; background: #fff7ed; }
.mode-modal-card--test .mode-modal-badge { background: #ffedd5; color: #c2410c; }
.mode-modal-card--test .mode-modal-icon { background: #ffedd5; }
.mode-modal-card--test .mode-modal-cta { color: #ea580c; }

.mode-modal-card--practice { border-color: #bfdbfe; }
.mode-modal-card--practice:hover { border-color: #3b82f6; background: #eff6ff; }
.mode-modal-card--practice .mode-modal-badge { background: #dbeafe; color: #1d4ed8; }
.mode-modal-card--practice .mode-modal-icon { background: #dbeafe; }
.mode-modal-card--practice .mode-modal-cta { color: #2563eb; }
</style>