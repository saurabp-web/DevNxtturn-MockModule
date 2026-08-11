<template>
  <aside class="panel filters-panel">
    <div class="filters-sticky-inner">
    <h3>Filters</h3>

    <div class="filter-scroll-area">
    <!-- 1. Exam Type (School / Entrance / Job) -->
    <div class="filter-group">
      <label>Exam Type</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'examType' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('examType')">
          <span>{{ examTypeLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'examType' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'examType'" class="filter-dropdown-panel">
          <label v-for="opt in examTypeOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.examTypeId === opt.value"
              @change="selectExamType(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 2. Education Level — always visible.
         Shows ALL levels when no exam type selected;
         narrows to relevant levels once School / Entrance / Job is picked. -->
    <div class="filter-group">
      <label>Education Level</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'educationLevel' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('educationLevel')">
          <span>{{ educationLevelLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'educationLevel' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'educationLevel'" class="filter-dropdown-panel">
          <label v-for="opt in educationLevelOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.educationLevelId === opt.value"
              @change="selectEducationLevel(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 3. Streams — always shown (common filter) -->
    <div class="filter-group">
      <label>Streams</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'stream' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('stream')">
          <span>{{ streamLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'stream' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'stream'" class="filter-dropdown-panel">
          <label v-for="opt in streamOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.streamId === opt.value"
              @change="selectStream(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 4. Field — Entrance only, depends on Stream (shown right after Streams) -->
    <div class="filter-group" v-if="branchType === 'entrance' && local.streamId">
      <label>Field</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'field' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('field')">
          <span>{{ fieldLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'field' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'field'" class="filter-dropdown-panel">
          <label v-for="opt in fieldOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.fieldId === opt.value"
              @change="selectField(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 5. Sub Field — Entrance only, depends on Field (shown right after Field) -->
    <div class="filter-group" v-if="branchType === 'entrance' && local.fieldId">
      <label>Sub Field</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'subField' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('subField')">
          <span>{{ subFieldLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'subField' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'subField'" class="filter-dropdown-panel">
          <label v-for="opt in subFieldOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.subFieldId === opt.value"
              @change="selectSubField(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 6. States — always shown (common filter) -->
    <div class="filter-group">
      <label>States</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'state' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('state')">
          <span>{{ stateLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'state' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'state'" class="filter-dropdown-panel">
          <label v-for="opt in stateOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.stateId === opt.value"
              @change="selectState(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 7. Exam Level (Central / State / University) — always shown (common filter) -->
    <div class="filter-group">
      <label>Exam Level</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'level' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('level')">
          <span>{{ levelLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'level' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'level'" class="filter-dropdown-panel">
          <label v-for="opt in levelOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.levelId === opt.value"
              @change="selectLevel(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- ── Below here: filters relevant to the selected Exam Type only ── -->

    <!-- 8. Board — School only -->
    <div class="filter-group" v-if="branchType === 'school'">
      <label>Board</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'board' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('board')">
          <span>{{ boardLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'board' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'board'" class="filter-dropdown-panel">
          <label v-for="opt in boardOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.boardId === opt.value"
              @change="selectBoard(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 9. Job Category — Job only -->
    <div class="filter-group" v-if="branchType === 'job'">
      <label>Job Category</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'jobCategory' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('jobCategory')">
          <span>{{ jobCategoryLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'jobCategory' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'jobCategory'" class="filter-dropdown-panel">
          <label v-for="opt in jobCategoryOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.jobCategoryId === opt.value"
              @change="selectJobCategory(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <!-- 10. Category — School / Entrance / Job (resolves to whichever
         category table matches the selected Exam Type, via
         /api/filters/exam-categories/) -->
    <!-- <div class="filter-group" v-if="branchType">
      <label>Category</label>
      <div class="filter-dropdown" :class="{ 'filter-dropdown--open': openFilter === 'category' }">
        <button type="button" class="filter-dropdown-trigger" @click="toggleFilter('category')">
          <span>{{ categoryLabel }}</span>
          <svg
            class="filter-dropdown-chevron"
            :class="{ 'filter-dropdown-chevron--open': openFilter === 'category' }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </button>
        <div v-if="openFilter === 'category'" class="filter-dropdown-panel">
          <label v-for="opt in categoryOptions" :key="opt.value" class="filter-checkbox-row">
            <input
              type="checkbox"
              class="filter-checkbox"
              :checked="local.categoryId === opt.value"
              @change="selectCategory(opt.value)"
            />
            <span>{{ opt.label }}</span>
          </label>
        </div>
      </div>
    </div> -->

    </div> <!-- end filter-scroll-area -->

    <div class="filter-actions">
      <button class="reset-btn" @click="resetFilters">Reset</button>
      <button class="apply-btn" @click="applyFilters">Apply Filters</button>
    </div>
    </div> <!-- end filters-sticky-inner -->
  </aside>
</template>

<script setup lang="ts">
import { reactive, computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import api from '@/services/axiosInstance'
import type { ExamFilters } from '../../types/exam'

const emit = defineEmits<{
  (e: 'change', filters: ExamFilters): void
  (e: 'apply'): void
}>()

// ── Types ────────────────────────────────────────────────────────────────────

interface Option { label: string; value: string }

interface SidebarState {
  examTypeId: string
  categoryId: string
  jobCategoryId: string
  educationLevelId: string
  streamId: string
  fieldId: string
  subFieldId: string
  boardId: string
  stateId: string
  levelId: string
}

function defaultState(): SidebarState {
  return {
    examTypeId: '',
    categoryId: '',
    jobCategoryId: '',
    educationLevelId: '',
    streamId: '',
    fieldId: '',
    subFieldId: '',
    boardId: '',
    stateId: '',
    levelId: '',
  }
}

const local = reactive<SidebarState>(defaultState())

const ALL_OPTION: Option = { label: 'All', value: '' }

/** Normalizes a filter-endpoint response into a plain array, whether it
 *  came back as a bare list (pagination_class = None) or the default
 *  DRF-paginated `{ results: [...] }` shape. */
function toArray<T = Record<string, unknown>>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[]
  if (data && Array.isArray((data as { results?: T[] }).results)) {
    return (data as { results: T[] }).results
  }
  return []
}

// ── Option lists — fetched from /api/filters/* ────────────────────────────────

const examTypeOptions = ref<Option[]>([ALL_OPTION])
const fieldOptions = ref<Option[]>([ALL_OPTION])
const subFieldOptions = ref<Option[]>([ALL_OPTION])
const boardOptions = ref<Option[]>([ALL_OPTION])
const stateOptions = ref<Option[]>([ALL_OPTION])
const levelOptions = ref<Option[]>([ALL_OPTION])
const jobCategoryOptions = ref<Option[]>([ALL_OPTION])
const categoryOptions = ref<Option[]>([ALL_OPTION])

/** exam_type_id -> lowercased type_name ('school' | 'entrance' | 'job' | ...),
 *  used to decide which sections of the panel to show — mirrors the
 *  type_name.strip().lower() branching in ExamFilterView / ExamCategoryListView. */
const examTypeNameById = ref<Record<string, string>>({})

const branchType = computed<'school' | 'entrance' | 'job' | ''>(() => {
  const name = examTypeNameById.value[local.examTypeId] ?? ''
  if (name === 'school' || name === 'entrance' || name === 'job') return name
  return ''
})

// ── Fetchers ─────────────────────────────────────────────────────────────────

async function fetchExamTypes(): Promise<void> {
  try {
    const res = await api.get('/filters/exam-types/')
    const rows = toArray<{ exam_type_id: number; type_name: string }>(res.data)
    examTypeOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.type_name, value: String(r.exam_type_id) }))]
    examTypeNameById.value = Object.fromEntries(
      rows.map(r => [String(r.exam_type_id), (r.type_name || '').trim().toLowerCase()]),
    )
  } catch (err) {
    console.error('Failed to load exam types', err)
  }
}

// ── Education level options filtered by exam type ─────────────────────────────
// Allowed education level IDs per exam type (client-side filter applied
// against the full list fetched from the backend on mount).
//   School   → Class 1–12          (IDs 1–12)
//   Entrance → Class10/12/ITI/Cert/Diploma/Polytechnic/UG-Pursuing/
//              Graduate/PG-Pursuing/PG/Integrated/Professional/
//              Doctorate/PostDoc/AnyGrad/AnyPG  (IDs 10–26)
//   Job      → Class10/12/ITI/Diploma/Polytechnic/Graduate/PG/
//              Professional/AnyGrad/AnyPG/AnyQualification (IDs 10,12,13,15,16,18,20,22,25,26,27)

const EDUCATION_LEVEL_IDS_BY_TYPE: Record<string, number[]> = {
  school:   [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
  entrance: [10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26],
  job:      [10, 12, 13, 15, 16, 18, 20, 22, 25, 26, 27],
}

// ALL education levels from backend — fetched once on mount, never re-fetched
const allEducationLevels = ref<{ id: number; label: string }[]>([])

async function fetchEducationLevels(): Promise<void> {
  try {
    const res = await api.get('/filters/education-levels/')
    const rows = toArray<{ education_level_id: number; education_level: string }>(res.data)
    allEducationLevels.value = rows.map(r => ({ id: r.education_level_id, label: r.education_level }))
    // Trigger recompute of educationLevelOptions (computed below)
  } catch (err) {
    console.error('Failed to load education levels', err)
  }
}

/** Filtered education level options — recomputed reactively whenever
 *  examTypeId or allEducationLevels changes. No async race condition possible
 *  because this is a pure computed from already-loaded data.
 *
 *  Behaviour:
 *   - No exam type selected → show ALL education levels (full list)
 *   - School selected       → Class 1–12 only
 *   - Entrance selected     → Class 10/12, ITI, Diploma … Doctorate, Any Grad/PG
 *   - Job selected          → Class 10/12, ITI, Diploma, Graduate … Any Qualification
 */
const educationLevelOptions = computed<Option[]>(() => {
  if (!allEducationLevels.value.length) return [ALL_OPTION]

  const typeName = examTypeNameById.value[local.examTypeId] ?? ''
  const allowedIds = EDUCATION_LEVEL_IDS_BY_TYPE[typeName] ?? null

  // No exam type selected (typeName = '') → allowedIds = null → show all levels
  const filtered = allowedIds
    ? allEducationLevels.value.filter(r => allowedIds.includes(r.id))
    : allEducationLevels.value   // all levels when no exam type chosen

  return [ALL_OPTION, ...filtered.map(r => ({ label: r.label, value: String(r.id) }))]
})

// ── Stream options filtered by education level ─────────────────────────────
// Same problem as Education Level: Stream has no dedicated relevance table,
// and deriving it from existing Exam rows (education_level_id + stream_id
// both set) comes back empty whenever seed data doesn't yet have that
// combination — which is normal for Class 10, since board exams usually
// don't set a stream at all. So this uses the same client-side curated
// mapping approach as EDUCATION_LEVEL_IDS_BY_TYPE, sourced from:
//   1 General, 2 Science, 3 Commerce, 4 Arts, 5 Humanities, 42 Mathematics,
//   33 Home Science, 39 Physical Education, 45 Open Schooling,
//   46 Vocational, 47 Any Stream
const STREAM_IDS_BY_EDUCATION_LEVEL: Record<string, number[]> = {
  '1': [1, 47], '2': [1, 47], '3': [1, 47], '4': [1, 47], '5': [1, 47],
  '6': [1, 47], '7': [1, 47], '8': [1, 47], '9': [1, 47],       // Class 1–9: General + Any Stream
  '10': [42, 45, 46, 47],                                        // Class 10: Maths Olympiad/IMO, NIOS, Vocational, Any Stream
  '11': [2, 3, 4, 5, 33, 39, 46, 47],                            // Class 11: Science/Commerce/Arts/Humanities + optionals
  '12': [2, 3, 4, 5, 33, 39, 46, 47],                            // Class 12: same as Class 11
}

// ALL streams from backend — fetched once on mount, never re-fetched
const allStreams = ref<{ id: number; label: string }[]>([])

async function fetchStreams(): Promise<void> {
  try {
    const res = await api.get('/filters/streams/')
    const rows = toArray<{ stream_id: number; stream_name: string }>(res.data)
    allStreams.value = rows.map(r => ({ id: r.stream_id, label: r.stream_name }))
  } catch (err) {
    console.error('Failed to load streams', err)
  }
}

/** Filtered stream options — recomputed reactively whenever educationLevelId
 *  or allStreams changes.
 *   - No education level selected, or one outside the curated map (e.g. an
 *     Entrance/Job level like Graduate/PG with no stream data yet) → show
 *     every stream, unfiltered.
 *   - Class 1–12 selected → only the streams actually relevant to that class,
 *     per STREAM_IDS_BY_EDUCATION_LEVEL above. */
const streamOptions = computed<Option[]>(() => {
  if (!allStreams.value.length) return [ALL_OPTION]

  const allowedIds = STREAM_IDS_BY_EDUCATION_LEVEL[local.educationLevelId] ?? null

  const filtered = allowedIds
    ? allStreams.value.filter(s => allowedIds.includes(s.id))
    : allStreams.value

  return [ALL_OPTION, ...filtered.map(s => ({ label: s.label, value: String(s.id) }))]
})

async function fetchJobCategories(): Promise<void> {
  try {
    const res = await api.get('/filters/job-categories/')
    const rows = toArray<{ job_category_id: number; job_category_name: string }>(res.data)
    jobCategoryOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.job_category_name, value: String(r.job_category_id) }))]
  } catch (err) {
    console.error('Failed to load job categories', err)
  }
}

async function fetchStates(): Promise<void> {
  try {
    const res = await api.get('/filters/states/')
    const rows = toArray<{ state_id: number; state_name: string }>(res.data)
    stateOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.state_name, value: String(r.state_id) }))]
  } catch (err) {
    console.error('Failed to load states', err)
  }
}

async function fetchExamLevels(): Promise<void> {
  try {
    const res = await api.get('/filters/exam-levels/')
    const rows = toArray<{ level_id: number; level_name: string }>(res.data)
    levelOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.level_name, value: String(r.level_id) }))]
  } catch (err) {
    console.error('Failed to load exam levels', err)
  }
}

async function fetchBoards(stateId: string): Promise<void> {
  try {
    const res = await api.get('/filters/boards/', { params: stateId ? { state_id: stateId } : {} })
    const rows = toArray<{ board_id: number; board_name: string }>(res.data)
    boardOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.board_name, value: String(r.board_id) }))]
  } catch (err) {
    console.error('Failed to load boards', err)
    boardOptions.value = [ALL_OPTION]
  }
}

async function fetchFields(streamId: string): Promise<void> {
  if (!streamId) {
    fieldOptions.value = [ALL_OPTION]
    return
  }
  try {
    const res = await api.get('/filters/fields/', { params: { stream_id: streamId } })
    const rows = toArray<{ field_id: number; field_name: string }>(res.data)
    fieldOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.field_name, value: String(r.field_id) }))]
  } catch (err) {
    console.error('Failed to load fields', err)
    fieldOptions.value = [ALL_OPTION]
  }
}

async function fetchSubFields(fieldId: string): Promise<void> {
  if (!fieldId) {
    subFieldOptions.value = [ALL_OPTION]
    return
  }
  try {
    const res = await api.get('/filters/sub-fields/', { params: { field_id: fieldId } })
    const rows = toArray<{ sub_fields?: { sub_field_id: number; sub_field_name: string }[] }>(res.data)
    const subs = rows.flatMap(r => r.sub_fields ?? [])
    subFieldOptions.value = [ALL_OPTION, ...subs.map(s => ({ label: s.sub_field_name, value: String(s.sub_field_id) }))]
  } catch (err) {
    console.error('Failed to load sub-fields', err)
    subFieldOptions.value = [ALL_OPTION]
  }
}

/** Category options come from whichever table ExamCategoryListView resolves
 *  to (School/Entrance/Job) based on exam_type_id, narrowed further by
 *  education_level_id (School/Entrance) or job_category_id (Job) — same
 *  params ExamCategoryListView / ExamFilterView expect. */
async function fetchCategories(): Promise<void> {
  if (!local.examTypeId) {
    categoryOptions.value = [ALL_OPTION]
    return
  }
  const params: Record<string, string> = { exam_type_id: local.examTypeId }
  if (branchType.value === 'job' && local.jobCategoryId) {
    params.job_category_id = local.jobCategoryId
  }
  if ((branchType.value === 'school' || branchType.value === 'entrance') && local.educationLevelId) {
    params.education_level_id = local.educationLevelId
  }
  try {
    const res = await api.get('/filters/exam-categories/', { params })
    const rows = toArray<{ category_id: number; category_name: string }>(res.data)
    categoryOptions.value = [ALL_OPTION, ...rows.map(r => ({ label: r.category_name, value: String(r.category_id) }))]
  } catch (err) {
    console.error('Failed to load exam categories', err)
    categoryOptions.value = [ALL_OPTION]
  }
}

// ── Cascading resets — mirrors the dependency chain ExamFilterView expects ────

watch(() => local.examTypeId, () => {
  // Reset all dependent filters when exam type changes.
  // educationLevelOptions is a computed — it updates automatically
  // as soon as local.examTypeId changes, with no async fetch needed.
  local.categoryId      = ''
  local.jobCategoryId   = ''
  local.educationLevelId = ''
  local.streamId        = ''
  local.fieldId         = ''
  local.subFieldId      = ''
  local.boardId         = ''
  local.stateId         = ''
  local.levelId         = ''
  fieldOptions.value    = [ALL_OPTION]
  subFieldOptions.value = [ALL_OPTION]
  fetchCategories()
})

watch(() => local.educationLevelId, () => {
  local.categoryId = ''
  local.streamId = ''   // streamOptions computed re-filters automatically; no fetch needed
  fetchCategories()
})

watch(() => local.jobCategoryId, () => {
  local.categoryId = ''
  fetchCategories()
})

watch(() => local.streamId, (val) => {
  local.fieldId = ''
  local.subFieldId = ''
  fetchFields(val)
})

watch(() => local.fieldId, (val) => {
  local.subFieldId = ''
  fetchSubFields(val)
})

watch(() => local.stateId, (val) => {
  if (branchType.value === 'school') {
    local.boardId = ''
    fetchBoards(val)
  }
})

// ── Selected-option labels shown on each dropdown trigger ─────────────────────

function labelFor(options: Option[], value: string): string {
  return options.find(o => o.value === value)?.label ?? 'All'
}

const examTypeLabel = computed(() => labelFor(examTypeOptions.value, local.examTypeId))
const educationLevelLabel = computed(() => labelFor(educationLevelOptions.value, local.educationLevelId))
const streamLabel = computed(() => labelFor(streamOptions.value, local.streamId))
const fieldLabel = computed(() => labelFor(fieldOptions.value, local.fieldId))
const subFieldLabel = computed(() => labelFor(subFieldOptions.value, local.subFieldId))
const boardLabel = computed(() => labelFor(boardOptions.value, local.boardId))
const stateLabel = computed(() => labelFor(stateOptions.value, local.stateId))
const levelLabel = computed(() => labelFor(levelOptions.value, local.levelId))
const jobCategoryLabel = computed(() => labelFor(jobCategoryOptions.value, local.jobCategoryId))
const categoryLabel = computed(() => labelFor(categoryOptions.value, local.categoryId))

// ── Which dropdown (if any) is currently open ──────────────────────────────────
// Only one at a time, and the panel renders inline (normal document flow) so
// opening it pushes the filters below it down the page instead of covering them.

const openFilter = ref<string | null>(null)

function toggleFilter(name: string): void {
  openFilter.value = openFilter.value === name ? null : name
}

function handleDocumentClick(e: MouseEvent): void {
  const target = e.target as HTMLElement
  if (!target.closest('.filter-dropdown')) {
    openFilter.value = null
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
  fetchExamTypes()
  fetchEducationLevels()   // fetch ALL levels once; computed filters them per exam type
  fetchStreams()
  fetchJobCategories()
  fetchStates()
  fetchExamLevels()
  fetchBoards('')
})
onBeforeUnmount(() => document.removeEventListener('click', handleDocumentClick))

// ── Option selection — behaves like a single-select, closes after choosing ────

function selectExamType(value: string): void {
  local.examTypeId = value
  openFilter.value = null
}
function selectEducationLevel(value: string): void {
  local.educationLevelId = value
  openFilter.value = null
}
function selectStream(value: string): void {
  local.streamId = value
  openFilter.value = null
}
function selectField(value: string): void {
  local.fieldId = value
  openFilter.value = null
}
function selectSubField(value: string): void {
  local.subFieldId = value
  openFilter.value = null
}
function selectBoard(value: string): void {
  local.boardId = value
  openFilter.value = null
}
function selectState(value: string): void {
  local.stateId = value
  openFilter.value = null
}
function selectLevel(value: string): void {
  local.levelId = value
  openFilter.value = null
}
function selectJobCategory(value: string): void {
  local.jobCategoryId = value
  openFilter.value = null
}
function selectCategory(value: string): void {
  local.categoryId = value
  openFilter.value = null
}

// ── Emit & reset ──────────────────────────────────────────────────────────────

function idOrUndefined(value: string): number | undefined {
  return value ? Number(value) : undefined
}

function labelOrUndefined(options: Option[], value: string): string | undefined {
  if (!value) return undefined
  return options.find(o => o.value === value)?.label
}

function emitChange(): void {
  emit('change', {
    exam_type_id: idOrUndefined(local.examTypeId),
    exam_type_label: labelOrUndefined(examTypeOptions.value, local.examTypeId),
    category_id: idOrUndefined(local.categoryId),
    category_label: labelOrUndefined(categoryOptions.value, local.categoryId),
    job_category_id: idOrUndefined(local.jobCategoryId),
    job_category_label: labelOrUndefined(jobCategoryOptions.value, local.jobCategoryId),
    education_level_id: idOrUndefined(local.educationLevelId),
    education_level_label: labelOrUndefined(educationLevelOptions.value, local.educationLevelId),
    stream_id: idOrUndefined(local.streamId),
    stream_label: labelOrUndefined(streamOptions.value, local.streamId),
    field_id: idOrUndefined(local.fieldId),
    field_label: labelOrUndefined(fieldOptions.value, local.fieldId),
    sub_field_id: idOrUndefined(local.subFieldId),
    sub_field_label: labelOrUndefined(subFieldOptions.value, local.subFieldId),
    board_id: idOrUndefined(local.boardId),
    board_label: labelOrUndefined(boardOptions.value, local.boardId),
    state_id: idOrUndefined(local.stateId),
    state_label: labelOrUndefined(stateOptions.value, local.stateId),
    level_id: idOrUndefined(local.levelId),
    level_label: labelOrUndefined(levelOptions.value, local.levelId),
  } as ExamFilters)
}

/** Bound to the "Apply Filters" button specifically — separate from
 *  emitChange() so the parent can react (e.g. scroll to results) only on
 *  an explicit user click, not on mount or Reset. */
function applyFilters(): void {
  emitChange()
  emit('apply')
}

function resetFilters(): void {
  Object.assign(local, defaultState())
  openFilter.value = null
  fieldOptions.value = [ALL_OPTION]
  subFieldOptions.value = [ALL_OPTION]
  categoryOptions.value = [ALL_OPTION]
  fetchBoards('')
  emitChange()
}

emitChange()

defineExpose({ reset: resetFilters })
</script>

<style scoped>
/* Outer card: stretched by .exam-page-grid's align-items: stretch to match
   the Main column's full height, so the lavender background fills the
   whole row instead of stopping short and leaving blank page background
   below it. */
.filters-panel {
  /* Don't stretch to match the (much taller) results column via the
     grid's align-items: stretch — that's what was pushing Reset/Apply
     far down with a big empty gap above them. Let the panel size to
     its own content; .filters-sticky-inner below still caps itself to
     the viewport height and scrolls internally if the filter list
     itself is long. */
  height: auto;
  align-self: start;
  display: flex;
  flex-direction: column;
}

/* Inner wrapper: this is what actually sticks near the top of the
   viewport and caps itself to the visible viewport height. Reset/Apply
   stay pinned at the bottom of this box, with the filter list scrolling
   internally if it overflows — same behavior as before, just moved off
   the outer (now full-height) card. */
.filters-sticky-inner {
  position: sticky;
  top: 96px;
  max-height: calc(100vh - 96px - 24px); /* viewport minus top offset and some breathing room */
  /* Size to actual filter content, not the stretched outer card, so
     Reset/Apply sit right under the last filter instead of being pushed
     down by empty space. Still capped by max-height above, so a long
     filter list scrolls internally rather than pushing buttons off
     screen. */
  height: auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (max-width: 1300px) {
  .filters-panel { height: auto; }
  .filters-sticky-inner {
    position: static;
    max-height: none;
    height: auto;
  }
}

.filter-scroll-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px; /* prevent scrollbar overlap */
  /* Thin, subtle scrollbar */
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}

.filter-scroll-area::-webkit-scrollbar {
  width: 4px;
}

.filter-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.filter-scroll-area::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
  border-radius: 4px;
}

.filter-actions {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 10px;
  margin-top: 8px;
  flex-shrink: 0; /* never squish — always visible at the bottom */
  padding-top: 8px;
  border-top: 1px solid #f3f4f6;
  background: inherit; /* match panel background */
}

.reset-btn {
  background: #fff;
  border: 1px solid #ddd;
  color: #1e2536;
  font-weight: 700;
  font-size: 13px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.reset-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.apply-btn {
  background: #7c3aed;
  border: none;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.apply-btn:hover {
  background: #6d28d9;
}

/* ── Custom checkbox dropdown ─────────────────────────────────────────────────
   Renders as a normal block in the document flow (not position: absolute),
   so opening one dropdown pushes the filter groups below it further down
   the page instead of floating over and hiding them. */

.filter-dropdown-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13.5px;
  color: #1e2536;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.filter-dropdown-trigger:hover {
  border-color: #a78bfa;
}

.filter-dropdown--open .filter-dropdown-trigger {
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
}

.filter-dropdown-chevron {
  width: 14px;
  height: 14px;
  color: #6b7280;
  flex-shrink: 0;
  transition: transform 0.15s, color 0.15s;
}

.filter-dropdown-chevron--open {
  transform: rotate(180deg);
  color: #7c3aed;
}

.filter-dropdown-panel {
  margin-top: 6px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  padding: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  max-height: 230px;
  overflow-y: auto;
}

.filter-checkbox-row {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px;
  border-radius: 6px;
  font-size: 13.5px;
  color: #374151;
  cursor: pointer;
  transition: background 0.12s;
}

.filter-checkbox-row:hover {
  background: #f5f3ff;
}

.filter-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #7c3aed;
  cursor: pointer;
  flex-shrink: 0;
}
</style>