<template>
  <div class="exam-page">

    <!-- ── Top Filter Bar (matches the image: tabs left, search right) ── -->
    <div class="top-filter-bar">
      <div class="top-filter-bar-inner">
        <div class="top-filter-left">
          <svg class="top-filter-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z"/>
            <path d="M9 21V12h6v9"/>
          </svg>
          <span class="top-filter-label">Home</span>
          <div class="top-tab-pills">
            <button
              v-for="tab in EXAM_TABS"
              :key="tab.value"
              type="button"
              class="top-tab-pill"
              :class="{ 'top-tab-pill--active': activeExamTab === tab.value }"
              @click="onExamTabSelect(tab.value)"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>
        <div class="top-filter-right">
          <div class="top-search-bar">
            <svg class="top-search-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search exams (e.g., JEE, NEET, UPSC, GATE, CLAT...)"
              class="top-search-input"
            />
          </div>
          <button class="top-search-btn">Search</button>
        </div>
      </div>
    </div>

    <div class="exam-page-grid">
      <!-- ── Left: Filters Sidebar ── -->
      <Sidebar ref="sidebarRef" @change="onFilterChange" @apply="scrollToFilteredResults" />

      <!-- ── Centre: Main content ── -->
      <div class="exam-page-main">

        <!-- Search Results -->
        <div class="content-card filtered-results-section" v-if="hasSearchQuery">
          <div class="card-header-row">
            <div>
              <h3 class="section-heading">🔍 Search Results</h3>
              <p class="section-sub">
                {{ searchResultExams.length }} exam{{ searchResultExams.length === 1 ? '' : 's' }} match "{{ searchQuery }}"
              </p>
            </div>
            <button class="view-all-btn" @click="clearSearch">Clear Search</button>
          </div>
          <div class="popular-grid" v-if="searchResultExams.length">
            <div
              v-for="exam in searchResultExams"
              :key="exam.id"
              class="popular-card"
              @click="goToExam(exam.id)"
            >
              <div class="popular-icon">
                <img v-if="exam.logo" :src="exam.logo" :alt="exam.label" class="popular-icon-img" loading="lazy" @error="onLogoError" />
                <span v-else class="popular-icon-fallback">{{ getExamInitials(exam.label) }}</span>
              </div>
              <h4 class="popular-name">{{ exam.label }}</h4>
              <p class="popular-desc">{{ exam.description }}</p>
              <span class="popular-count">{{ exam.testCount }} Tests</span>
            </div>
          </div>
          <div v-else class="no-results">No exams found for "{{ searchQuery }}"</div>
        </div>

        <!-- Filtered Results -->
        <div class="content-card filtered-results-section" ref="filteredResultsRef" v-if="hasAppliedFilters">
          <div class="card-header-row">
            <div>
              <h3 class="section-heading">🔎 Filtered Results</h3>
              <p class="section-sub">{{ filteredResultExams.length }} exam{{ filteredResultExams.length === 1 ? '' : 's' }} match your filters</p>
            </div>
            <button class="view-all-btn" @click="clearAppliedFilters">Clear Filters</button>
          </div>
          <div class="applied-filter-chips">
            <span v-if="appliedFilters?.exam_type_label"       class="filter-chip">Exam Type: {{ appliedFilters.exam_type_label }}</span>
            <span v-if="appliedFilters?.job_category_label"    class="filter-chip">Job Category: {{ appliedFilters.job_category_label }}</span>
            <span v-if="appliedFilters?.category_label"        class="filter-chip">Category: {{ appliedFilters.category_label }}</span>
            <span v-if="appliedFilters?.education_level_label" class="filter-chip">Education Level: {{ appliedFilters.education_level_label }}</span>
            <span v-if="appliedFilters?.stream_label"          class="filter-chip">Stream: {{ appliedFilters.stream_label }}</span>
            <span v-if="appliedFilters?.field_label"           class="filter-chip">Field: {{ appliedFilters.field_label }}</span>
            <span v-if="appliedFilters?.sub_field_label"       class="filter-chip">Sub Field: {{ appliedFilters.sub_field_label }}</span>
            <span v-if="appliedFilters?.board_label"           class="filter-chip">Board: {{ appliedFilters.board_label }}</span>
            <span v-if="appliedFilters?.state_label"           class="filter-chip">State: {{ appliedFilters.state_label }}</span>
            <span v-if="appliedFilters?.level_label"           class="filter-chip">Level: {{ appliedFilters.level_label }}</span>
          </div>
          <div v-if="filteringLoading" class="no-results">Loading exams…</div>
          <template v-else>
            <div class="filtered-list" v-if="filteredResultExams.length">
              <div
                v-for="exam in paginatedFilteredExams"
                :key="exam.exam_id"
                class="filtered-row"
                @click="goToFilteredExam(exam)"
              >
                <div class="filtered-row-icon">
                  <img
                    v-if="exam.logo"
                    :src="exam.logo"
                    :alt="exam.exam_name"
                    class="filtered-row-logo-img"
                    @error="onLogoError"
                  />
                  <span v-else>{{ getExamInitials(exam.exam_name) }}</span>
                </div>

                <div class="filtered-row-namecol">
                  <div class="filtered-row-nametop">
                    <span class="filtered-row-code-inline">{{ getExamCode(exam) }}</span>
                    <span v-if="exam.is_trending" class="filtered-row-trending">🔥 Trending</span>
                  </div>
                  <div class="filtered-row-name">{{ getExamFullName(exam) }}</div>
                </div>

                <div class="filtered-row-meta">
                  <svg class="filtered-row-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>
                  </svg>
                  <div class="filtered-row-meta-text">
                    <span class="filtered-row-meta-label">Exam Type</span>
                    <span class="filtered-row-meta-value">{{ getExamTag(exam) }}</span>
                  </div>
                </div>

                <div class="filtered-row-meta">
                  <svg class="filtered-row-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20Z"/>
                  </svg>
                  <div class="filtered-row-meta-text">
                    <span class="filtered-row-meta-label">Level</span>
                    <span class="filtered-row-meta-value">{{ getExamLevelLabel(exam) }}</span>
                  </div>
                </div>

                <div class="filtered-row-meta">
                  <svg class="filtered-row-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>
                  </svg>
                  <div class="filtered-row-meta-text">
                    <span class="filtered-row-meta-label">Purpose</span>
                    <span class="filtered-row-meta-value">{{ getExamPurpose(exam) }}</span>
                  </div>
                </div>

                <svg class="filtered-row-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m9 6 6 6-6 6"/>
                </svg>
              </div>
            </div>
            <div v-else class="no-results">No exams match the selected filters. Try adjusting them.</div>

            <div class="filtered-pagination" v-if="filteredResultExams.length">
              <template v-if="!filteredShowAll">
                <button class="view-all-btn" @click="filteredShowAll = true">
                  View All Exams
                </button>
              </template>
              <template v-else>
                <span class="filtered-pagination-info">
                  Showing all {{ filteredResultExams.length }} exams
                </span>
                <button class="view-all-btn" @click="filteredShowAll = false; filteredPage = 1">
                  Show Less
                </button>
              </template>
            </div>
          </template>
        </div>

        <!-- Related Exams (shown alongside Filtered Results, once filters are applied) -->
        <div class="content-card" v-if="hasAppliedFilters">
          <div class="card-header-row">
            <div>
              <h3 class="section-heading">🧭 Related Exams</h3>
              <p class="section-sub">You might also be interested in these</p>
            </div>
          </div>
          <div class="popular-grid" v-if="relatedExams.length">
            <div v-for="exam in relatedExams" :key="exam.id" class="popular-card" @click="goToExam(exam.id)">
              <div class="popular-icon">
                <img v-if="exam.logo" :src="exam.logo" :alt="exam.label" class="popular-icon-img" loading="lazy" @error="onLogoError" />
                <span v-else class="popular-icon-fallback">{{ getExamInitials(exam.label) }}</span>
              </div>
              <h4 class="popular-name">{{ exam.label }}</h4>
              <p class="popular-desc">{{ exam.description }}</p>
              <span class="popular-count">{{ exam.testCount }} Tests</span>
            </div>
          </div>
          <div v-else class="no-results">No related exams found.</div>
        </div>

        <!-- ── Entrance / Job / School Exams Card ── -->
        <div class="content-card" v-if="!hasAppliedFilters">
          <!-- Header row -->
          <div class="card-header-row">
            <div>
              <h3 class="section-heading" v-if="activeExamTab === 'all'">
                📚 All Exams
              </h3>
              <h3 class="section-heading" v-else>
                {{ EXAM_TABS.find(t => t.value === activeExamTab)?.icon }}
                {{ EXAM_TABS.find(t => t.value === activeExamTab)?.label }}s
              </h3>
              <p class="section-sub" v-if="activeExamTab === 'all'">Explore exams across every category</p>
              <p class="section-sub" v-else>Explore top exams and start your preparation</p>
            </div>
            <button
              v-if="activeExamTab !== 'all'"
              class="view-all-btn"
              @click="toggleCategoryExpanded(activeExamTab)"
            >
              {{ isCategoryExpanded(activeExamTab) ? 'Show Less' : 'View All Exams' }}
            </button>
          </div>

          <div v-if="popularExamsLoading" class="no-results">Loading exams…</div>

          <!-- All Exams: grouped by category -->
          <template v-else-if="activeExamTab === 'all'">
            <div v-for="group in groupedExamsByCategory" :key="group.category" class="category-group">
              <div class="category-group-header">
                <h4 class="category-group-title">{{ group.icon }} {{ group.label }}</h4>
                <button class="view-all-btn view-all-btn--small" @click="toggleCategoryExpanded(group.category)">
                  {{ isCategoryExpanded(group.category) ? 'Show Less' : 'View All' }}
                </button>
              </div>
              <div class="popular-grid">
                <div v-for="exam in group.exams" :key="exam.id" class="popular-card" @click="goToExam(exam.id)">
                  <div class="popular-icon">
                    <img v-if="exam.logo" :src="exam.logo" :alt="exam.label" class="popular-icon-img" loading="lazy" @error="onLogoError" />
                    <span v-else class="popular-icon-fallback">{{ getExamInitials(exam.label) }}</span>
                  </div>
                  <h4 class="popular-name">{{ exam.label }}</h4>
                  <p class="popular-desc">{{ exam.description }}</p>
                  <span class="popular-count">{{ exam.testCount }} Tests</span>
                </div>
              </div>
            </div>
            <div v-if="groupedExamsByCategory.length === 0" class="no-results">No exams found for "{{ searchQuery }}"</div>
          </template>

          <!-- Single category view -->
          <template v-else>
            <div class="popular-grid">
              <div v-for="exam in filteredPopularExams" :key="exam.id" class="popular-card" @click="goToExam(exam.id)">
                <div class="popular-icon">
                  <img v-if="exam.logo" :src="exam.logo" :alt="exam.label" class="popular-icon-img" loading="lazy" @error="onLogoError" />
                  <span v-else class="popular-icon-fallback">{{ getExamInitials(exam.label) }}</span>
                </div>
                <h4 class="popular-name">{{ exam.label }}</h4>
                <p class="popular-desc">{{ exam.description }}</p>
                <span class="popular-count">{{ exam.testCount }} Tests</span>
              </div>
            </div>
            <div v-if="filteredPopularExams.length === 0" class="no-results">No exams found for "{{ searchQuery }}"</div>
          </template>
        </div>

        <!-- Upcoming Exams (TestGrid — left as-is per your request) -->
        <TestGrid
          v-if="!hasAppliedFilters"
          :exams="pagedExams"
          :loading="loading"
          :current-page="currentPage"
          :total-pages="totalPages"
          @page-change="onPageChange"
          @take="onTakeTest"
          @bookmark="onBookmark"
        />
      </div>

      <!-- ── Right: Featured Ads ── -->
      <FeaturedAds />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, type Ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/axiosInstance'
import Sidebar from '../components/exam/Sidebar.vue'
import TestGrid from '../components/exam/TestGrid.vue'
import FeaturedAds from '../components/exam/FeaturedAds.vue'
import type { Exam, ExamFilters, ExamFilterMeta, ExamFilterResponse, PaginatedResponse } from '@/types/exam'
import { usePracticeTestStore } from '../stores/practiceTest'

// Scraped from https://www.ixambee.com/free-mock-tests
// Shape: { "<category heading>": [{ name: string, logo: string }] }
import mockCategoriesRaw from '@/data/mocktest_categories.json'

const router = useRouter()
const store = usePracticeTestStore()
const searchQuery = ref('')

// ── Exam category tabs ────────────────────────────────────────────────────────
const EXAM_TABS = [
  { label: 'All Exams',     value: 'all',      icon: '📚' },
  { label: 'Entrance Exam', value: 'entrance', icon: '🎓' },
  { label: 'Job Exam',      value: 'job',      icon: '💼' },
  { label: 'School Exam',   value: 'school',   icon: '🏫' },
]
const activeExamTab = ref<'all' | 'entrance' | 'job' | 'school'>('all')

function onExamTabSelect(value: typeof activeExamTab.value): void {
  activeExamTab.value = value
}

// ── All popular exams by category ─────────────────────────────────────────────

interface PopularExam {
  id: string
  label: string
  logo: string
  colorClass: string
  description: string
  testCount: string
  category: 'entrance' | 'job' | 'school'
  examCode: string   // backend Exam.exam_code — needed downstream for /api/mockexams/
}

/** Rotates through a fixed palette so cards still get varied icon colors
 *  even though the backend has no color field of its own. */
const POPULAR_COLOR_CLASSES = [
  'ico-purple', 'ico-indigo', 'ico-green', 'ico-teal', 'ico-yellow',
  'ico-orange', 'ico-blue', 'ico-red', 'ico-cyan', 'ico-violet',
  'ico-pink', 'ico-brown', 'ico-slate',
]

/** Maps the backend's exam_type_name ("School" / "Entrance" / "Job") onto
 *  the tab/category values this page already uses everywhere else. */
function resolveCategory(exam: Exam): 'entrance' | 'job' | 'school' {
  const typeName = (exam.exam_type_name || '').trim().toLowerCase()
  if (typeName === 'job') return 'job'
  if (typeName === 'school') return 'school'
  return 'entrance'
}

/** Human-readable subtitle for a card, built from whatever real data the
 *  exam actually has — category name first, then conducting body, then
 *  the exam type — instead of the hand-written blurbs the static list used. */
function resolveDescription(exam: Exam): string {
  return exam.category_name || exam.conducting_body || exam.exam_type_name || ''
}

function formatTestCount(count?: number | null): string {
  if (!count) return '—'
  if (count >= 1000) return `${(count / 1000).toFixed(1).replace(/\.0$/, '')}K+`
  return `${count}`
}

/** Converts one backend Exam row (from GET /api/exams/filter/) into the
 *  card shape this page's templates render. */
function mapApiExamToPopular(exam: Exam, index: number): PopularExam {
  return {
    id: String(exam.exam_id),
    label: exam.exam_name,
    logo: exam.logo || '',
    colorClass: POPULAR_COLOR_CLASSES[index % POPULAR_COLOR_CLASSES.length],
    description: resolveDescription(exam),
    testCount: formatTestCount(exam.question_count),
    category: resolveCategory(exam),
    examCode: exam.exam_code || '',
  }
}

/** Backs every "popular exam" card on this page (All/Entrance/Job/School
 *  tabs, Search Results, Related Exams). Previously a large hand-written
 *  array — now populated from the real backend via fetchPopularExams(). */
const popularExams = ref<PopularExam[]>([])
const popularExamsLoading = ref(false)

async function fetchPopularExams(): Promise<void> {
  popularExamsLoading.value = true
  try {
    // No filters — pull every active exam across School/Entrance/Job in one
    // page, then bucket/slice client-side (same pattern the rest of the
    // page already uses for the curated cards).
    const res = await api.get<ExamFilterResponse>('/exams/filter/', {
      params: { page: 1, page_size: 1000 },
    })
    popularExams.value = (res.data.results ?? []).map(mapApiExamToPopular)
  } catch (err) {
    console.error('Failed to load popular exams from backend', err)
    popularExams.value = []
  } finally {
    popularExamsLoading.value = false
  }
}

const POPULAR_LIMIT = 6

/** Tracks which categories ('entrance' | 'job' | 'school') currently have
 *  their "View All" expanded, so each category's button only affects its
 *  own grid — not the others. */
const expandedCategories = ref<Set<string>>(new Set())

function isCategoryExpanded(cat: string): boolean {
  return expandedCategories.value.has(cat)
}

function toggleCategoryExpanded(cat: string): void {
  const next = new Set(expandedCategories.value)
  if (next.has(cat)) {
    next.delete(cat)
  } else {
    next.add(cat)
  }
  expandedCategories.value = next
}

const filteredPopularExams = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  let list = popularExams.value.filter(e => e.category === activeExamTab.value)
  if (query) {
    list = list.filter(e =>
      e.label.toLowerCase().includes(query) ||
      e.description.toLowerCase().includes(query)
    )
  }
  return isCategoryExpanded(activeExamTab.value) ? list : list.slice(0, POPULAR_LIMIT)
})

/** Used when the "All Exams" option is selected — buckets every exam
 *  back into its category (entrance / job / school) so they can be
 *  rendered as separate labelled sections, each with its own
 *  independent "View All" button. */
const groupedExamsByCategory = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const categories: Array<'entrance' | 'job' | 'school'> = ['entrance', 'job', 'school']

  return categories
    .map(cat => {
      let list = popularExams.value.filter(e => e.category === cat)
      if (query) {
        list = list.filter(e =>
          e.label.toLowerCase().includes(query) ||
          e.description.toLowerCase().includes(query)
        )
      }
      const tab = EXAM_TABS.find(t => t.value === cat)
      return {
        category: cat,
        label: `${tab?.label ?? cat}s`,
        icon: tab?.icon ?? '',
        exams: isCategoryExpanded(cat) ? list : list.slice(0, POPULAR_LIMIT),
      }
    })
    .filter(group => group.exams.length > 0)
})

/** If a logo URL fails to load (e.g. Wikimedia hotlink blocked/broken), hide the <img>
 *  and swap in an initials monogram so the card never shows a blank circle. */
function onLogoError(event: Event): void {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
  const fallback = document.createElement('span')
  fallback.className = 'popular-icon-fallback'
  fallback.textContent = getExamInitials(target.alt)
  target.parentElement?.appendChild(fallback)
}

/** Builds a short 1-2 letter monogram from an exam name, e.g.
 *  "Maharashtra State SSC Board" -> "MS", "Uttar Pradesh Madhyamik SSC" -> "UP" */
function getExamInitials(name?: string | null): string {
  if (!name) return '?'
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
}

/** Derives a short, human-readable exam category tag (Olympiad, Scholarship,
 *  Board Exam, Talent Search, etc.) by scanning the exam name for keywords.
 *  Falls back to any category/type data already on the record, then to a
 *  generic label — so the card never repeats the raw filter value ("School"). */
function getExamTag(exam: { exam_name?: string | null; category_name?: string | null; exam_type_name?: string | null; conducting_body?: string | null }): string {
  const name = (exam.exam_name || '').toLowerCase()

  const KEYWORD_TAGS: Array<[RegExp, string]> = [
    [/olympiad/, 'Olympiad'],
    [/scholarship/, 'Scholarship'],
    [/talent search|nmms|talent/, 'Talent Search'],
    [/entrance/, 'Entrance Exam'],
    [/board/, 'Board Exam'],
    [/navodaya|jnvst/, 'Entrance Exam'],
    [/eligibility test|nlet|net\b/, 'Eligibility Test'],
    [/aptitude/, 'Aptitude Test'],
  ]

  for (const [pattern, tag] of KEYWORD_TAGS) {
    if (pattern.test(name)) return tag
  }

  return exam.category_name || exam.exam_type_name || exam.conducting_body || 'School Exam'
}

/** Curated full official names for well-known short-code exams. Used as a
 *  fallback when the backend's exam_name is just the short code itself
 *  (e.g. exam_name: "KIITEE" instead of the full official title), so the
 *  row list always shows a real full name next to the code — matching the
 *  target design (e.g. AEEE -> "Amrita Entrance Examination Engineering"). */
const EXAM_FULL_NAMES: Record<string, string> = {
  AEEE:        'Amrita Entrance Examination Engineering',
  'AP EAPCET': 'Andhra Pradesh Engineering, Agriculture and Pharmacy Common Entrance Test',
  CAT:         'Common Admission Test',
  'COMEDK UGET': 'Consortium of Medical, Engineering and Dental Colleges of Karnataka Under Graduate Entrance Test',
  GATE:        'Graduate Aptitude Test in Engineering',
  GUJCET:      'Gujarat Common Entrance Test',
  KCET:        'Karnataka Common Entrance Test',
  KEAM:        'Kerala Engineering Architecture Medical Entrance Exam',
  KIITEE:      'Kalinga Institute of Industrial Technology Entrance Examination',
  'LPU NEST':  'Lovely Professional University National Entrance and Scholarship Test',
  'MAH MBA CET': 'Maharashtra MBA Common Entrance Test',
  'MHT CET PCM': 'Maharashtra Common Entrance Test (Physics, Chemistry, Maths)',
  OJEE:        'Odisha Joint Entrance Examination',
  TNEA:        'Tamil Nadu Engineering Admissions',
  WBJEE:       'West Bengal Joint Entrance Examination',
  SRMJEEE:     'SRM Joint Engineering Entrance Examination',
  VITEEE:      'VIT Engineering Entrance Examination',
  BITSAT:      'Birla Institute of Technology and Science Admission Test',
}

/** Returns the exam's full display name, falling back to the curated map
 *  above when the backend only gave us the short code as the "name". */
function getExamFullName(exam: { exam_name?: string | null; exam_code?: string | null }): string {
  const name = (exam.exam_name || '').trim()
  const code = (exam.exam_code || '').trim().toUpperCase().replace(/_/g, ' ')
  const normalizedName = name.toUpperCase().replace(/[.\s]+/g, ' ').trim()
  const normalizedCode = code.replace(/[.\s]+/g, ' ').trim()

  // If exam_name is empty, or it's identical to the short code (ignoring
  // case/spacing), the backend didn't give us a real full name — look one up.
  if (!name || (normalizedCode && normalizedName === normalizedCode)) {
    const lookupKey = code || name.toUpperCase()
    if (EXAM_FULL_NAMES[lookupKey]) return EXAM_FULL_NAMES[lookupKey]
  }

  return name || code || 'Untitled Exam'
}

/** Short code shown before the exam name in the row list (e.g. "AEEE",
 *  "AP EAPCET"). Uses the backend exam_code when present, otherwise falls
 *  back to the same monogram used for the icon. */
function getExamCode(exam: { exam_name?: string | null; exam_code?: string | null }): string {
  if (exam.exam_code) return exam.exam_code.toUpperCase().replace(/_/g, ' ')
  return getExamInitials(exam.exam_name)
}

/** Returns the exam's level label. The seed data (exams_by_type_merged_filled.json)
 *  stores a real `state` on state-specific exams (e.g. MHT-CET -> "Maharashtra")
 *  and leaves it null for national ones, so this reads that directly instead of
 *  guessing — "National" is only a fallback for the rare case state_name is unset
 *  and level_name isn't provided either. */
function getExamLevelLabel(exam: { level_name?: string | null; state_name?: string | null }): string {
  if (exam.state_name) return `State (${exam.state_name})`
  return exam.level_name || 'National'
}

/** Returns the "Purpose" text. The seed data already stores a real, human-written
 *  description per exam (e.g. JEE Main -> "Engineering Entrance (National)",
 *  NEET-UG -> "Medical Entrance (UG)"), so this uses that directly. The keyword
 *  map below only kicks in for exams with no description at all, to still show
 *  something reasonable rather than a blank field. */
function getExamPurpose(exam: { exam_name?: string | null; category_name?: string | null; description?: string | null; exam_type_name?: string | null }): string {
  if (exam.description) return exam.description

  const name = (exam.exam_name || '').toLowerCase()

  const KEYWORD_PURPOSE: Array<[RegExp, string]> = [
    [/neet.?ug/, 'MBBS / BDS Admissions'],
    [/neet.?pg/, 'MD / MS / PG Medical Admissions'],
    [/jee.?adv/, 'IIT Admissions'],
    [/jee/, 'Engineering Admissions'],
    [/bitsat/, 'Engineering Admissions (BITS Campuses)'],
    [/cuet/, 'UG University Admissions'],
    [/clat/, 'Law (UG & PG) Admissions'],
    [/mht.?cet/, 'Engineering & Pharma Admissions'],
    [/cat\b/, 'MBA Admissions'],
    [/gate/, 'M.Tech / PSU Recruitment'],
    [/upsc/, 'Civil Services Recruitment'],
    [/ssc/, 'Government Job Recruitment'],
    [/net\b|ugc/, 'Assistant Professor / JRF Eligibility'],
  ]

  for (const [pattern, purpose] of KEYWORD_PURPOSE) {
    if (pattern.test(name)) return purpose
  }

  if (exam.category_name) return exam.category_name
  return exam.exam_type_name ? `${exam.exam_type_name} Admissions` : 'Admissions'
}

/** Picks a badge color for the exam-type tag so Management/Medical/etc.
 *  stand out from the default purple "Engineering Entrance" style badge. */
function getExamTagClass(exam: { exam_name?: string | null; category_name?: string | null; exam_type_name?: string | null; conducting_body?: string | null }): string {
  const tag = getExamTag(exam).toLowerCase()
  if (tag.includes('management')) return 'tag-amber'
  if (tag.includes('medical')) return 'tag-rose'
  if (tag.includes('olympiad')) return 'tag-blue'
  if (tag.includes('scholarship') || tag.includes('talent')) return 'tag-green'
  return 'tag-purple'
}

/** Cards now carry the real backend exam_id directly (mapApiExamToPopular
 *  sets PopularExam.id = String(exam.exam_id)), so this can navigate
 *  straight to the practice flow — no more slug-to-category guessing or an
 *  extra lookup call to resolve a numeric PK. */
function goToExam(examId: string): void {
  const exam = popularExams.value.find(e => e.id === examId)
  if (!exam) return

  store.setExam({
    id: exam.id,
    label: exam.label,
    category: exam.description,
    code: exam.examCode,
  })
  store.setExamType({ id: exam.id, dbId: Number(exam.id), label: exam.label })
  router.push({ name: 'practice-test-type' })
}

// ── Upcoming Exams (fed from the scraped ixambee JSON) ──────

/** Extra field beyond the base Exam type — TestGrid can ignore it if unused. */
type ScrapedExam = Exam & { logo?: string | null }

interface RawCategoryEntry {
  name: string
  logo: string | null
}

/**
 * Best-effort category bucket, purely from the exam's name, so it lines up
 * with the exam_category values used elsewhere in this file (BANKING, SSC,
 * RAILWAY, etc.). Adjust the keyword lists as needed for your data.
 */
function guessCategory(name: string): string {
  const n = name.toUpperCase()
  if (/\b(IBPS|SBI|BANK|RBI|NABARD|IDBI|RRB\s*(PO|CLERK|OFFICER)|FEDERAL BANK|CANARA|SYNDICATE)\b/.test(n)) return 'BANKING'
  if (/\bSSC\b/.test(n)) return 'SSC'
  if (/\b(RAILWAY|RRB\s*(NTPC|JE|GROUP)|RPF)\b/.test(n)) return 'RAILWAY'
  if (/\b(NIACL|LIC|OICL|GIC|INSURANCE|ECGC)\b/.test(n)) return 'INSURANCE'
  if (/\b(SEBI|PFRDA|EPFO)\b/.test(n)) return 'REGULATORY'
  if (/\b(POLICE|ARMY|NAVY|AIR ?FORCE|CONSTABLE|AGNIVEER|AFCAT)\b/.test(n)) return 'DEFENCE'
  if (/\b(KVS|NVS|TEACHER|TET|EMRS)\b/.test(n)) return 'TEACHING'
  if (/\bUPSC\b/.test(n)) return 'UPSC'
  if (/\b(MAT|CMAT|CLAT)\b/.test(n)) return 'MBA_LAW'
  return 'OTHER'
}

/** Flatten { "<category heading>": [...] } into a single list of raw entries. */
function flattenRawCategories(raw: Record<string, RawCategoryEntry[]>): RawCategoryEntry[] {
  return Object.values(raw).flat()
}

/** Map one scraped { name, logo } entry to the Exam shape TestGrid expects. */
function mapToExam(entry: RawCategoryEntry, index: number): ScrapedExam {
  return {
    exam_id: index + 1,
    exam_name: entry.name,
    exam_year: new Date().getFullYear(),
    conducting_body: entry.name.split(' ')[0], // e.g. "SBI", "IBPS", "SSC" — refine if you need something smarter
    exam_category: guessCategory(entry.name),
    question_count: 0,          // not available from the scrape — TestGrid should treat 0/blank as "not shown"
    duration_minutes: 0,        // not available from the scrape
    difficulty: 'medium',
    language: 'English, Hindi',
    logo: entry.logo,
  }
}

const allScrapedExams: ScrapedExam[] = flattenRawCategories(
  mockCategoriesRaw as unknown as Record<string, RawCategoryEntry[]>
).map(mapToExam)

const exams: Ref<Exam[]> = ref([])
const loading: Ref<boolean> = ref(false)
const currentPage: Ref<number> = ref(1)

/** "Upcoming Exams" is now a short preview, not a paginated browse-all list —
 *  cap it to a handful of exams. totalPages stays at 1 so TestGrid's
 *  pagination controls (which only render when totalPages > 1) stay hidden. */
const UPCOMING_EXAMS_LIMIT = 6
const totalPages = computed(() => 1)

/** Local dataset filtered by the search box only.
 *  NOTE: intentionally NOT filtered by the sidebar's Apply Filters — the
 *  "Upcoming Exams" preview below should always draw from the full
 *  scraped dataset regardless of what's selected in the Filters sidebar.
 *  Sidebar-driven filtering is handled separately by the "Filtered Results"
 *  card (see filteredResultExams) further up the page. */
const filteredScrapedExams = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return allScrapedExams.filter((exam) => {
    if (query && !exam.exam_name.toLowerCase().includes(query)) return false
    return true
  })
})

/** First few exams from the filtered dataset — a short preview, not a full page. */
const pagedExams = computed<Exam[]>(() =>
  filteredScrapedExams.value.slice(0, UPCOMING_EXAMS_LIMIT)
)

async function fetchExams(): Promise<void> {
  loading.value = true
  try {
    const params: Record<string, string | number> = { page: currentPage.value }
    const res  = await api.get<Exam[] | PaginatedResponse<Exam>>('/exams/', { params })
    const data = res.data
    if (Array.isArray(data) && data.length) {
      exams.value = data
    } else if (!Array.isArray(data) && data.results?.length) {
      exams.value = data.results
    }
  } catch (err) {
    console.error('Failed to fetch exams, falling back to scraped mock-test categories', err)
  } finally {
    loading.value = false
  }
}

// ── Search Results section (driven by the top search box) ─────────────────────

const hasSearchQuery = computed(() => searchQuery.value.trim().length > 0)

/** Exams shown in the "Search Results" card — matched against the curated
 *  popularExams list (same dataset/card shape as Filtered Results & All
 *  Exams) by name or description, across every category. */
const searchResultExams = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return []
  return popularExams.value.filter(e =>
    e.label.toLowerCase().includes(query) ||
    e.description.toLowerCase().includes(query)
  )
})

function clearSearch(): void {
  searchQuery.value = ''
}

// ── Filtered Results section (driven by the Sidebar's "Apply Filters") ────────

const sidebarRef = ref<InstanceType<typeof Sidebar> | null>(null)
const appliedFilters: Ref<ExamFilters | null> = ref(null)
const filteredResultsRef = ref<HTMLElement | null>(null)

/** Bound to the Sidebar's "apply" event — scrolls the page up to bring the
 *  Filtered Results card into view once the user clicks Apply Filters,
 *  since the filters panel can be scrolled well below it. Waits a tick so
 *  the (v-if-gated) results section has actually rendered first. */
async function scrollToFilteredResults(): Promise<void> {
  await nextTick()
  if (filteredResultsRef.value) {
    filteredResultsRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const hasAppliedFilters = computed(() => {
  const f = appliedFilters.value
  if (!f) return false
  return !!(
    f.exam_type_id || f.category_id || f.job_category_id || f.education_level_id ||
    f.stream_id || f.field_id || f.sub_field_id || f.board_id || f.state_id || f.level_id
  )
})

/** Exams shown in the "Filtered Results" card — now sourced directly from
 *  GET /api/exams/filter/ (ExamFilterView), not the curated popularExams
 *  mock list. See fetchFilteredExams(). */
const filteredApiResults: Ref<Exam[]> = ref([])
const filterMeta: Ref<ExamFilterMeta | null> = ref(null)
const filterWarnings: Ref<string[]> = ref([])
const filteringLoading = ref(false)

const filteredResultExams = computed(() => filteredApiResults.value)

/* ── Filtered Results: client-side pagination (8 rows per page) ── */
const filteredPage = ref(1)
const filteredShowAll = ref(false)
const FILTERED_PAGE_SIZE = 8
const paginatedFilteredExams = computed(() => {
  if (filteredShowAll.value) return filteredResultExams.value
  const start = (filteredPage.value - 1) * FILTERED_PAGE_SIZE
  return filteredResultExams.value.slice(start, start + FILTERED_PAGE_SIZE)
})

/** "Related Exams" shown once the full filtered list is expanded — pulls
 *  from the curated popularExams list for the currently active tab (or all
 *  categories, if the "All Exams" tab is active), excluding anything that's
 *  already present in the filtered results, capped to a short preview row. */
const relatedExams = computed(() => {
  const filteredNames = new Set(
    filteredResultExams.value.map(e => (e.exam_name || '').trim().toUpperCase())
  )
  const pool = activeExamTab.value === 'all'
    ? popularExams.value
    : popularExams.value.filter(e => e.category === activeExamTab.value)

  return pool
    .filter(e => !filteredNames.has(e.label.trim().toUpperCase()))
    .slice(0, 6)
})

/** Builds the query params ExamFilterView expects from the *_id fields on
 *  appliedFilters (the *_label fields are UI-only and never sent). */
async function fetchFilteredExams(): Promise<void> {
  const f = appliedFilters.value
  if (!f || !hasAppliedFilters.value) {
    filteredApiResults.value = []
    filterMeta.value = null
    filterWarnings.value = []
    filteredPage.value = 1
    filteredShowAll.value = false
    return
  }

  filteringLoading.value = true
  try {
    const params: Record<string, number> = {}
    if (f.exam_type_id) params.exam_type_id = f.exam_type_id
    if (f.category_id) params.category_id = f.category_id
    if (f.job_category_id) params.job_category_id = f.job_category_id
    if (f.education_level_id) params.education_level_id = f.education_level_id
    if (f.stream_id) params.stream_id = f.stream_id
    if (f.field_id) params.field_id = f.field_id
    if (f.sub_field_id) params.sub_field_id = f.sub_field_id
    if (f.board_id) params.board_id = f.board_id
    if (f.state_id) params.state_id = f.state_id
    if (f.level_id) params.level_id = f.level_id
    // Pagination removed for Filtered Results — always fetch the full match set.
    params.page = 1
    params.page_size = f.page_size ?? 1000

    const res = await api.get<ExamFilterResponse>('/exams/filter/', { params })
    filteredApiResults.value = res.data.results ?? []
    filterMeta.value = res.data.meta ?? null
    filterWarnings.value = res.data.warnings ?? []
    filteredPage.value = 1
    filteredShowAll.value = false
  } catch (err) {
    console.error('Failed to load filtered exams', err)
    filteredApiResults.value = []
    filterMeta.value = null
  } finally {
    filteringLoading.value = false
  }
}

function clearAppliedFilters(): void {
  sidebarRef.value?.reset()
}

function onFilterChange(newFilters: ExamFilters): void {
  appliedFilters.value = { ...newFilters, page: 1 }
  fetchFilteredExams()
}

/** Both this and goToExam() now navigate using the real backend exam_id
 *  directly, since popularExams is populated from the API too. */
function goToFilteredExam(exam: Exam): void {
  store.setExam({
    id: String(exam.exam_id),
    label: exam.exam_name,
    category: exam.category_name ?? exam.exam_type_name ?? '',
    code: exam.exam_code || '',
  })
  store.setExamType({ id: String(exam.exam_id), dbId: exam.exam_id, label: exam.exam_name })
  router.push({ name: 'practice-test-type' })
}

function onPageChange(page: number):  void { currentPage.value = page; fetchExams() }
function onTakeTest(exam: Exam):      void { router.push({ name: 'exam-attempt', params: { id: exam.exam_id } }) }
function onBookmark(exam: Exam):      void { exam.is_bookmarked = !exam.is_bookmarked }

onMounted(() => {
  fetchExams()
  fetchPopularExams()
})
</script>

<style>
/* ══════════════════════════════════════════════════════════════════
   TOP FILTER BAR  (tabs + search — full-width bar above the 3-col grid)
   ══════════════════════════════════════════════════════════════════ */
.top-filter-bar {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 18px;
  padding: 14px 20px;
}

.top-filter-bar-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.top-filter-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1 1 auto;
}

.top-filter-icon {
  width: 17px; height: 17px;
  color: #7c3aed;
  flex-shrink: 0;
}

.top-filter-label {
  font-size: 13px;
  font-weight: 700;
  color: #1e2536;
  white-space: nowrap;
  margin-right: 4px;
}

.top-tab-pills {
  margin-left: 170px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.top-tab-pill {
  background: #fff;
  border: 1.5px solid #e2e2ea;
  color: #4b5165;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 18px;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  user-select: none;
}
.top-tab-pill:hover   { border-color: #a78bfa; color: #7c3aed; }
.top-tab-pill--active { background: #7c3aed; border-color: #7c3aed; color: #fff; }
.top-tab-pill--active:hover { background: #6d28d9; color: #fff; }

/* divider between tabs and search */
.top-filter-right {
  display: flex;
  align-items: center;
  gap: 10px;
  border-left: 1.5px solid #e5e7eb;
  padding-left: 20px;
  flex-shrink: 0;
}

.top-search-bar {
  position: relative;
}
.top-search-ico {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  width: 15px; height: 15px; color: #9ca3af;
}
.top-search-input {
  width: 320px;
  box-sizing: border-box;
  padding: 9px 14px 9px 36px;
  border: 1.5px solid #e5e7eb;
  border-radius: 999px;
  font-size: 13px;
  color: #1e2536;
  outline: none;
  transition: border-color 0.15s;
  background: #f9fafb;
}
.top-search-input:focus { border-color: #7c3aed; background: #fff; }

.top-search-btn {
  background: #7c3aed;
  color: #fff;
  border: none;
  font-size: 13px;
  font-weight: 700;
  padding: 9px 22px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
  user-select: none;
}
.top-search-btn:hover { background: #6d28d9; }

/* ══════════════════════════════════════════════════════════════════
   PAGE LAYOUT  (3-column grid below the top bar)
   ══════════════════════════════════════════════════════════════════ */
.exam-page { padding: 0; }

.exam-page-grid {
  display: grid;
  grid-template-columns: 250px 1fr 270px;
  gap: 18px;
  align-items: start;
}

/* Ads column sticky */
.exam-page-grid > *:last-child {
  position: sticky;
  top: 80px;
}

@media (max-width: 1300px) {
  .exam-page-grid { grid-template-columns: 1fr; }
  .exam-page-grid > *:last-child { position: static; }
  .top-search-input { width: 200px; }
}

@media (max-width: 700px) {
  .top-filter-bar-inner { flex-direction: column; align-items: flex-start; }
  .top-filter-right { border-left: none; padding-left: 0; border-top: 1.5px solid #e5e7eb; padding-top: 12px; width: 100%; }
  .top-search-input { width: 100%; }
}

.exam-page-main { min-width: 0; }

/* ══════════════════════════════════════════════════════════════════
   SHARED CONTENT CARD
   ══════════════════════════════════════════════════════════════════ */
.content-card {
  background: #fff;
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 16px;
  border: 1px solid #f0f0f0;
}

.filtered-results-section {
  border-color: #ddd6fe;
  scroll-margin-top: 90px;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.section-heading { font-size: 15px; font-weight: 700; color: #1e2536; margin: 0 0 2px; }
.section-sub     { font-size: 12.5px; color: #6b7280; margin: 0; }

/* ── Applied filter chips ── */
.applied-filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.filter-chip {
  background: #f5f3ff;
  border: 1px solid #ddd6fe;
  color: #6d28d9;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 999px;
  white-space: nowrap;
}

/* ── View All button ── */
.view-all-btn {
  background: #fff; border: 1.5px solid #7c3aed; color: #7c3aed;
  font-size: 12.5px; font-weight: 600; padding: 7px 14px;
  border-radius: 8px; cursor: pointer; white-space: nowrap;
  transition: background 0.15s;
  user-select: none;
}
.view-all-btn:hover { background: #f5f3ff; }
.view-all-btn--small { font-size: 11.5px; padding: 5px 12px; }

/* ══════════════════════════════════════════════════════════════════
   EXAM GRID  (6-up card grid matching the image)
   ══════════════════════════════════════════════════════════════════ */
.popular-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  align-items: stretch;
}
@media (max-width: 1100px) { .popular-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 700px)  { .popular-grid { grid-template-columns: repeat(2, 1fr); } }

.popular-card {
  display: flex; flex-direction: column; align-items: center; text-align: center;
  background: #fafafa; border: 1.5px solid #f0f0f0; border-radius: 12px;
  padding: 14px 8px; cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  user-select: none;
}
.popular-card:hover { border-color: #c4b5fd; box-shadow: 0 2px 12px rgba(124,58,237,0.08); }

.popular-icon {
  width: 68px; height: 68px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 8px; overflow: hidden;
  background: #f5f5f5; border: 1.5px solid #e5e7eb;
  flex-shrink: 0;
}
.popular-icon-img {
  width: 58px; height: 58px;
  object-fit: contain; object-position: center;
  border-radius: 0; display: block; image-orientation: from-image;
}
.popular-icon-fallback {
  width: 58px; height: 58px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; color: #7c3aed;
  background: #ede9fe; border-radius: 50%;
}

/* icon color helpers */
.ico-purple { background: #ede9fe; }
.ico-green  { background: #d1fae5; }
.ico-orange { background: #fef3c7; }
.ico-pink   { background: #fce7f3; }
.ico-blue   { background: #dbeafe; }
.ico-violet { background: #e0e7ff; }
.ico-cyan   { background: #cffafe; }
.ico-red    { background: #fee2e2; }
.ico-indigo { background: #e0e7ff; }
.ico-teal   { background: #ccfbf1; }
.ico-yellow { background: #fef9c3; }
.ico-brown  { background: #f3e8d9; }
.ico-slate  { background: #e2e8f0; }

.popular-name  { font-size: 13px; font-weight: 700; color: #1e2536; margin: 0 0 3px; }
.popular-desc  { font-size: 10.5px; color: #6b7280; margin: 0; line-height: 1.3; flex: 1; }
.popular-count { font-size: 11px; color: #7c3aed; font-weight: 600; margin-top: 8px; }
.no-results    { text-align: center; color: #6b7280; font-size: 13px; padding: 20px 0; }

/* ══════════════════════════════════════════════════════════════════
   FILTERED RESULTS — horizontal row list (matches target design)
   ══════════════════════════════════════════════════════════════════ */
.filtered-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filtered-row {
  display: grid;
  grid-template-columns: 48px minmax(140px, 1.4fr) repeat(3, minmax(0, 1fr)) 16px;
  align-items: center;
  column-gap: 13px;
  background: #fff;
  border: 1.5px solid #ececf5;
  border-radius: 14px;
  padding: 16px 18px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  min-width: 0;
  overflow: hidden;
}
.filtered-row:hover {
  border-color: #c4b5fd;
  box-shadow: 0 4px 14px rgba(124,58,237,0.08);
}

.filtered-row-icon {
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: #fff; border: 1.5px solid #ddd6fe;
  font-size: 13px; font-weight: 700; color: #6d28d9;
  overflow: hidden;
}
.filtered-row-logo-img {
  width: 100%; height: 100%; object-fit: contain; object-position: center;
}

.filtered-row-namecol {
  min-width: 0;
  display: flex; flex-direction: column; gap: 4px;
}
.filtered-row-nametop {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.filtered-row-code-inline {
  font-size: 15px; font-weight: 800; color: #1e2536; letter-spacing: 0.2px;
}
.filtered-row-name {
  font-size: 12.5px; color: #6b7280; line-height: 1.35;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}

.filtered-row-meta {
  display: flex; align-items: flex-start; gap: 8px;
  min-width: 0; height: 100%;
}
.filtered-row-meta-icon {
  width: 18px; height: 18px; color: #7c3aed; flex-shrink: 0; margin-top: 2px;
}
.filtered-row-meta-text {
  display: flex; flex-direction: column; gap: 2px; min-width: 0;
}
.filtered-row-meta-label {
  font-size: 11.5px; color: #9ca3af; font-weight: 500; white-space: nowrap;
}
.filtered-row-meta-value {
  font-size: 13px; color: #1e2536; font-weight: 600; line-height: 1.3;
  word-break: break-word;
}

.filtered-row-trending {
  font-size: 11px; font-weight: 700; padding: 4px 10px;
  border-radius: 999px; white-space: nowrap; flex-shrink: 0;
  background: #fff1e6; color: #c2410c; border: 1px solid #fed7aa;
}
.tag-purple { background: #ede9fe; color: #6d28d9; }
.tag-amber  { background: #fef3c7; color: #b45309; }
.tag-rose   { background: #ffe4e6; color: #be123c; }
.tag-blue   { background: #dbeafe; color: #1d4ed8; }
.tag-green  { background: #d1fae5; color: #047857; }

.filtered-row-chevron {
  width: 16px; height: 16px; color: #9ca3af; flex-shrink: 0;
}

@media (max-width: 900px) {
  .filtered-row {
    grid-template-columns: 48px 1fr;
    row-gap: 12px;
  }
  .filtered-row-namecol { grid-column: 2 / 3; }
  .filtered-row-meta { grid-column: 1 / -1; }
  .filtered-row-chevron { display: none; }
}

/* ── Filtered Results footer: "View All Exams" / "Show Less" ── */
.filtered-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 18px;
  flex-wrap: wrap;
}
.filtered-pagination-info { font-size: 12.5px; color: #6b7280; }

/* ── Category groups (All Exams view) ── */
.category-group { margin-bottom: 22px; }
.category-group:last-child { margin-bottom: 0; }
.category-group-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.category-group-title { font-size: 13.5px; font-weight: 700; color: #1e2536; margin: 0; }

/* ══════════════════════════════════════════════════════════════════
   SIDEBAR & FEATURED ADS  (shared globals used by child components)
   ══════════════════════════════════════════════════════════════════ */
.panel { background: #f3f1fb; border-radius: 14px; padding: 18px; box-shadow: 0 4px 16px rgba(0,0,0,0.04); }
.panel h3 { font-size: 15px; font-weight: 700; margin: 0 0 14px; }

.filter-group { margin-bottom: 18px; }
.filter-group label { display: block; font-size: 13px; font-weight: 600; color: #1e2536; margin-bottom: 6px; }
.filter-select { width: 100%; padding: 9px 10px; border-radius: 8px; border: 1px solid #ddd; background: #fff; font-size: 13px; color: #1e2536; }

.filter-section-title { display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.check-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }
.check-row .left { display: flex; align-items: center; gap: 8px; }

.toggle { width: 34px; height: 18px; border-radius: 999px; background: #ddd6fe; position: relative; cursor: pointer; transition: background 0.2s; }
.toggle.on { background: #3b5bfd; }
.toggle::after { content: ''; position: absolute; top: 2px; left: 2px; width: 14px; height: 14px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle.on::after { transform: translateX(16px); }

.section-title { font-size: 15px; font-weight: 700; margin: 0 0 14px; }

.ad-card { border-radius: 12px; padding: 14px; margin-bottom: 14px; position: relative; overflow: hidden; }
.ad-card .ad-title { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.ad-card .ad-subtitle { font-size: 11px; color: #6b7280; margin-bottom: 10px; }
.ad-card .ad-price { font-size: 13px; font-weight: 700; margin-right: 8px; }
.ad-buy-btn { background: #fff; border: none; padding: 6px 14px; border-radius: 7px; font-weight: 700; font-size: 11px; cursor: pointer; }
.ads-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ad-card-small { border-radius: 12px; padding: 10px; }
.ad-card-small .ad-title { font-size: 11px; }
</style>