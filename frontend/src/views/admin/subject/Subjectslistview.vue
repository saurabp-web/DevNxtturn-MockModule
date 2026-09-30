<template>
  <div class="subjects-page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Subjects</h1>
        <p class="page-sub">Manage subjects for all exams</p>
      </div>
      <div class="breadcrumb">
        <span>Home</span>
        <span class="crumb-sep">›</span>
        <span>Syllabus</span>
        <span class="crumb-sep">›</span>
        <span class="crumb-current">Subjects</span>
      </div>
    </div>

    <!-- Loading / error status (mirrors AddSubjectView.vue's pattern) -->
    <p v-if="loadingSubjects" class="exam-load-status">Loading subjects…</p>
    <p v-else-if="loadError" class="exam-load-status error">⚠ {{ loadError }}</p>

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.iconBg, color: s.iconColor }">
          <component :is="s.icon" :size="20" />
        </div>
        <div class="stat-body">
          <p class="stat-label">{{ s.label }}</p>
          <p class="stat-value">{{ s.value }}</p>
          <p class="stat-hint">{{ s.hint }}</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="search-input">
        <Search :size="16" class="search-icon" />
        <input v-model="searchTerm" type="text" placeholder="Search subjects..." />
      </div>

      <div class="filter-select">
        <label>Select Exam</label>
        <select v-model="filters.exam">
          <option value="">All Exams</option>
          <option v-for="e in examOptions" :key="e" :value="e">{{ e }}</option>
        </select>
      </div>

      <div class="filter-select">
        <label>Stream</label>
        <select v-model="filters.stream">
          <option value="">All Streams</option>
          <option v-for="s in streamOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="filter-select">
        <label>Status</label>
        <select v-model="filters.status">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      <button class="btn btn-primary add-subject-btn" @click="goToAddSubject">
        <Plus :size="16" />
        Add Subject
      </button>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="subjects-table">
        <thead>
          <tr>
            <th class="col-num">#</th>
            <th>Subject Name</th>
            <th>Exam</th>
            <th>Stream(s)</th>
            <th>Education Level(s)</th>
            <th class="col-center">Chapters</th>
            <th>Status</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in pagedRows" :key="row.id">
            <td class="col-num">{{ (page - 1) * pageSize + i + 1 }}</td>
            <td>
              <div class="subject-cell">
                <span class="subject-icon"><BookOpen :size="16" /></span>
                <span class="subject-name">{{ row.name }}</span>
              </div>
            </td>
            <td>
              <div class="exam-cell">
                <span class="exam-name">{{ row.examName }}</span>
                <span class="exam-code">{{ row.examCode }}</span>
              </div>
            </td>
            <td>
              <div class="chip-row">
                <span
                  v-for="chip in row.streams.slice(0, 2)"
                  :key="chip"
                  class="chip"
                  :class="chipClass(chip)"
                >{{ chip }}</span>
                <span v-if="row.streams.length > 2" class="chip chip-more">
                  +{{ row.streams.length - 2 }}
                </span>
              </div>
            </td>
            <td class="edu-level">{{ row.educationLevel }}</td>
            <td class="col-center chapters-count">{{ row.chapters }}</td>
            <td>
              <span class="status-badge" :class="row.active ? 'status-active' : 'status-inactive'">
                <span class="status-dot" />
                {{ row.active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="col-actions">
              <div class="action-icons">
                <button class="icon-btn" title="View" @click="$emit('view', row)">
                  <Eye :size="15" />
                </button>
                <button class="icon-btn" title="Edit" @click="goToEditSubject(row)">
                  <Pencil :size="15" />
                </button>
                <button class="icon-btn icon-danger" title="Delete" @click="confirmDelete(row)">
                  <Trash2 :size="15" />
                </button>
              </div>
            </td>
          </tr>

          <tr v-if="!pagedRows.length">
            <td colspan="8" class="empty-row">
              <template v-if="loadingSubjects">Loading subjects…</template>
              <template v-else-if="!rows.length">
                No subjects found yet. Click "Add Subject" to create one.
              </template>
              <template v-else>No subjects match your filters.</template>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination footer -->
      <div class="table-footer">
        <p class="showing-text">
          Showing {{ rangeStart }} to {{ rangeEnd }} of {{ filteredRows.length }} subjects
        </p>
        <div class="pagination">
          <button class="page-btn" :disabled="page === 1" @click="page--">
            <ChevronLeft :size="15" />
          </button>
          <button
            v-for="p in pageButtons"
            :key="p.key"
            class="page-btn"
            :class="{ active: p.num === page, ellipsis: p.num === null }"
            :disabled="p.num === null"
            @click="p.num && (page = p.num)"
          >{{ p.num ?? '…' }}</button>
          <button class="page-btn" :disabled="page === totalPages" @click="page++">
            <ChevronRight :size="15" />
          </button>
          <select v-model.number="pageSize" class="page-size-select">
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, Plus, BookOpen, CheckCircle2, Layers, FileText,
  Eye, Pencil, Trash2, ChevronLeft, ChevronRight,
} from 'lucide-vue-next'

interface SubjectRow {
  id: number | string
  name: string
  examName: string
  examCode: string
  streams: string[]
  educationLevel: string
  chapters: number
  active: boolean
}

// CHANGED: switched from `withDefaults(defineProps<{...}>(), {...})` to
// plain runtime prop declarations. The type-only macro version was
// compiling in this project such that `rows` still resolved to
// `undefined` instead of `[]` at runtime — "Missing required prop: rows"
// plus a crash on `props.rows.length`. Runtime declarations with an
// explicit `default` always apply regardless of compiler/macro quirks,
// so this is the more robust fix.
const props = defineProps({
  rows: {
    type: Array as PropType<SubjectRow[]>,
    default: () => [],
  },
  totalSubjects: { type: Number, default: undefined },
  activeSubjects: { type: Number, default: undefined },
  examsCovered: { type: Number, default: undefined },
  recentlyAdded: { type: Number, default: undefined },
})

const emit = defineEmits<{
  (e: 'add-subject'): void
  (e: 'view', row: SubjectRow): void
  (e: 'edit', row: SubjectRow): void
  (e: 'delete', row: SubjectRow): void
}>()

// ── Live data fetch ──────────────────────────────────────────
// CHANGED: previously fetched /api/exams/ then fired one
// /api/subjects/?exam_id=X request per exam (N+1) — with hundreds of
// exams that's hundreds of parallel requests and the "Loading
// subjects…" state never resolved. The backend's /api/subjects/ now
// returns every subject (with exam name/code/streams/education levels
// already joined in) in a SINGLE call when no exam_id/exam_code is
// passed, so this is now just one fetch.
const fetchedRows = ref<SubjectRow[]>([])
const loadingSubjects = ref(false)
const loadError = ref('')

const rows = computed(() => {
  const passed = props.rows ?? []
  return passed.length ? passed : fetchedRows.value
})

async function loadSubjectsIfNeeded() {
  if ((props.rows ?? []).length) return   // parent already supplied them
  loadingSubjects.value = true
  loadError.value = ''
  try {
    const res = await fetch('/api/subjects/')
    if (!res.ok) throw new Error(`Failed to load subjects (${res.status})`)
    const json = await res.json()
    const subjects = json.subjects ?? []
    fetchedRows.value = subjects.map((s: any) => ({
      id: s.subject_id,
      name: s.subject_name,
      examName: s.exam_name ?? '',
      examCode: s.exam_code ?? '',
      streams: s.stream_names ?? [],
      educationLevel: (s.education_level_names ?? []).join(', '),
      chapters: s.chapter_count ?? 0,
      active: s.is_active ?? true,
    })) as SubjectRow[]
  } catch (err: any) {
    loadError.value = err.message || 'Could not load subjects.'
    console.error('Failed to load subjects:', err)
  } finally {
    loadingSubjects.value = false
  }
}

onMounted(loadSubjectsIfNeeded)

// ── Navigation ───────────────────────────────────────────────
// CHANGED: this component previously only emitted 'add-subject' with
// no listener anywhere (it's mounted directly by the router, not
// wrapped by a parent that handles the emit) — so the button did
// nothing. Navigate directly; still emit too in case a parent wants
// to override/listen.
const router = useRouter()

function goToAddSubject() {
  emit('add-subject')
  // Confirmed against router/index.ts: name 'admin-subjects-create',
  // path 'syllabus/subjects/create' under the '/exam-admin' parent —
  // i.e. /exam-admin/syllabus/subjects/create, not '.../subjects/add'.
  router.push({ name: 'admin-subjects-create' })
}

function goToEditSubject(row: SubjectRow) {
  emit('edit', row)
  // router/index.ts: name 'admin-subjects-edit', path
  // 'syllabus/subjects/:id/edit', props: true — so :id maps straight
  // to a route param.
  router.push({ name: 'admin-subjects-edit', params: { id: row.id } })
}

const activePct = computed(() => {
  const total = props.totalSubjects ?? rows.value.length
  const active = props.activeSubjects ?? rows.value.filter(r => r.active).length
  return total ? ((active / total) * 100).toFixed(2) : '0.00'
})

const stats = computed(() => [
  {
    label: 'Total Subjects',
    value: props.totalSubjects ?? rows.value.length,
    hint: 'Across all exams',
    icon: BookOpen,
    iconBg: '#EDE9FE',
    iconColor: '#7C3AED',
  },
  {
    label: 'Active Subjects',
    value: props.activeSubjects ?? rows.value.filter(r => r.active).length,
    hint: `${activePct.value}% active`,
    icon: CheckCircle2,
    iconBg: '#D1FAE5',
    iconColor: '#059669',
  },
  {
    label: 'Exams Covered',
    value: props.examsCovered ?? new Set(rows.value.map(r => r.examName)).size,
    hint: 'With subjects',
    icon: Layers,
    iconBg: '#FFEDD5',
    iconColor: '#D97706',
  },
  {
    label: 'Recently Added',
    value: props.recentlyAdded ?? 0,
    hint: 'In last 7 days',
    icon: FileText,
    iconBg: '#DBEAFE',
    iconColor: '#2563EB',
  },
])

// ── Filters ──────────────────────────────────────────────
const searchTerm = ref('')
const filters = ref({ exam: '', stream: '', status: '' })

const examOptions = computed(() => [...new Set(rows.value.map(r => r.examName))])
const streamOptions = computed(() => [...new Set(rows.value.flatMap(r => r.streams))])

const filteredRows = computed(() => {
  return rows.value.filter(r => {
    if (searchTerm.value && !r.name.toLowerCase().includes(searchTerm.value.toLowerCase())) return false
    if (filters.value.exam && r.examName !== filters.value.exam) return false
    if (filters.value.stream && !r.streams.includes(filters.value.stream)) return false
    if (filters.value.status === 'active' && !r.active) return false
    if (filters.value.status === 'inactive' && r.active) return false
    return true
  })
})

// ── Pagination ───────────────────────────────────────────
const page = ref(1)
const pageSize = ref(10)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize.value)))

const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredRows.value.slice(start, start + pageSize.value)
})

const rangeStart = computed(() => filteredRows.value.length ? (page.value - 1) * pageSize.value + 1 : 0)
const rangeEnd = computed(() => Math.min(page.value * pageSize.value, filteredRows.value.length))

// Compact page-button list with ellipses, e.g. 1 2 3 … 53
const pageButtons = computed(() => {
  const total = totalPages.value
  const current = page.value
  const nums: (number | null)[] = []
  const push = (n: number | null) => nums.push(n)

  if (total <= 7) {
    for (let i = 1; i <= total; i++) push(i)
  } else {
    push(1)
    if (current > 3) push(null)
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) push(i)
    if (current < total - 2) push(null)
    push(total)
  }
  return nums.map((n, i) => ({ num: n, key: `${n}-${i}` }))
})

function chipClass(chip: string) {
  const key = chip.toLowerCase()
  if (key === 'science') return 'chip-science'
  if (key === 'engineering') return 'chip-engineering'
  if (key === 'arts') return 'chip-arts'
  if (key === 'general') return 'chip-general'
  return 'chip-default'
}

function confirmDelete(row: SubjectRow) {
  if (confirm(`Delete "${row.name}"? This cannot be undone.`)) {
    emit('delete', row)
  }
}
</script>

<style scoped>
.subjects-page {
  padding: 28px 32px;
  background: #F9FAFB;
  min-height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #111827;
}

/* Header */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 26px; font-weight: 800; margin: 0; color: #111827; }
.page-sub { font-size: 13px; color: #6B7280; margin: 4px 0 0; }
.breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #9CA3AF; margin-top: 6px; }
.crumb-sep { color: #D1D5DB; }
.crumb-current { color: #7C3AED; font-weight: 600; }

.exam-load-status {
  font-size: 12.5px; color: #6B7280; margin: 0 0 14px;
  background: #fff; border: 1px solid #F0F0F2; border-radius: 10px;
  padding: 10px 14px;
}
.exam-load-status.error { color: #DC2626; background: #FEF2F2; border-color: #FECACA; }

/* Stat cards */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 22px;
}
.stat-card {
  background: #fff;
  border: 1px solid #F0F0F2;
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.stat-icon {
  width: 42px; height: 42px; border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-label { font-size: 12.5px; color: #6B7280; margin: 0 0 4px; font-weight: 600; }
.stat-value { font-size: 24px; font-weight: 800; margin: 0 0 2px; color: #111827; }
.stat-hint { font-size: 11.5px; color: #9CA3AF; margin: 0; }

/* Filters */
.filters-bar {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}
.search-input {
  position: relative;
  flex: 1;
  min-width: 220px;
}
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #9CA3AF; }
.search-input input {
  width: 100%;
  padding: 10px 12px 10px 34px;
  border: 1px solid #E5E7EB;
  border-radius: 9px;
  font-size: 13px;
  background: #fff;
}
.search-input input:focus { outline: none; border-color: #A78BFA; box-shadow: 0 0 0 3px #EDE9FE; }

.filter-select { display: flex; flex-direction: column; gap: 6px; min-width: 160px; }
.filter-select label { font-size: 11.5px; color: #6B7280; font-weight: 600; }
.filter-select select {
  padding: 9px 10px;
  border: 1px solid #E5E7EB;
  border-radius: 9px;
  font-size: 13px;
  background: #fff;
  color: #374151;
}
.filter-select select:focus { outline: none; border-color: #A78BFA; }

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  border-radius: 9px; font-size: 13px; font-weight: 700;
  padding: 10px 16px; cursor: pointer; border: none;
}
.btn-primary { background: #7C3AED; color: #fff; }
.btn-primary:hover { background: #6D28D9; }
.add-subject-btn { white-space: nowrap; }

/* Table */
.table-card {
  background: #fff;
  border: 1px solid #F0F0F2;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.subjects-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.subjects-table thead tr { background: #FAFAFB; border-bottom: 1px solid #F0F0F2; }
.subjects-table th {
  text-align: left; padding: 12px 16px;
  font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
  color: #9CA3AF; text-transform: uppercase;
}
.subjects-table td { padding: 14px 16px; border-bottom: 1px solid #F5F5F6; color: #374151; }
.subjects-table tbody tr:last-child td { border-bottom: none; }
.subjects-table tbody tr:hover { background: #FAFAFF; }
.col-num { width: 40px; color: #9CA3AF; }
.col-center { text-align: center; }
.col-actions { width: 110px; }

.subject-cell { display: flex; align-items: center; gap: 10px; }
.subject-icon {
  width: 30px; height: 30px; border-radius: 8px;
  background: #F5F3FF; color: #7C3AED;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.subject-name { font-weight: 700; color: #111827; }

.exam-cell { display: flex; flex-direction: column; gap: 2px; }
.exam-name { font-weight: 600; color: #374151; }
.exam-code { font-size: 11px; color: #9CA3AF; }

.chip-row { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  font-size: 11px; font-weight: 700; padding: 3px 9px;
  border-radius: 999px; white-space: nowrap;
}
.chip-science { background: #DBEAFE; color: #1D4ED8; }
.chip-engineering { background: #E0E7FF; color: #4338CA; }
.chip-arts { background: #FCE7F3; color: #BE185D; }
.chip-general { background: #F3F4F6; color: #374151; }
.chip-default { background: #F3F4F6; color: #374151; }
.chip-more { background: #F3F4F6; color: #6B7280; }

.edu-level { color: #6B7280; }
.chapters-count { font-weight: 700; color: #374151; }

.status-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 700; padding: 4px 10px 4px 8px;
  border-radius: 999px;
}
.status-active { background: #ECFDF5; color: #059669; }
.status-inactive { background: #F3F4F6; color: #6B7280; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.action-icons { display: flex; gap: 4px; }
.icon-btn {
  width: 28px; height: 28px; border-radius: 7px;
  border: none; background: none; color: #6B7280;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.icon-btn:hover { background: #F3F4F6; color: #374151; }
.icon-danger:hover { background: #FEF2F2; color: #DC2626; }

.empty-row { text-align: center; padding: 40px; color: #9CA3AF; }

/* Footer / pagination */
.table-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-top: 1px solid #F0F0F2;
}
.showing-text { font-size: 12.5px; color: #6B7280; margin: 0; }
.pagination { display: flex; align-items: center; gap: 6px; }
.page-btn {
  min-width: 30px; height: 30px; padding: 0 8px;
  border-radius: 7px; border: 1px solid #E5E7EB; background: #fff;
  font-size: 12.5px; font-weight: 600; color: #6B7280; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.page-btn:hover:not(:disabled) { background: #F9FAFB; }
.page-btn.active { background: #7C3AED; border-color: #7C3AED; color: #fff; }
.page-btn.ellipsis { border: none; cursor: default; }
.page-btn:disabled:not(.ellipsis) { opacity: 0.4; cursor: not-allowed; }
.page-size-select {
  margin-left: 6px; padding: 6px 8px; border-radius: 7px;
  border: 1px solid #E5E7EB; font-size: 12.5px; color: #374151; background: #fff;
}

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 700px) {
  .stat-grid { grid-template-columns: 1fr; }
  .filters-bar { flex-direction: column; align-items: stretch; }
}
</style>