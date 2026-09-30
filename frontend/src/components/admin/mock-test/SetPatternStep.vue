<template>
  <section class="card">
    <header class="card-head">
      <span class="card-icon">⚙️</span>
      <h3>Set Pattern</h3>
    </header>

    <div class="pattern-grid">
      <div class="pattern-settings">
        <p class="sub-title">Pattern Settings</p>

        <div class="grid-2">
          <div class="field">
            <label>Total Questions <span class="req">*</span></label>
            <input v-model="form.totalQuestions" type="number" placeholder="Enter total number of questions" />
          </div>
          <div class="field">
            <label>Total Marks</label>
            <input v-model="form.totalMarks" type="number" placeholder="Enter total marks" />
          </div>
        </div>
        <p v-if="form.subjects.length > 0 && (form.totalQuestions || form.totalMarks)" class="distribute-hint">
          ✦ Distributing equally across {{ form.subjects.length }} subjects. Edit any row to override.
        </p>

        <div class="grid-2">
          <div class="field">
            <label>Marks Per Question <span class="req">*</span></label>
            <input v-model="form.marksPerQuestion" type="number" placeholder="Enter marks per question" />
          </div>
          <div class="field">
            <label>Negative Marking</label>
            <select v-model="form.negativeMarking">
              <option value="" disabled>Select negative marking</option>
              <option v-for="n in negativeOptions" :key="n" :value="n">{{ n }}</option>
            </select>
          </div>
        </div>

        <div class="field">
          <label>Sectional Time (Optional)</label>
          <div class="toggle-row">
            <button type="button" class="toggle" :class="{ on: form.sectionalTime }" @click="form.sectionalTime = !form.sectionalTime">
              <span class="knob"></span>
            </button>
            <span>Enabled</span>
          </div>
          <input v-model="form.sectionalMinutes" type="number" placeholder="Enter time in minutes" class="mt-8" />
        </div>
      </div>

      <div class="subjects-panel">
        <p class="sub-title">Subjects &amp; Questions</p>

        <!-- Loading state -->
        <div v-if="loadingSubjects" class="subjects-loading">
          <span class="spinner"></span> Loading subjects for this examu2026
        </div>

        <!-- Error / info banner -->
        <div v-if="subjectsError && !loadingSubjects" class="subjects-notice">
          u26a0 {{ subjectsError }}
        </div>

        <table v-if="!loadingSubjects">
          <thead>
            <tr><th>#</th><th>Subject</th><th>No. of Questions</th><th>Marks</th><th>Action</th></tr>
          </thead>
          <tbody>
            <!-- Real subject rows -->
            <tr v-for="(s, i) in form.subjects" :key="i">
              <td>{{ i + 1 }}</td>
              <td>
                <input
                  v-if="editingIndex === i"
                  v-model="s.name"
                  type="text"
                  class="cell-input cell-input-name"
                  placeholder="Subject name"
                  @blur="editingIndex = null"
                />
                <span v-else>{{ s.name }}</span>
              </td>
              <td>
                <input
                  v-if="editingIndex === i"
                  v-model="s.questions"
                  type="number"
                  class="cell-input"
                  @blur="editingIndex = null"
                />
                <span v-else>{{ s.questions || '-' }}</span>
              </td>
              <td>
                <input
                  v-if="editingIndex === i"
                  v-model="s.marks"
                  type="number"
                  class="cell-input"
                  @blur="editingIndex = null"
                />
                <span v-else>{{ s.marks || '-' }}</span>
              </td>
              <td class="action-cell">
                <button class="edit-btn" @click="editingIndex = editingIndex === i ? null : i">✎</button>
                <button class="edit-btn remove-btn" title="Remove subject" @click="removeSubject(i)">✕</button>
              </td>
            </tr>

            <!-- Inline "add new subject" row — always the next row, starting at #1 -->
            <tr class="add-row">
              <td>{{ form.subjects.length + 1 }}</td>
              <td>
                <input
                  v-model="newSubjectName"
                  type="text"
                  class="cell-input cell-input-name"
                  placeholder="New subject name"
                  @keyup.enter="addSubject"
                />
              </td>
              <td colspan="2">
                <button class="add-subject-btn" :disabled="!newSubjectName.trim()" @click="addSubject">
                  Add Subject
                </button>
              </td>
              <td><button class="edit-btn plus" :disabled="!newSubjectName.trim()" @click="addSubject">+</button></td>
            </tr>
          </tbody>
        </table>

        <p v-if="form.subjects.length === 0 && !loadingSubjects" class="hint-text">
          No subjects added yet. Type a subject name above and click "Add Subject" to get started.
        </p>
      </div>
    </div>

    <div class="actions actions-between">
      <button class="btn-secondary" @click="$emit('back')">← Previous Step</button>
      <button class="btn-primary" @click="$emit('next')">Next Step →</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, watch, ref, onMounted } from 'vue'
import { fetchSubjectsForExam } from '@/services/mockTestApi'

const props = defineProps<{
  modelValue?: Record<string, any>
  /** exam_id passed down from the parent wizard (set in SelectExamStep) */
  examId?: number | string | null
}>()
const emit = defineEmits(['update:modelValue', 'back', 'next'])

const form = reactive({
  totalQuestions: '',
  totalMarks: '',
  marksPerQuestion: '',
  negativeMarking: '',
  sectionalTime: false,
  sectionalMinutes: '',
  subjects: [] as { name: string; subject_id?: number; questions: string | number; marks: string | number }[],
  ...props.modelValue,
})

// Strip blank/placeholder rows that may arrive via modelValue
form.subjects = (form.subjects || []).filter((s) => !!s?.name?.trim?.())

watch(form, (val) => emit('update:modelValue', { ...val }), { deep: true })

// Edit mode: CreateMockTestView fetches the existing mock test
// asynchronously and only THEN fills in modelValue — but `form` above
// was already built from an empty modelValue at mount time. This
// watcher re-hydrates the pattern fields (and subjects, if the saved
// mock test already had a pattern) the moment real data arrives,
// exactly once, so it never overwrites the admin's own edits
// afterward. loadSubjectsForExam()'s existing "don't overwrite if
// form.subjects.length > 0" guard means hydrating real subjects here
// automatically prevents the auto-fetch-from-exam from clobbering them.
let hydratedFromParent = !!(
  props.modelValue &&
  (props.modelValue.totalQuestions || (props.modelValue.subjects && props.modelValue.subjects.length))
)
watch(
  () => props.modelValue,
  (val) => {
    if (hydratedFromParent || !val) return
    if (val.totalQuestions || val.marksPerQuestion || (val.subjects && val.subjects.length)) {
      Object.assign(form, val)
      form.subjects = (form.subjects || []).filter((s) => !!s?.name?.trim?.())
      hydratedFromParent = true
    }
  },
  { deep: true }
)

const negativeOptions = ['None', '-1', '-0.5', '-0.25']
const editingIndex = ref<number | null>(null)
const newSubjectName = ref('')

// ── Auto-distribute questions & marks equally across subjects ─────────────
// Fires whenever totalQuestions, totalMarks, or the subject list changes.
// Remainders (from non-even division) are added to the last subject so the
// totals always add up exactly.
watch(
  () => [form.totalQuestions, form.totalMarks, form.subjects.length] as const,
  ([tq, tm, count]) => {
    if (!count) return

    const totalQ = parseInt(String(tq), 10)
    const totalM = parseInt(String(tm), 10)

    // Distribute questions
    if (!isNaN(totalQ) && totalQ > 0) {
      const baseQ = Math.floor(totalQ / count)
      const remQ  = totalQ - baseQ * count
      form.subjects.forEach((s, i) => {
        s.questions = i === count - 1 ? baseQ + remQ : baseQ
      })
    } else {
      // Clear if field is emptied
      if (!tq) form.subjects.forEach(s => { s.questions = '' })
    }

    // Distribute marks
    if (!isNaN(totalM) && totalM > 0) {
      const baseM = Math.floor(totalM / count)
      const remM  = totalM - baseM * count
      form.subjects.forEach((s, i) => {
        s.marks = i === count - 1 ? baseM + remM : baseM
      })
    } else {
      if (!tm) form.subjects.forEach(s => { s.marks = '' })
    }
  }
)

// ── Auto-load subjects from the exam selected in Step 2 ──────
const loadingSubjects = ref(false)
const subjectsError = ref('')

async function loadSubjectsForExam() {
  if (!props.examId) return
  // If the admin already has subjects (e.g. coming back to this step), don't overwrite.
  if (form.subjects.length > 0) return

  loadingSubjects.value = true
  subjectsError.value = ''
  try {
    const result = await fetchSubjectsForExam(props.examId)
    const fetched = result.subjects ?? []
    if (fetched.length === 0) {
      subjectsError.value = 'No subjects found for this exam. Add them manually below.'
      return
    }
    // Populate the table with exam subjects; leave questions/marks blank for admin to fill.
    form.subjects = fetched.map((s) => ({
      name: s.subject_name,
      subject_id: s.subject_id,
      questions: '',
      marks: '',
    }))
  } catch (e) {
    subjectsError.value = 'Could not load subjects. You can add them manually below.'
  } finally {
    loadingSubjects.value = false
  }
}

onMounted(() => {
  loadSubjectsForExam()
})

// If parent wizard changes the examId after mount (edge case: user goes
// back and picks a different exam), reload subjects.
watch(() => props.examId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    form.subjects = []  // clear old exam's subjects
    loadSubjectsForExam()
  }
})

function addSubject() {
  const name = newSubjectName.value.trim()
  if (!name) return
  form.subjects.push({ name, questions: '', marks: '' })
  newSubjectName.value = ''
}

function removeSubject(index: number) {
  form.subjects.splice(index, 1)
  if (editingIndex.value === index) editingIndex.value = null
}
</script>

<style scoped>
.card { background: #fff; border: 1px solid #ecedf3; border-radius: 12px; padding: 22px 24px 26px; }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
.card-icon { font-size: 15px; }
.card-head h3 { font-size: 14.5px; margin: 0; }
.sub-title { font-size: 12.5px; font-weight: 700; color: #1f2333; margin: 0 0 14px; }
.pattern-grid { display: grid; grid-template-columns: 1fr 1.4fr; gap: 22px; align-items: start; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.field label { font-size: 12.5px; font-weight: 600; color: #4b4f66; }
.req { color: #ef4444; }
input, select { border: 1px solid #dfe1ea; border-radius: 8px; padding: 9px 12px; font-size: 13px; outline: none; font-family: inherit; width: 100%; background: #fff; }
input:focus, select:focus { border-color: #a78bfa; box-shadow: 0 0 0 3px #ede9fe; }
.mt-8 { margin-top: 8px; }
.toggle-row { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.toggle { width: 40px; height: 22px; border-radius: 999px; background: #d8dae6; border: none; position: relative; cursor: pointer; padding: 0; }
.toggle.on { background: #6d28d9; }
.knob { position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform 0.15s; }
.toggle.on .knob { transform: translateX(18px); }
.subjects-panel { border: 1px solid #ecedf3; border-radius: 10px; padding: 16px; }
.hint-text { font-size: 12px; color: #8a8fa3; margin: 10px 0 0; }
.distribute-hint { font-size: 11.5px; color: #6d28d9; background: #f5f3ff; border: 1px solid #ede9fe; border-radius: 6px; padding: 6px 10px; margin: -6px 0 14px; }
.subjects-loading { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: #6d28d9; padding: 12px 0; }
.subjects-notice { font-size: 12px; color: #b45309; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #ede9fe; border-top-color: #6d28d9; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { text-align: left; color: #a6abc0; font-weight: 600; padding: 6px 8px; border-bottom: 1px solid #ecedf3; }
td { padding: 9px 8px; border-bottom: 1px solid #f3f3f8; color: #1f2333; }
.cell-input { padding: 4px 6px; font-size: 12px; width: 70px; }
.cell-input-name { width: 100%; min-width: 140px; }
.action-cell { display: flex; gap: 6px; }
.edit-btn { border: 1px solid #dfe1ea; background: #fff; border-radius: 6px; width: 26px; height: 26px; cursor: pointer; font-size: 12px; color: #6d28d9; }
.edit-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.remove-btn { color: #dc2626; }
.add-row td { border-bottom: none; }
.add-subject-btn { border: none; background: transparent; color: #6d28d9; font-weight: 600; cursor: pointer; padding: 0; font-size: 12.5px; }
.add-subject-btn:disabled { color: #c4c8d6; cursor: not-allowed; }
.edit-btn.plus { color: #6d28d9; font-weight: 700; }
.actions { display: flex; margin-top: 22px; }
.actions-between { justify-content: space-between; }
.btn-primary { background: #6d28d9; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #5b21b6; }
.btn-secondary { background: #fff; color: #4b4f66; border: 1px solid #dfe1ea; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-secondary:hover { background: #f6f7fb; }
</style>