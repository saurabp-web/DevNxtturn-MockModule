<template>
  <div class="page-wrapper">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Question Bank</h1>
        <p class="page-desc">Manage and organize all your questions.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn--secondary" @click="router.push({ name: 'question-import' })">
          ↑ Import Questions
        </button>
        <button class="btn btn--primary" @click="router.push({ name: 'question-add' })">
          + Add Question
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <input
        v-model="search"
        type="text"
        class="search-input"
        placeholder="Search questions..."
      />
      <select v-model="filterSubject" class="filter-select">
        <option value="">All Subjects</option>
        <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
      <select v-model="filterDifficulty" class="filter-select">
        <option value="">All Difficulties</option>
        <option value="easy">Easy</option>
        <option value="medium">Medium</option>
        <option value="hard">Hard</option>
      </select>
      <select v-model="filterType" class="filter-select">
        <option value="">All Types</option>
        <option value="single_correct">Single Correct</option>
        <option value="multiple_correct">Multiple Correct</option>
        <option value="integer">Integer</option>
      </select>
    </div>

    <!-- Table -->
    <div class="card">
      <table class="table">
        <thead>
          <tr>
            <th class="th-check">
              <input type="checkbox" v-model="selectAll" @change="toggleAll" />
            </th>
            <th>Question</th>
            <th>Subject</th>
            <th>Chapter</th>
            <th>Mapped Exams</th>
            <th>Type</th>
            <th>Difficulty</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="empty-row">Loading questions...</td>
          </tr>
          <tr v-else-if="error">
            <td colspan="8" class="empty-row error-row">
              <span>⚠️ {{ error }}</span>
              <br />
              <button class="retry-btn" @click="fetchQuestions">Retry</button>
            </td>
          </tr>
          <tr v-else-if="filteredQuestions.length === 0">
            <td colspan="8" class="empty-row">No questions found.</td>
          </tr>
          <tr
            v-for="question in filteredQuestions"
            :key="question.id"
            class="table-row"
          >
            <td>
              <input type="checkbox" v-model="selected" :value="question.id" />
            </td>
            <td class="question-cell">
              <p class="question-text">{{ question.text }}</p>
            </td>
            <td class="td-meta">{{ question.subject }}</td>
            <td class="td-meta">{{ question.chapter }}</td>
            <td class="td-exams">
              <span
                v-for="(exam, idx) in question.mappedExams.slice(0, 2)"
                :key="idx"
                class="exam-chip"
                :title="examChipTitle(exam)"
              >
                {{ exam.exam_name || 'Unknown exam' }}
              </span>
              <span
                v-if="question.mappedExams.length > 2"
                class="exam-chip exam-chip--more"
                :title="question.mappedExams.slice(2).map(e => e.exam_name).join(', ')"
              >
                +{{ question.mappedExams.length - 2 }}
              </span>
            </td>
            <td class="td-meta">{{ question.type }}</td>
            <td>
              <span :class="['badge', `badge--${question.difficulty}`]">
                {{ question.difficulty }}
              </span>
            </td>
            <td>
              <div class="action-btns">
                <button class="icon-btn" title="Edit" @click="router.push({ name: 'question-edit', params: { id: question.id } })">✏️</button>
                <button class="icon-btn" title="Review" @click="router.push({ name: 'question-review', params: { id: question.id } })">👁️</button>
                <button class="icon-btn icon-btn--danger" title="Delete" @click="deleteQuestion(question.id)">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="totalPages > 1 || totalCount > 0" class="pagination-bar">
        <span class="pagination-info">
          {{ totalCount }} question{{ totalCount !== 1 ? 's' : '' }}
        </span>
        <div class="pagination-controls">
          <button class="page-btn" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">‹ Prev</button>
          <span class="page-indicator">Page {{ currentPage }} of {{ totalPages }}</span>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">Next ›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const search        = ref('')
const filterSubject = ref('')
const filterDifficulty = ref('')
const filterType    = ref('')
const selected      = ref([])
const selectAll     = ref(false)
const loading       = ref(false)
const error         = ref(null)

// Pagination
const currentPage   = ref(1)
const totalPages    = ref(1)
const totalCount    = ref(0)
const PAGE_SIZE     = 20

// Dynamic data from backend
const questions = ref([])
const subjects  = ref([])   // for the Subject dropdown

// ── Fetch subject list for the filter dropdown ──────────────────────────
async function fetchSubjects() {
  try {
    const res  = await fetch('/api/subjects/')
    if (!res.ok) return
    const data = await res.json()
    const raw  = Array.isArray(data) ? data : (data.results ?? [])
    // SubjectSerializer returns { id, label }
    subjects.value = raw.map(s => ({ id: s.id ?? s.subject_id, name: s.label ?? s.subject_name }))
  } catch (_) { /* silently skip — dropdown will just be empty */ }
}

// ── Fetch question bank from the new admin endpoint ─────────────────────
async function fetchQuestions(page = 1) {
  loading.value = true
  error.value   = null
  try {
    const params = new URLSearchParams()
    params.append('admin',     'true')
    params.append('page',      page)
    params.append('page_size', PAGE_SIZE)

    if (search.value)           params.append('search',        search.value)
    if (filterSubject.value)    params.append('subject_id',    filterSubject.value)
    if (filterDifficulty.value) params.append('difficulty',    filterDifficulty.value)
    if (filterType.value)       params.append('question_type', filterType.value)

    const res = await fetch(`/api/questions/?${params.toString()}`)

    if (!res.ok) {
      let msg = `Server error: ${res.status}`
      try {
        const body = await res.json()
        if (body.error)  msg = body.error
        else if (body.detail) msg = body.detail
      } catch (_) {}
      throw new Error(msg)
    }

    const data = await res.json()

    // Response shape: { count, total_pages, page, page_size, results: [] }
    const raw       = Array.isArray(data) ? data : (data.results ?? [])
    totalCount.value = data.count   ?? raw.length
    totalPages.value = data.total_pages ?? 1
    currentPage.value = page

    questions.value = raw.map(q => ({
      id:          q.question_id,
      text:        q.question_text,
      subject:     q.subject_name   || '—',
      chapter:     q.chapter_name   || '—',
      type:        formatType(q.question_type),
      difficulty:  (q.difficulty_level || 'medium').toLowerCase(),
      // Grouped duplicate-question data from the admin endpoint — one row
      // per unique question text, with every exam it's mapped to. Falls
      // back to a single-entry list so this still renders sensibly if the
      // backend response isn't grouped (e.g. an older API version).
      mappedExams: q.mapped_exams ?? [{ exam_name: null, year: null, session: null }],
      // Every underlying question_id in this group — needed so delete
      // removes the whole group, not just the primary row, and so we
      // don't leave orphaned duplicate rows behind.
      allQuestionIds: q.all_question_ids ?? [q.question_id],
    }))
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function formatType(raw) {
  if (!raw) return '—'
  const map = {
    single_correct:   'Single Correct',
    mcq:              'Single Correct',
    multiple_correct: 'Multiple Correct',
    msq:              'Multiple Correct',
    integer:          'Integer',
    numeric:          'Integer',
    subjective:       'Subjective',
  }
  return map[raw.toLowerCase()] ?? raw
}

// Tooltip text for a single exam chip — includes year/session when present
// so the admin can see e.g. "NEET-UG · 2024 · shift_1" on hover without
// needing to open the question.
function examChipTitle(exam) {
  const parts = [exam.exam_name || 'Unknown exam']
  if (exam.year) parts.push(exam.year)
  if (exam.session) parts.push(exam.session)
  return parts.join(' · ')
}

// Re-fetch from page 1 whenever filters change
watch([search, filterSubject, filterDifficulty, filterType], () => {
  fetchQuestions(1)
})

onMounted(() => {
  fetchSubjects()
  fetchQuestions(1)
})

// Client-side select-all scoped to current page
const filteredQuestions = computed(() => questions.value)

function toggleAll() {
  selected.value = selectAll.value ? questions.value.map(q => q.id) : []
}

async function deleteQuestion(id) {
  if (!confirm('Are you sure you want to delete this question?')) return
  // A grouped row can represent several underlying Question rows (the
  // same text mapped onto multiple exams) — deleting the group needs to
  // remove all of them, or the "duplicate" rows would just reappear the
  // next time this list is fetched.
  const group = questions.value.find(q => q.id === id)
  const idsToDelete = group?.allQuestionIds ?? [id]
  try {
    await Promise.all(
      idsToDelete.map(qid =>
        fetch(`/api/questions/?admin=true&id=${qid}`, { method: 'DELETE' }).then(res => {
          if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
        })
      )
    )
    questions.value  = questions.value.filter(q => q.id !== id)
    selected.value   = selected.value.filter(sid => sid !== id)
    totalCount.value = Math.max(0, totalCount.value - 1)
  } catch (err) {
    alert(err.message)
  }
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  fetchQuestions(page)
}
</script>

<style scoped>
.page-wrapper {
  padding: 28px 32px;
  background: #f5f6fa;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
}

.page-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--primary { background: #4f46e5; color: #fff; }
.btn--primary:hover { background: #4338ca; }
.btn--secondary { background: #fff; color: #374151; border: 1px solid #d1d5db; }
.btn--secondary:hover { background: #f3f4f6; }

.filters-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
  background: #fff;
}

.search-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
}

.filter-select {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #374151;
  background: #fff;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #4f46e5;
}

.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table thead tr {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.th-check { width: 40px; }

.table-row {
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.1s;
}

.table-row:last-child { border-bottom: none; }
.table-row:hover { background: #f9fafb; }

.table td {
  padding: 14px 16px;
  vertical-align: middle;
}

.question-cell { max-width: 380px; }

.question-text {
  font-size: 14px;
  color: #111827;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 360px;
}

.td-meta {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}

.td-exams {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-width: 220px;
}

.exam-chip {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  background: #eef2ff;
  color: #4338ca;
  white-space: nowrap;
  cursor: default;
}

.exam-chip--more {
  background: #f3f4f6;
  color: #6b7280;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.badge--easy { background: #dcfce7; color: #16a34a; }
.badge--medium { background: #fef3c7; color: #d97706; }
.badge--hard { background: #fee2e2; color: #dc2626; }

.action-btns {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.12s;
}

.icon-btn:hover { background: #f3f4f6; }
.icon-btn--danger:hover { background: #fee2e2; }

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.pagination-info {
  font-size: 13px;
  color: #6b7280;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-btn {
  padding: 5px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  color: #374151;
  transition: background 0.12s;
}
.page-btn:hover:not(:disabled) { background: #f3f4f6; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.page-indicator {
  font-size: 13px;
  color: #374151;
  min-width: 100px;
  text-align: center;
}

.empty-row {
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
  padding: 48px 0;
}

.error-row {
  color: #dc2626;
}

.retry-btn {
  margin-top: 10px;
  padding: 6px 16px;
  border: 1px solid #dc2626;
  border-radius: 6px;
  background: #fff;
  color: #dc2626;
  font-size: 13px;
  cursor: pointer;
}
.retry-btn:hover { background: #fee2e2; }
</style>