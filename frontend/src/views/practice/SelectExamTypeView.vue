<template>
  <div class="pt-page">
    <PracticeBreadcrumb
      :crumbs="[
        { label: 'Select Exam', to: { name: 'exams' } },
        { label: store.exam?.label ?? 'Exam', to: { name: 'exams' } },
        { label: 'Select Type' },
      ]"
      :active-index="2"
    />

    <h2 class="pt-title">Select Exam Type</h2>
    <p class="pt-subtitle">Choose the type of exam you want to prepare for</p>

    <div v-if="checking" class="checking-banner">Checking available exams…</div>
    <div v-else-if="loadError" class="checking-banner error">
      {{ loadError }} <button class="retry-link" @click="loadAvailableExams">Retry</button>
    </div>

    <div v-if="examTypes.length === 0" class="no-types">
      <p>No types available for this exam. <RouterLink :to="{ name: 'exams' }">Go back</RouterLink></p>
    </div>

    <div v-else class="type-grid">
      <div
        v-for="type in examTypes"
        :key="type.id"
        class="type-card"
        :class="{ selected: selectedStaticId === type.id }"
        @click="selectType(type)"
      >
        <div class="type-radio" :class="{ on: selectedStaticId === type.id }"></div>
        <div class="type-icon">{{ type.icon }}</div>
        <h4>{{ type.label }}</h4>
        <p>{{ type.description }}</p>
        <ul>
          <li v-for="point in type.points" :key="point">&#10003; {{ point }}</li>
        </ul>
      </div>
    </div>

    <p v-if="selectError" class="select-error">{{ selectError }}</p>

    <div class="pt-footer">
      <button class="back-btn" @click="router.push({ name: 'exams' })">&larr; Back</button>
      <button class="continue-btn" :disabled="!store.examType" @click="goNext">
        Continue &rarr;
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PracticeBreadcrumb from '@/components/practice/PracticeBreadcrumb.vue'
import api from '@/services/axiosInstance'
import { usePracticeTestStore } from '@/stores/practiceTest'

const router = useRouter()
const store = usePracticeTestStore()

// No hard redirect — just show "go back" if exam missing

interface ExamTypeOption {
  id: string          // cosmetic id, matches the UI card only — NOT a real PK
  label: string
  icon: string
  description: string
  points: string[]
  // exam_code value(s) (case-insensitive) that identify the REAL Exam row
  // this card should resolve to. These must match whatever --exam-code
  // you passed to `load_syllabus` when loading that exam's data.
  examCodes: string[]
}

const examTypeMap: Record<string, ExamTypeOption[]> = {
  jee: [
    { id: 'jee-mains',    label: 'JEE Mains',    icon: '📝', description: 'First stage entrance for NITs, IIITs & CFTIs.', points: ['90 Questions', '3 Hours', 'Online CBT'], examCodes: ['JEE_MAIN', 'JEE_MAINS'] },
    { id: 'jee-advanced', label: 'JEE Advanced', icon: '🏆', description: 'Second stage for admission to IITs.',           points: ['2 Papers', 'Higher Difficulty', 'IIT Entry'], examCodes: ['JEE_ADVANCED'] },
  ],
  neet: [
    { id: 'neet-ug', label: 'NEET UG', icon: '🩺', description: 'For MBBS, BDS & other UG medical courses.', points: ['180 Questions', '3 Hours 20 Min', 'Pen & Paper'], examCodes: ['NEET_UG'] },
    { id: 'neet-pg', label: 'NEET PG', icon: '🔬', description: 'For MD, MS & PG Diploma admissions.',       points: ['200 Questions', '3 Hours 30 Min', 'Computer Based'], examCodes: ['NEET_PG'] },
  ],
  upsc: [
    { id: 'upsc-prelims', label: 'UPSC Prelims', icon: '📄', description: 'Screening stage with objective type papers.', points: ['2 Papers', '400 Marks', 'Objective Type'], examCodes: ['UPSC_PRELIMS'] },
    { id: 'upsc-mains',   label: 'UPSC Mains',   icon: '✍️', description: 'Written examination with descriptive papers.', points: ['9 Papers', '1750 Marks', 'Descriptive'], examCodes: ['UPSC_MAINS'] },
  ],
  ssc: [
    { id: 'ssc-cgl',  label: 'SSC CGL',  icon: '📊', description: 'Combined Graduate Level for Group B & C posts.', points: ['4 Tiers', 'Graduate Level', 'Group B & C'], examCodes: ['SSC_CGL'] },
    { id: 'ssc-chsl', label: 'SSC CHSL', icon: '📋', description: 'Combined Higher Secondary Level posts.',          points: ['3 Tiers', '12th Pass', 'Group C & D'], examCodes: ['SSC_CHSL'] },
    { id: 'ssc-mts',  label: 'SSC MTS',  icon: '🗂️', description: 'Multi Tasking Staff non-technical posts.',       points: ['2 Papers', '10th Pass', 'Group C'], examCodes: ['SSC_MTS'] },
  ],
  banking: [
    { id: 'ibps-po',  label: 'IBPS PO',  icon: '🏦', description: 'Probationary Officer exam for public sector banks.', points: ['Prelims + Mains', '200 Marks', 'Interview'], examCodes: ['IBPS_PO'] },
    { id: 'sbi-po',   label: 'SBI PO',   icon: '💳', description: 'State Bank of India PO recruitment.',               points: ['3 Phases', 'Group Exercise', 'Interview'], examCodes: ['SBI_PO'] },
    { id: 'ibps-clerk', label: 'IBPS Clerk', icon: '📑', description: 'Clerk posts in public sector banks.',           points: ['Prelims + Mains', 'No Interview', 'Clerical'], examCodes: ['IBPS_CLERK'] },
  ],
  railways: [
    { id: 'rrb-ntpc', label: 'RRB NTPC',    icon: '🚂', description: 'Non-Technical Popular Category posts.',     points: ['CBT 1 + 2', 'Graduate Level', 'Group B & C'], examCodes: ['RRB_NTPC'] },
    { id: 'rrb-je',   label: 'RRB JE',      icon: '🔧', description: 'Junior Engineer recruitment.',              points: ['CBT 1 + 2', 'Diploma/Degree', 'Technical'], examCodes: ['RRB_JE'] },
    { id: 'rrb-group-d', label: 'RRB Group D', icon: '🛤️', description: 'Group D posts across railway zones.', points: ['CBT + PET', '10th Pass', 'Group D'], examCodes: ['RRB_GROUP_D'] },
  ],
  gate: [
    { id: 'gate-cs',  label: 'GATE CS',  icon: '💻', description: 'Computer Science & Information Technology.',      points: ['65 Questions', '3 Hours', 'MCQ + NAT'], examCodes: ['GATE_CS'] },
    { id: 'gate-ece', label: 'GATE ECE', icon: '📡', description: 'Electronics & Communication Engineering.',        points: ['65 Questions', '3 Hours', 'MCQ + NAT'], examCodes: ['GATE_ECE'] },
    { id: 'gate-me',  label: 'GATE ME',  icon: '⚙️', description: 'Mechanical Engineering stream.',                 points: ['65 Questions', '3 Hours', 'MCQ + NAT'], examCodes: ['GATE_ME'] },
  ],
  cat: [
    { id: 'cat-full', label: 'CAT', icon: '📈', description: 'Common Admission Test for IIMs & top B-schools.', points: ['66 Questions', '2 Hours', '3 Sections'], examCodes: ['CAT'] },
  ],
  cuet: [
    { id: 'cuet-ug', label: 'CUET UG', icon: '🎓', description: 'Undergraduate admission to central universities.', points: ['Domain + General', 'MCQ Based', 'Central Universities'], examCodes: ['CUET_UG'] },
    { id: 'cuet-pg', label: 'CUET PG', icon: '📚', description: 'Postgraduate admission to central universities.',  points: ['Subject Specific', 'MCQ Based', 'PG Admission'], examCodes: ['CUET_PG'] },
  ],
  nda: [
    { id: 'nda-1', label: 'NDA Paper I',  icon: '🔢', description: 'Mathematics paper — 120 questions.', points: ['120 Questions', '2.5 Hours', '300 Marks'], examCodes: ['NDA_1'] },
    { id: 'nda-2', label: 'NDA Paper II', icon: '📖', description: 'General Ability Test — 150 questions.', points: ['150 Questions', '2.5 Hours', '600 Marks'], examCodes: ['NDA_2'] },
  ],
}

const examTypes = computed<ExamTypeOption[]>(
  () => examTypeMap[store.exam?.id ?? ''] ?? []
)

interface RawExam {
  exam_id: number
  exam_code: string
  exam_name: string
}

// Real Exam rows for this category, fetched once on mount. Clicking a
// static card just matches against this list locally — no network call
// per click.
const availableExams = ref<RawExam[]>([])
const checking        = ref(true)
const loadError       = ref('')
const selectError     = ref('')
const selectedStaticId = ref<string | null>(null)

async function loadAvailableExams(): Promise<void> {
  const category = store.exam?.category
  if (!category) {
    loadError.value = 'No exam selected.'
    checking.value = false
    return
  }
  checking.value = true
  loadError.value = ''
  try {
    const res = await api.get('/exams/', { params: { exam_category: category } })
    availableExams.value = res.data.results
  } catch {
    loadError.value = 'Failed to check available exam types. You can still try selecting one.'
  } finally {
    checking.value = false
  }
}

onMounted(loadAvailableExams)

function selectType(type: ExamTypeOption): void {
  selectError.value = ''
  const match = availableExams.value.find((e) =>
    type.examCodes.some((code) => e.exam_code.trim().toUpperCase() === code.toUpperCase())
  )
  if (!match) {
    selectError.value = 'This exam type is not available yet. Please pick another.'
    selectedStaticId.value = null
    return
  }
  selectedStaticId.value = type.id
  store.setExamType({ id: String(match.exam_id), label: match.exam_name })
}

function goNext(): void {
  if (!store.examType) return
  router.push({ name: 'practice-test-type' })
}
</script>

<style scoped>
.pt-page { max-width: 900px; margin: 0 auto; }
.pt-title  { font-size: 19px; font-weight: 800; color: #1e2536; margin: 0 0 4px; }
.pt-subtitle { font-size: 13px; color: #6b7280; margin: 0 0 20px; }

.no-types { padding: 40px; text-align: center; color: #6b7280; font-size: 14px; }
.no-types a { color: #7c3aed; }

.checking-banner {
  font-size: 12.5px; color: #6b7280; margin-bottom: 12px;
}
.checking-banner.error { color: #b91c1c; }
.retry-link {
  background: none; border: none; color: #7c3aed; font-weight: 600;
  font-size: 12.5px; cursor: pointer;
  user-select: none; padding: 0; margin-left: 4px; text-decoration: underline;
}

.select-error {
  color: #b91c1c; font-size: 13px; margin: -10px 0 16px;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
@media (max-width: 700px) { .type-grid { grid-template-columns: 1fr; } }

.type-card {
  position: relative;
  background: #fff;
  border: 1.5px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s, background 0.15s;
}
.type-card:hover { border-color: #c4b5fd; }
.type-card.selected { border-color: #7c3aed; background: #f5f3ff; }

.type-radio {
  position: absolute; top: 14px; right: 14px;
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid #d1d5db;
}
.type-radio.on {
  border-color: #7c3aed;
  background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%);
}

.type-icon { font-size: 24px; margin-bottom: 10px; }
.type-card h4  { font-size: 15px; font-weight: 700; color: #1e2536; margin: 0 0 4px; }
.type-card p   { font-size: 12px; color: #6b7280; margin: 0 0 10px; line-height: 1.4; }
.type-card ul  { list-style: none; margin: 0; padding: 0; font-size: 12px; color: #374151; }
.type-card ul li { margin-bottom: 3px; }

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