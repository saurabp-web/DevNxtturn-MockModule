<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'
const router = useRouter()
const route  = useRoute()

// ── success toast (shown after "Create Test" in the PYQ wizard) ──
const toast = ref({ show: false, message: '' })
let toastTimer = null
function showToast(message) {
  toast.value = { show: true, message }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 5000)
}
function checkCreated() {
  if (route.query.created) {
    showToast('PYQ Test has been created successfully')
    // drop ?created so a refresh doesn't show the toast again
    const { created, ...rest } = route.query
    router.replace({ query: rest })
  }
}

// ── loading / error ───────────────────────────────────
const loadingStats = ref(true)
const loadingTests = ref(true)
const error        = ref(null)

// ── filter state ──────────────────────────────────────
const filterExam     = ref('')
const filterYear     = ref('')
const filterTestType = ref('Mock')
const filterStatus   = ref('')
const filterSearch   = ref('')
const pageSize       = ref(10)
const currentPage    = ref(1)

// ── stats ─────────────────────────────────────────────
const rawStats = ref({
  total: 0, published: 0, draft: 0, archived: 0,
  delta_total: 0, delta_published: 0, delta_draft: 0, delta_archived: 0,
})

const stats = computed(() => [
  {
    label: 'Total PYQ Sources',
    value: rawStats.value.total,
    delta: formatDelta(rawStats.value.delta_total),
    icon: 'doc',
    tint: 'violet',
    pos: rawStats.value.delta_total > 0,
  },
  {
    label: 'Total Questions',
    value: rawStats.value.published,
    delta: formatDelta(rawStats.value.delta_published),
    icon: 'check',
    tint: 'emerald',
    pos: rawStats.value.delta_published > 0,
  },
  {
    label: 'Total Tests',
    value: rawStats.value.draft,
    delta: formatDelta(rawStats.value.delta_draft),
    icon: 'tests',
    tint: 'blue',
    pos: rawStats.value.delta_draft > 0,
  },
  {
    label: 'Archived',
    value: rawStats.value.archived,
    delta: formatDelta(rawStats.value.delta_archived),
    icon: 'archive',
    tint: 'amber',
    pos: false,
  },
])

function formatDelta(n) {
  return n > 0 ? `+${n} this week` : `+0 this week`
}

// ── table data ────────────────────────────────────────
const tests      = ref([])
const totalCount = ref(0)

const totalPages  = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
const showingFrom = computed(() => totalCount.value === 0 ? 0 : (currentPage.value - 1) * pageSize.value + 1)
const showingTo   = computed(() => Math.min(currentPage.value * pageSize.value, totalCount.value))

// ── fetch stats ───────────────────────────────────────
async function fetchStats() {
  loadingStats.value = true
  error.value = null
  try {
    const res = await fetch(`${API_BASE}/pyq/stats/`)
    if (!res.ok) throw new Error(`Stats API error: ${res.status}`)
    rawStats.value = await res.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loadingStats.value = false
  }
}

// ── fetch tests ───────────────────────────────────────
async function fetchTests(page = 1) {
  loadingTests.value = true
  currentPage.value = page
  try {
    const params = new URLSearchParams({ page, page_size: pageSize.value })
    if (filterExam.value)     params.set('exam',      filterExam.value)
    if (filterYear.value)     params.set('year',      filterYear.value)
    if (filterTestType.value) params.set('test_type', filterTestType.value)
    if (filterStatus.value)   params.set('status',    filterStatus.value)
    if (filterSearch.value)   params.set('search',    filterSearch.value)

    const res = await fetch(`${API_BASE}/pyq/tests/?${params}`)
    if (!res.ok) throw new Error(`Tests API error: ${res.status}`)
    const data       = await res.json()
    tests.value      = data.results ?? []
    totalCount.value = data.count   ?? 0
  } catch (e) {
    error.value = e.message
    tests.value = []
  } finally {
    loadingTests.value = false
  }
}

function applyFilters() { fetchTests(1) }

function resetFilters() {
  filterExam.value = ''
  filterYear.value = ''
  filterTestType.value = 'Mock'
  filterStatus.value = ''
  filterSearch.value = ''
  fetchTests(1)
}

onMounted(() => { checkCreated(); fetchStats(); fetchTests(1) })

// ── pagination ────────────────────────────────────────
function goPage(p) {
  if (p < 1 || p > totalPages.value) return
  fetchTests(p)
}

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur   = currentPage.value
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 3)   return [1, 2, 3, 4, '...', total]
  if (cur >= total - 2) return [1, '...', total - 3, total - 2, total - 1, total]
  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

// ── checkboxes ────────────────────────────────────────
const selectedIds = ref(new Set())
const allChecked  = computed(() =>
  tests.value.length > 0 && tests.value.every(t => selectedIds.value.has(t.id))
)
function toggleAll() {
  if (allChecked.value) tests.value.forEach(t => selectedIds.value.delete(t.id))
  else tests.value.forEach(t => selectedIds.value.add(t.id))
  selectedIds.value = new Set(selectedIds.value)
}
function toggleRow(id) {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

// ── action menu ───────────────────────────────────────
const openMenuFor = ref(null)
function toggleMenu(id, e) {
  e.stopPropagation()
  openMenuFor.value = openMenuFor.value === id ? null : id
}
function closeMenu() { openMenuFor.value = null }

// ── nav ───────────────────────────────────────────────
function goAdd() { router.push({ name: 'admin-tests-previous-upload' }) }
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-6" @click="closeMenu">

    <!-- Success toast -->
    <transition name="fade">
      <div
        v-if="toast.show"
        class="fixed right-6 top-6 z-50 flex items-center gap-3 rounded-xl border border-emerald-200 bg-white px-4 py-3 shadow-lg"
        role="status"
      >
        <span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
        </span>
        <span class="text-sm font-medium text-gray-800">{{ toast.message }}</span>
        <button class="ml-2 text-gray-400 hover:text-gray-600" @click="toast.show = false">✕</button>
      </div>
    </transition>

    <!-- ═══════════════════════════════════════════════════
         1. HEADER
    ════════════════════════════════════════════════════ -->
    <div class="mb-5 flex items-start justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Previous Year Tests</h1>
        <p class="mt-0.5 text-xs text-gray-500">Manage and organize previous year question papers and tests.</p>
      </div>
      <button
        class="flex items-center gap-1.5 rounded-lg bg-[#6C4CF1] px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-[#5B3EE0] transition-colors"
        @click="goAdd"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Add PYQ Source
      </button>
    </div>

    <!-- Error banner -->
    <div v-if="error" class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">
      ⚠ {{ error }}
    </div>

    <!-- ═══════════════════════════════════════════════════
         2. STAT CARDS  (shown first)
    ════════════════════════════════════════════════════ -->
    <div class="mb-5 grid grid-cols-4 gap-4">
      <div
        v-for="s in stats"
        :key="s.label"
        class="flex items-center gap-4 rounded-xl border border-gray-200 bg-white px-5 py-4"
      >
        <!-- icon circle -->
        <div
          class="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full"
          :class="{
            'bg-violet-100 text-violet-600':  s.tint === 'violet',
            'bg-emerald-100 text-emerald-600': s.tint === 'emerald',
            'bg-blue-100 text-blue-600':       s.tint === 'blue',
            'bg-amber-100 text-amber-600':     s.tint === 'amber',
          }"
        >
          <svg v-if="s.icon === 'doc'"   width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <svg v-else-if="s.icon === 'check'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <svg v-else-if="s.icon === 'tests'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="9" y1="7" x2="15" y2="7"/><line x1="9" y1="11" x2="15" y2="11"/><line x1="9" y1="15" x2="13" y2="15"/></svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="4" rx="1"/><path d="M4 7v13a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7"/><line x1="10" y1="13" x2="14" y2="13"/></svg>
        </div>

        <!-- text -->
        <div>
          <p class="text-[11px] font-medium text-gray-500">{{ s.label }}</p>
          <div v-if="loadingStats" class="mt-1 h-7 w-14 animate-pulse rounded bg-gray-100" />
          <p v-else class="text-2xl font-bold leading-tight text-gray-900">{{ s.value.toLocaleString() }}</p>
          <div v-if="loadingStats" class="mt-1 h-3 w-20 animate-pulse rounded bg-gray-100" />
          <p v-else class="mt-0.5 text-[11px] font-medium" :class="s.pos ? 'text-emerald-500' : 'text-gray-400'">
            {{ s.delta }}
          </p>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════
         3. FILTER BAR  (shown second)
    ════════════════════════════════════════════════════ -->
    <div class="mb-5 rounded-xl border border-gray-200 bg-white px-4 py-4">
      <!-- Row 1: dropdowns + search -->
      <div class="flex flex-wrap items-end gap-3">

        <!-- Exam Name -->
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-500">Exam Name</label>
          <div class="relative">
            <select v-model="filterExam" class="h-8 min-w-[140px] appearance-none rounded-lg border border-gray-200 bg-white pl-3 pr-7 text-xs text-gray-700 focus:border-[#6C4CF1] focus:outline-none">
              <option value="">All Exams</option>
              <option value="JEE Main">JEE Main</option>
              <option value="NEET UG">NEET UG</option>
              <option value="GATE">GATE</option>
              <option value="UPSC CSE">UPSC CSE</option>
            </select>
            <svg class="pointer-events-none absolute right-2 top-2 text-gray-400" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Exam Year -->
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-500">Exam Year</label>
          <div class="relative">
            <select v-model="filterYear" class="h-8 min-w-[110px] appearance-none rounded-lg border border-gray-200 bg-white pl-3 pr-7 text-xs text-gray-700 focus:border-[#6C4CF1] focus:outline-none">
              <option value="">All Years</option>
              <option v-for="y in [2025,2024,2023,2022,2021,2020]" :key="y" :value="y">{{ y }}</option>
            </select>
            <svg class="pointer-events-none absolute right-2 top-2 text-gray-400" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Test Type -->
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-500">Test Type</label>
          <div class="relative">
            <select v-model="filterTestType" class="h-8 min-w-[110px] appearance-none rounded-lg border border-gray-200 bg-white pl-3 pr-7 text-xs text-gray-700 focus:border-[#6C4CF1] focus:outline-none">
              <option value="Mock">Mock</option>
              <option value="Practice">Practice</option>
              <option value="Custom">Custom</option>
            </select>
            <svg class="pointer-events-none absolute right-2 top-2 text-gray-400" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Status -->
        <div class="flex flex-col gap-1">
          <label class="text-[11px] font-medium text-gray-500">Status</label>
          <div class="relative">
            <select v-model="filterStatus" class="h-8 min-w-[120px] appearance-none rounded-lg border border-gray-200 bg-white pl-3 pr-7 text-xs text-gray-700 focus:border-[#6C4CF1] focus:outline-none">
              <option value="">All Status</option>
              <option value="Published">Published</option>
              <option value="Draft">Draft</option>
              <option value="Archived">Archived</option>
            </select>
            <svg class="pointer-events-none absolute right-2 top-2 text-gray-400" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>

        <!-- Search -->
        <div class="flex flex-1 flex-col gap-1 min-w-[200px]">
          <label class="text-[11px] font-medium text-gray-500">&nbsp;</label>
          <div class="relative">
            <svg class="pointer-events-none absolute left-2.5 top-2 text-gray-400" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="filterSearch"
              type="text"
              placeholder="Search by exam name or year..."
              class="h-8 w-full rounded-lg border border-gray-200 bg-white pl-8 pr-3 text-xs text-gray-700 placeholder-gray-400 focus:border-[#6C4CF1] focus:outline-none"
              @keyup.enter="applyFilters"
            />
          </div>
        </div>
      </div>

      <!-- Row 2: action buttons -->
      <div class="mt-3 flex gap-2">
        <button
          class="flex h-8 items-center gap-1.5 rounded-lg bg-[#6C4CF1] px-4 text-xs font-semibold text-white hover:bg-[#5B3EE0] transition-colors"
          @click="applyFilters"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
          Apply Filters
        </button>
        <button
          class="flex h-8 items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-4 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          @click="resetFilters"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/></svg>
          Reset
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════
         4. TABLE
    ════════════════════════════════════════════════════ -->
    <div class="rounded-xl border border-gray-200 bg-white">

      <!-- top bar: count + show/page controls -->
      <div class="flex items-center justify-between border-b border-gray-100 px-5 py-3">
        <p class="text-xs text-gray-500">
          <template v-if="!loadingTests && totalCount > 0">
            Showing {{ showingFrom }}–{{ showingTo }} of {{ totalCount }} results
          </template>
        </p>
        <div class="flex items-center gap-2 text-xs text-gray-500">
          Show:
          <select
            v-model="pageSize"
            class="h-7 rounded-md border border-gray-200 px-2 text-xs text-gray-700 focus:outline-none"
            @change="fetchTests(1)"
          >
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
          <button class="rounded p-1 hover:bg-gray-100 disabled:opacity-30 transition-colors" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <button class="rounded p-1 hover:bg-gray-100 disabled:opacity-30 transition-colors" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
      </div>

      <!-- table -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="border-b border-gray-100 bg-gray-50/60 text-gray-500">
              <th class="w-10 px-4 py-3">
                <input type="checkbox" class="rounded border-gray-300 accent-[#6C4CF1]" :checked="allChecked" @change="toggleAll" />
              </th>
              <th class="w-10 px-2 py-3 font-medium">#</th>
              <th class="px-4 py-3 font-medium">
                <span class="flex items-center gap-1 cursor-pointer select-none">
                  Exam Name
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                </span>
              </th>
              <th class="px-4 py-3 font-medium">Exam Year</th>
              <th class="px-4 py-3 font-medium">Total Questions</th>
              <th class="px-4 py-3 font-medium">
                <span class="flex items-center gap-1 cursor-pointer select-none">
                  Test Type
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                </span>
              </th>
              <th class="px-4 py-3 font-medium">
                <span class="flex items-center gap-1 cursor-pointer select-none">
                  Question Used In
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                </span>
              </th>
              <th class="px-4 py-3 font-medium">Status</th>
              <th class="px-4 py-3 font-medium">
                <span class="flex items-center gap-1 cursor-pointer select-none">
                  Updated On
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                </span>
              </th>
              <th class="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>

          <tbody>
            <!-- skeleton rows -->
            <template v-if="loadingTests">
              <tr v-for="i in Number(pageSize)" :key="i" class="border-b border-gray-50">
                <td v-for="c in 10" :key="c" class="px-4 py-3.5">
                  <div class="h-3 animate-pulse rounded bg-gray-100" :style="{ width: c === 2 ? '20px' : c === 8 ? '60px' : '80%' }" />
                </td>
              </tr>
            </template>

            <!-- empty state -->
            <tr v-else-if="tests.length === 0">
              <td colspan="10" class="py-16 text-center">
                <div class="flex flex-col items-center gap-3 text-gray-400">
                  <div class="flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-gray-600">No previous year tests found</p>
                    <p class="mt-0.5 text-xs text-gray-400">Click <span class="font-semibold text-[#6C4CF1]">+ Add PYQ Source</span> to import one.</p>
                  </div>
                </div>
              </td>
            </tr>

            <!-- data rows -->
            <tr
              v-else
              v-for="(t, idx) in tests"
              :key="t.id"
              class="border-b border-gray-50 last:border-0 hover:bg-gray-50/70 transition-colors"
            >
              <td class="px-4 py-3.5">
                <input type="checkbox" class="rounded border-gray-300 accent-[#6C4CF1]" :checked="selectedIds.has(t.id)" @change="toggleRow(t.id)" />
              </td>
              <td class="px-2 py-3.5 font-semibold text-gray-400">
                {{ (currentPage - 1) * Number(pageSize) + idx + 1 }}
              </td>
              <td class="px-4 py-3.5 font-semibold text-gray-900">{{ t.name }}</td>
              <td class="px-4 py-3.5 text-gray-500">{{ t.year ?? '—' }}</td>
              <td class="px-4 py-3.5 text-gray-600">{{ t.questions }}</td>
              <td class="px-4 py-3.5">
                <span class="rounded-full bg-violet-100 px-2.5 py-0.5 text-[11px] font-medium text-violet-700">
                  {{ t.test_type ?? 'Mock' }}
                </span>
              </td>
              <td class="px-4 py-3.5">
                <div class="flex flex-wrap gap-1">
                  <span v-if="t.used_in_practice" class="rounded-full bg-blue-100 px-2.5 py-0.5 text-[11px] font-medium text-blue-700">Practice</span>
                  <span v-if="t.used_in_custom"   class="rounded-full bg-amber-100 px-2.5 py-0.5 text-[11px] font-medium text-amber-700">Custom</span>
                  <span v-if="!t.used_in_practice && !t.used_in_custom" class="text-gray-300">—</span>
                </div>
              </td>
              <td class="px-4 py-3.5">
                <div class="flex items-center gap-1.5">
                  <span class="h-1.5 w-1.5 flex-shrink-0 rounded-full"
                    :class="{
                      'bg-emerald-500': t.status === 'Published',
                      'bg-amber-400':   t.status === 'Draft',
                      'bg-gray-400':    t.status === 'Archived',
                    }"
                  />
                  <span class="text-[11px] font-semibold"
                    :class="{
                      'text-emerald-600': t.status === 'Published',
                      'text-amber-600':   t.status === 'Draft',
                      'text-gray-500':    t.status === 'Archived',
                    }"
                  >{{ t.status }}</span>
                </div>
              </td>
              <td class="px-4 py-3.5 text-gray-500">{{ t.updated }}</td>
              <td class="relative px-4 py-3.5">
                <button
                  class="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                  @click="(e) => toggleMenu(t.id, e)"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="5"  r="1.5"/>
                    <circle cx="12" cy="12" r="1.5"/>
                    <circle cx="12" cy="19" r="1.5"/>
                  </svg>
                </button>
                <Transition name="fade">
                  <div
                    v-if="openMenuFor === t.id"
                    class="absolute right-4 top-10 z-20 w-36 rounded-xl border border-gray-100 bg-white py-1 shadow-xl"
                    @click.stop
                  >
                    <button class="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-gray-700 hover:bg-gray-50">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      View
                    </button>
                    <button class="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-gray-700 hover:bg-gray-50">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      Edit
                    </button>
                    <div class="my-1 border-t border-gray-100" />
                    <button class="flex w-full items-center gap-2 px-3 py-2 text-left text-xs text-red-500 hover:bg-red-50">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="4" rx="1"/><path d="M4 7v13a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7"/></svg>
                      Archive
                    </button>
                  </div>
                </Transition>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- pagination footer -->
      <div class="flex items-center justify-between border-t border-gray-100 px-5 py-3.5">
        <p class="text-xs text-gray-500">
          <template v-if="!loadingTests && totalCount > 0">
            Showing {{ showingFrom }} to {{ showingTo }} of {{ totalCount }} results
          </template>
          <template v-else-if="!loadingTests">No results</template>
        </p>

        <div class="flex items-center gap-1">
          <button
            class="flex h-7 w-7 items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-30 transition-colors"
            :disabled="currentPage <= 1"
            @click="goPage(currentPage - 1)"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          </button>

          <template v-for="p in visiblePages" :key="String(p)">
            <span v-if="p === '...'" class="flex h-7 w-7 items-center justify-center text-xs text-gray-400">…</span>
            <button
              v-else
              class="flex h-7 w-7 items-center justify-center rounded-md text-xs font-semibold transition-colors"
              :class="p === currentPage
                ? 'bg-[#6C4CF1] text-white shadow-sm'
                : 'border border-gray-200 text-gray-600 hover:bg-gray-50'"
              @click="goPage(p)"
            >{{ p }}</button>
          </template>

          <button
            class="flex h-7 w-7 items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-30 transition-colors"
            :disabled="currentPage >= totalPages"
            @click="goPage(currentPage + 1)"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>