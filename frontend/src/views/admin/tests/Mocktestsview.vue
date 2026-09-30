<template>
  <div class="page">
    <header class="page-head">
      <div>
        <h1>Mock Tests</h1>
        <p>Create and manage mock tests for students</p>
      </div>
      <button class="btn-primary" @click="goToCreate">+ Create Mock Test</button>
    </header>

    <!-- Stat cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon purple">📄</div>
        <div>
          <p class="stat-label">Total Mock Tests</p>
          <p class="stat-value">{{ stats.total }}</p>
          <p class="stat-sub">All mock tests</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">✓</div>
        <div>
          <p class="stat-label">Active</p>
          <p class="stat-value">{{ stats.published }}</p>
          <p class="stat-sub">Active mock tests</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon amber">🕓</div>
        <div>
          <p class="stat-label">Inactive</p>
          <p class="stat-value">{{ stats.draft }}</p>
          <p class="stat-sub">Not visible to students</p>
        </div>
      </div>
    </div>

    <!-- Filters + table card -->
    <div class="table-card">
      <div class="filters-row">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input v-model="search" type="text" placeholder="Search mock tests..." @input="onSearchInput" />
        </div>

        <div class="filter-field">
          <label>Exam Type</label>
          <select v-model="filters.examType" @change="loadData">
            <option value="">All Types</option>
            <option v-for="t in examTypes" :key="t.exam_type_id" :value="t.exam_type_id">{{ t.type_name }}</option>
          </select>
        </div>

        <div class="filter-field">
          <label>Exam Category</label>
          <select v-model="filters.category" @change="loadData">
            <option value="">All Categories</option>
            <option v-for="c in examCategories" :key="c.category_id" :value="c.category_id">{{ c.category_name }}</option>
          </select>
        </div>

        <div class="filter-field">
          <label>Status</label>
          <select v-model="filters.status" @change="loadData">
            <option value="">All Status</option>
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
          </select>
        </div>

        <button class="btn-reset" @click="resetFilters">⟲ Reset</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Mock Test Name</th>
              <th>Exam</th>
              <th>Exam Type</th>
              <th>Category</th>
              <th>Subjects</th>
              <th>Questions</th>
              <th>Marks</th>
              <th>Duration</th>
              <th>Status</th>
              <th>Created On</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="12" class="empty-cell">Loading mock tests…</td>
            </tr>
            <tr v-else-if="loadError">
              <td colspan="12" class="empty-cell error-cell">{{ loadError }}</td>
            </tr>
            <tr v-else-if="!rows.length">
              <td colspan="12" class="empty-cell">No mock tests found.</td>
            </tr>
            <tr v-for="(row, i) in rows" :key="row.mockexam_id">
              <td>{{ (page - 1) * pageSize + i + 1 }}</td>
              <td class="name-cell">{{ row.mockexam_name }}</td>
              <td>{{ row.exam_name || row.exam_code || '—' }}</td>
              <td>
                <span class="tag" :class="typeTagClass(row.exam_type_name)">{{ row.exam_type_name || '—' }}</span>
              </td>
              <td>{{ row.category_name || '—' }}</td>
              <td>{{ row.subjects_count ?? '—' }}</td>
              <td>{{ row.question_count ?? '—' }}</td>
              <td>{{ row.total_marks ?? '—' }}</td>
              <td>{{ row.duration_minutes ? `${row.duration_minutes} min` : '—' }}</td>
              <td>
                <span class="status-pill" :class="statusClass(row)">{{ statusLabel(row) }}</span>
              </td>
              <td>{{ formatDate(row.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button class="icon-btn" title="View" @click="onView(row)">👁</button>
                  <button class="icon-btn" title="Edit" @click="onEdit(row)">✎</button>
                  <button class="icon-btn delete-btn" title="Delete" :disabled="deletingId === row.mockexam_id" @click="onDelete(row)">
                    {{ deletingId === row.mockexam_id ? '…' : '🗑' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-foot">
        <span>Showing {{ rangeStart }} to {{ rangeEnd }} of {{ total }} entries</span>
        <div class="pagination">
          <button class="page-btn" :disabled="page === 1" @click="goToPage(page - 1)">‹</button>
          <button
            v-for="p in pageNumbers"
            :key="p"
            class="page-btn"
            :class="{ active: p === page }"
            @click="goToPage(p)"
          >
            {{ p }}
          </button>
          <button class="page-btn" :disabled="page === totalPages" @click="goToPage(page + 1)">›</button>

          <select v-model.number="pageSize" class="page-size" @change="loadData">
            <option :value="10">10 / page</option>
            <option :value="25">25 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </footer>
    </div>

    <!-- ── View Detail Modal ─────────────────────────────── -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="viewModal.open" class="modal-backdrop" @click.self="viewModal.open = false">
          <div class="modal-box">
            <div class="modal-header">
              <h2>{{ viewModal.data?.mockexam_name }}</h2>
              <button class="modal-close" @click="viewModal.open = false">✕</button>
            </div>
            <div v-if="viewModal.loading" class="modal-loading">Loading details…</div>
            <div v-else-if="viewModal.data" class="modal-body">
              <div class="detail-grid">
                <div class="detail-item"><span class="detail-label">Exam</span><span>{{ viewModal.data.exam_name || viewModal.data.exam_code || '—' }}</span></div>
                <div class="detail-item"><span class="detail-label">Exam Type</span><span>{{ viewModal.data.exam_type_name || '—' }}</span></div>
                <div class="detail-item"><span class="detail-label">Year</span><span>{{ viewModal.data.year || '—' }}</span></div>
                <div class="detail-item"><span class="detail-label">Total Marks</span><span>{{ viewModal.data.total_marks ?? '—' }}</span></div>
                <div class="detail-item"><span class="detail-label">Duration</span><span>{{ viewModal.data.duration_minutes ? viewModal.data.duration_minutes + ' min' : '—' }}</span></div>
                <div class="detail-item"><span class="detail-label">Questions</span><span>{{ viewModal.data.question_count ?? '—' }}</span></div>
                <div class="detail-item"><span class="detail-label">Status</span>
                  <span class="status-pill" :class="viewModal.data.is_active ? 'status-published' : 'status-draft'">
                    {{ viewModal.data.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
                <div class="detail-item"><span class="detail-label">Created On</span><span>{{ formatDate(viewModal.data.created_at) }}</span></div>
              </div>

              <!-- Subjects breakdown -->
              <div v-if="viewModal.data.subjects_detail?.length" class="subjects-section">
                <p class="subjects-title">Subjects</p>
                <table class="subjects-table">
                  <thead><tr><th>Subject</th><th>Planned Q</th><th>Planned Marks</th><th>Uploaded Q</th></tr></thead>
                  <tbody>
                    <tr v-for="s in viewModal.data.subjects_detail" :key="s.name">
                      <td>{{ s.name }}</td>
                      <td>{{ s.planned_questions }}</td>
                      <td>{{ s.planned_marks }}</td>
                      <td>{{ s.uploaded_questions }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="modal-footer">
                <button class="btn-secondary" @click="viewModal.open = false">Close</button>
                <button class="btn-primary" @click="onEdit(viewModal.data); viewModal.open = false">Edit</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Delete Confirm Modal ──────────────────────────── -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="deleteModal.open" class="modal-backdrop" @click.self="deleteModal.open = false">
          <div class="modal-box modal-box--sm">
            <div class="modal-header">
              <h2>Delete Mock Test</h2>
              <button class="modal-close" @click="deleteModal.open = false">✕</button>
            </div>
            <div class="modal-body">
              <p class="delete-warn">
                <strong>"{{ deleteModal.name }}"</strong> has
                <strong>{{ deleteModal.questionCount }} question(s)</strong> linked to it.
                Deleting will permanently remove them too.
              </p>
              <div class="modal-footer">
                <button class="btn-secondary" @click="deleteModal.open = false">Cancel</button>
                <button class="btn-danger" :disabled="deleteModal.confirming" @click="confirmForceDelete">
                  {{ deleteModal.confirming ? 'Deleting…' : 'Yes, Delete All' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Success notification after creating a mock test -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div v-if="showToast" class="success-toast" role="status" aria-live="polite">
          <span class="toast-icon">✓</span>
          <div class="toast-text">
            <strong>Mock test created successfully</strong>
            <span>{{ toastName }} has been added to your mock tests.</span>
          </div>
          <button class="toast-close" aria-label="Dismiss" @click="showToast = false">✕</button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  listMockExams,
  fetchMockExamStats,
  fetchExamTypes,
  fetchExamCategories,
  deleteMockExam,
  fetchMockExamDetail,
  toggleMockExamStatus,
  type MockExam,
  type MockExamDetail,
  type MockExamDeleteConflict,
  type ExamType,
  type ExamCategory,
} from '@/services/mocktestapi'

const router = useRouter()
const route = useRoute()

const rows = ref<MockExam[]>([])
const total = ref(0)
const loading = ref(false)

const page = ref(1)
const pageSize = ref(10)
const search = ref('')

const examTypes = ref<ExamType[]>([])
const examCategories = ref<ExamCategory[]>([])

const filters = reactive({ examType: '', category: '', status: '' })

const stats = reactive({ total: 0, published: 0, draft: 0, archived: 0 })

const showToast = ref(false)
const toastName = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null
let searchDebounce: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const rangeStart = computed(() => (total.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const rangeEnd = computed(() => Math.min(page.value * pageSize.value, total.value))
const pageNumbers = computed(() => {
  const pages: number[] = []
  const maxShown = 3
  let start = Math.max(1, page.value - 1)
  let end = Math.min(totalPages.value, start + maxShown - 1)
  start = Math.max(1, end - maxShown + 1)
  for (let p = start; p <= end; p++) pages.push(p)
  return pages
})

function typeTagClass(name?: string) {
  if (!name) return ''
  return name.toLowerCase() === 'job' ? 'tag-blue' : 'tag-purple'
}

// Your /mockexams/ API returns is_active, so the row pill is a simple
// Active/Inactive reflection of that flag.
function statusLabel(row: MockExam) {
  return row.is_active ? 'Active' : 'Inactive'
}
function statusClass(row: MockExam) {
  return row.is_active ? 'status-published' : 'status-draft'
}
function formatDate(value?: string) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
}

const loadError = ref('')

async function loadData() {
  loading.value = true
  loadError.value = ''
  try {
    const { results, count } = await listMockExams({
      page: page.value,
      page_size: pageSize.value,
      search: search.value || undefined,
      exam_type: filters.examType || undefined,
      category_id: filters.category || undefined,
      status: filters.status || undefined,
    })
    rows.value = results
    total.value = count
  } catch (err: any) {
    console.error('listMockExams failed:', err?.response?.status, err?.response?.data || err)
    rows.value = []
    total.value = 0
    loadError.value =
      err?.response?.status === 404
        ? 'Mock tests endpoint not found (check the API path in mockTestApi.ts).'
        : err?.response?.status === 401 || err?.response?.status === 403
          ? 'Not authorized to load mock tests (check auth token).'
          : 'Could not load mock tests from the server.'
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const s = await fetchMockExamStats()
    Object.assign(stats, s)
    return
  } catch {
    // /api/mockexams/stats/ not implemented yet — silently fall through
    // to the computed-counts fallback below.
  }

  // Fallback: your backend doesn't have a /mockexams/stats/ endpoint
  // (yet), so derive the same 3 numbers from listMockExams() itself —
  // one lightweight request per bucket (page_size 1, we only need count).
  try {
    const [all, active, inactive] = await Promise.all([
      listMockExams({ page_size: 1 }),
      listMockExams({ page_size: 1, status: 'Active' }),
      listMockExams({ page_size: 1, status: 'Inactive' }),
    ])
    stats.total = all.count
    stats.published = active.count
    stats.draft = inactive.count
    stats.archived = 0
  } catch (err: any) {
    console.error('Stats fallback also failed:', err?.response?.status || err)
  }
}

function onSearchInput() {
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    page.value = 1
    loadData()
  }, 350)
}

function resetFilters() {
  search.value = ''
  filters.examType = ''
  filters.category = ''
  filters.status = ''
  page.value = 1
  loadData()
}

function goToPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  loadData()
}

function goToCreate() {
  router.push({ name: 'admin-mock-test-create' })
}

// ── View ──────────────────────────────────────────────────
const viewModal = reactive<{
  open: boolean
  loading: boolean
  data: MockExamDetail | null
}>({ open: false, loading: false, data: null })

async function onView(row: MockExam) {
  viewModal.open = true
  viewModal.loading = true
  viewModal.data = null
  try {
    viewModal.data = await fetchMockExamDetail(row.mockexam_id)
  } catch {
    viewModal.data = { ...row, subjects_detail: [] } as MockExamDetail
  } finally {
    viewModal.loading = false
  }
}

// ── Edit ──────────────────────────────────────────────────
function onEdit(row: MockExam) {
  // Navigate to the create/edit wizard.
  // Uses the same route as "Create Mock Test" — pass the mockexam_id as a
  // query param so the wizard knows to load an existing test instead of
  // creating a new one: /tests/mock/create?edit=<id>
  // Change 'admin-mock-test-create' below to your actual edit route name if
  // you have a separate one defined in your router.
  router.push({ name: 'admin-mock-test-create', query: { edit: String(row.mockexam_id) } })
}

// ── Delete ────────────────────────────────────────────────
const deletingId = ref<number | null>(null)

const deleteModal = reactive<{
  open: boolean
  confirming: boolean
  id: number | null
  name: string
  questionCount: number
}>({ open: false, confirming: false, id: null, name: '', questionCount: 0 })

async function onDelete(row: MockExam) {
  deletingId.value = row.mockexam_id
  try {
    const result = await deleteMockExam(row.mockexam_id)
    if (result.deleted) {
      // No questions — deleted immediately
      await Promise.all([loadData(), loadStats()])
    } else {
      // Has questions — show confirmation modal
      const conflict = result.conflict as MockExamDeleteConflict
      deleteModal.id = row.mockexam_id
      deleteModal.name = conflict.mockexam_name
      deleteModal.questionCount = conflict.question_count
      deleteModal.open = true
    }
  } catch {
    window.alert('Could not delete this mock test. Please try again.')
  } finally {
    deletingId.value = null
  }
}

async function confirmForceDelete() {
  if (!deleteModal.id) return
  deleteModal.confirming = true
  try {
    await deleteMockExam(deleteModal.id, true)
    deleteModal.open = false
    await Promise.all([loadData(), loadStats()])
  } catch {
    window.alert('Force delete failed. Please try again.')
  } finally {
    deleteModal.confirming = false
  }
}

// ── Toggle Status (status pill click) ────────────────────
async function onToggleStatus(row: MockExam) {
  try {
    const result = await toggleMockExamStatus(row.mockexam_id)
    Object.assign(row, result.row)
  } catch {
    window.alert('Could not update status. Please try again.')
  }
}

function showCreatedToast(name: string) {
  toastName.value = name || 'Your mock test'
  showToast.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (showToast.value = false), 4000)
}

// If we arrived here right after the create wizard finished, show the
// success notification and clean the query string so a refresh doesn't
// re-trigger it.
onMounted(async () => {
  if (route.query.created === '1') {
    showCreatedToast(String(route.query.name || ''))
    router.replace({ name: 'admin-tests-mock' })
  }
  const [types] = await Promise.all([fetchExamTypes(), loadStats(), loadData()])
  examTypes.value = types
})

watch(
  () => filters.examType,
  async (val) => {
    filters.category = ''
    examCategories.value = val ? await fetchExamCategories(val) : []
  },
)
</script>

<style scoped>
.page { max-width: 1400px; margin: 0 auto; padding: 28px 32px 60px; }
.page-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; }
.page-head h1 { font-size: 22px; margin: 0 0 4px; color: #1f2333; }
.page-head p { font-size: 13px; color: #8a8fa3; margin: 0; }
.btn-primary { background: #6d28d9; color: #fff; border: none; padding: 11px 20px; border-radius: 8px; font-size: 13.5px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #5b21b6; }

.stat-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-bottom: 20px; }
.stat-card { background: #fff; border: 1px solid #ecedf3; border-radius: 12px; padding: 20px; display: flex; gap: 14px; align-items: flex-start; }
.stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.stat-icon.purple { background: #f2effe; }
.stat-icon.green { background: #e8fbf0; }
.stat-icon.amber { background: #fef6e6; }
.stat-icon.red { background: #fdeaea; }
.stat-label { font-size: 12px; color: #8a8fa3; margin: 0 0 4px; }
.stat-value { font-size: 22px; font-weight: 700; color: #1f2333; margin: 0; }
.stat-sub { font-size: 11.5px; color: #a6abc0; margin: 2px 0 0; }

.table-card { background: #fff; border: 1px solid #ecedf3; border-radius: 12px; padding: 20px 22px 8px; }
.filters-row { display: flex; align-items: flex-end; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.search-box { position: relative; flex: 1 1 240px; min-width: 200px; }
.search-box input { width: 100%; border: 1px solid #dfe1ea; border-radius: 8px; padding: 9px 12px 9px 32px; font-size: 13px; outline: none; }
.search-box input:focus { border-color: #a78bfa; box-shadow: 0 0 0 3px #ede9fe; }
.search-icon { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); font-size: 12px; opacity: 0.5; }
.filter-field { display: flex; flex-direction: column; gap: 5px; }
.filter-field label { font-size: 11.5px; font-weight: 600; color: #8a8fa3; }
.filter-field select { border: 1px solid #dfe1ea; border-radius: 8px; padding: 8px 30px 8px 12px; font-size: 13px; min-width: 150px; background: #fff; }
.btn-reset { border: 1px solid #dfe1ea; background: #fff; border-radius: 8px; padding: 9px 16px; font-size: 13px; font-weight: 600; color: #4b4f66; cursor: pointer; height: 37px; }
.btn-reset:hover { background: #f6f7fb; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align: left; color: #a6abc0; font-weight: 600; padding: 10px 10px; border-bottom: 1px solid #ecedf3; white-space: nowrap; }
td { padding: 12px 10px; border-bottom: 1px solid #f3f3f8; color: #1f2333; white-space: nowrap; }
.name-cell { font-weight: 600; }
.empty-cell { text-align: center; color: #a6abc0; padding: 30px; white-space: normal; }
.error-cell { color: #dc2626; font-weight: 600; }

.tag { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.tag-purple { background: #f2effe; color: #6d28d9; }
.tag-blue { background: #eaf1ff; color: #2563eb; }

.status-pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.status-published { background: #dcfce7; color: #16a34a; }
.status-draft { background: #fef3c7; color: #d97706; }
.status-archived { background: #fee2e2; color: #dc2626; }

.row-actions { display: flex; gap: 6px; }
.icon-btn { border: 1px solid #ecedf3; background: #fff; border-radius: 6px; width: 28px; height: 28px; cursor: pointer; font-size: 12px; color: #4b4f66; }
.icon-btn:hover { background: #f6f7fb; }

.table-foot { display: flex; justify-content: space-between; align-items: center; padding: 16px 4px; font-size: 12.5px; color: #8a8fa3; }
.pagination { display: flex; align-items: center; gap: 6px; }
.page-btn { border: 1px solid #dfe1ea; background: #fff; border-radius: 7px; width: 30px; height: 30px; font-size: 12.5px; cursor: pointer; color: #4b4f66; }
.page-btn.active { background: #6d28d9; border-color: #6d28d9; color: #fff; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-size { border: 1px solid #dfe1ea; border-radius: 7px; padding: 6px 10px; font-size: 12.5px; margin-left: 8px; background: #fff; }

.success-toast {
  position: fixed; bottom: 28px; right: 28px; z-index: 1000;
  display: flex; align-items: flex-start; gap: 12px;
  background: #16a34a; color: #fff; padding: 14px 16px; border-radius: 10px;
  box-shadow: 0 12px 32px rgba(22, 163, 74, 0.28); max-width: 340px;
}
.toast-icon {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
  background: rgba(255, 255, 255, 0.22); display: flex; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700;
}
.toast-text { display: flex; flex-direction: column; gap: 2px; }
.toast-text strong { font-size: 13px; font-weight: 700; }
.toast-text span { font-size: 12px; opacity: 0.92; }
.toast-close { margin-left: auto; background: none; border: none; color: #fff; opacity: 0.75; cursor: pointer; font-size: 12px; padding: 2px; flex-shrink: 0; }
.toast-close:hover { opacity: 1; }

.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateY(8px); }

/* ── Modals ─────────────────────────────────────────────── */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-box { background: #fff; border-radius: 14px; width: 100%; max-width: 640px; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.18); }
.modal-box--sm { max-width: 420px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px 0; }
.modal-header h2 { font-size: 16px; font-weight: 700; color: #1f2333; margin: 0; }
.modal-close { background: none; border: none; font-size: 16px; cursor: pointer; color: #8a8fa3; padding: 4px; }
.modal-close:hover { color: #1f2333; }
.modal-loading { padding: 40px; text-align: center; color: #8a8fa3; font-size: 13px; }
.modal-body { padding: 20px 24px 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px; }
.detail-item { display: flex; flex-direction: column; gap: 3px; }
.detail-label { font-size: 11px; font-weight: 600; color: #8a8fa3; text-transform: uppercase; letter-spacing: 0.5px; }
.detail-item span:last-child { font-size: 13.5px; color: #1f2333; font-weight: 500; }
.subjects-section { border-top: 1px solid #ecedf3; padding-top: 16px; }
.subjects-title { font-size: 13px; font-weight: 700; color: #1f2333; margin: 0 0 10px; }
.subjects-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.subjects-table th { text-align: left; color: #8a8fa3; font-weight: 600; padding: 6px 8px; border-bottom: 1px solid #ecedf3; }
.subjects-table td { padding: 8px 8px; border-bottom: 1px solid #f3f3f8; color: #1f2333; }
.btn-secondary { border: 1px solid #dfe1ea; background: #fff; border-radius: 8px; padding: 9px 18px; font-size: 13px; font-weight: 600; color: #4b4f66; cursor: pointer; }
.btn-secondary:hover { background: #f6f7fb; }
.btn-danger { background: #dc2626; color: #fff; border: none; padding: 9px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.delete-warn { font-size: 13.5px; color: #1f2333; line-height: 1.6; margin: 0; }
.delete-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>