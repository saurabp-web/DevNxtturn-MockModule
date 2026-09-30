<template>
  <div class="wizard-panel">
    <!-- FIXED: merged the old Step 2 (Classification) and Step 3 (Academic
         Mapping) into one step. They were two full pages of cascading
         dropdowns with duplicate "Selected ..." summary cards describing
         overlapping taxonomy (Exam Category vs Education Level/Stream/Field
         cover a lot of the same ground) — collapsing them removes a step
         of admin fatigue with no loss of data collected. -->
    <h2 class="panel-title">2. Classification &amp; Academic Mapping</h2>
    <div class="panel-grid">
      <div class="col">
        <p class="group-heading">Classification</p>
        <div class="field">
          <label>Exam Type <span class="req">*</span></label>
          <select v-model="form.classification.examType">
            <option value="" disabled>Select exam type</option>
            <option v-for="t in examTypes" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Exam Category <span class="req">*</span></label>
          <input
            v-model="form.classification.examCategory"
            type="text"
            placeholder="e.g. Engineering, Medical, SSC"
          />
        </div>
        <div class="field">
          <label>Exam Level <span class="req">*</span></label>
          <select v-model="form.classification.examLevel">
            <option value="" disabled>Select exam level</option>
            <option v-for="l in examLevels" :key="l.id" :value="l.id">{{ l.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Conducting Body <span class="req">*</span></label>
          <input
            v-model="form.classification.conductingBody"
            type="text"
            placeholder="e.g. NTA, UPSC, SSC"
          />
        </div>

        <p class="group-heading" style="margin-top:22px">Academic Mapping</p>
        <div class="field">
          <label>Education Level <span class="req">*</span></label>
          <select v-model="form.academicMapping.educationLevel" :disabled="!form.classification.examType">
            <option value="" disabled>
              {{ form.classification.examType ? 'Select education level' : 'Select an Exam Type first' }}
            </option>
            <option v-for="e in educationLevels" :key="e.id" :value="e.id">{{ e.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Stream <span class="req">*</span></label>
          <select v-model="form.academicMapping.stream" :disabled="!form.academicMapping.educationLevel">
            <option value="" disabled>
              {{ form.academicMapping.educationLevel ? 'Select stream' : 'Select an Education Level first' }}
            </option>
            <option v-for="s in streams" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>Field <span class="req">*</span></label>
          <select v-model="form.academicMapping.field" :disabled="!form.academicMapping.stream">
            <option value="" disabled>
              {{ form.academicMapping.stream ? 'Select field' : 'Select a Stream first' }}
            </option>
            <option v-for="f in fields" :key="f.id" :value="f.id">{{ f.name }}</option>
          </select>
        </div>
        <!-- Sub Field intentionally not collected — kept in the shared
             form shape (sent as null) so nothing downstream breaks. -->
      </div>

      <div class="col">
        <div class="summary-card">
          <p class="summary-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 2-3 4"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            Selected Classification
          </p>
          <div class="summary-row">
            <span class="summary-label">Exam Type</span>
            <span class="summary-value">{{ examTypeName || '—' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Category</span>
            <span class="summary-value">{{ form.classification.examCategory || '—' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Exam Level</span>
            <span class="summary-value">{{ examLevelName || '—' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Conducting Body</span>
            <span class="summary-value">{{ form.classification.conductingBody || '—' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Education Level</span>
            <span class="summary-value">{{ educationLevelName || '—' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Stream</span>
            <span class="summary-value">{{ streamName || '—' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Field</span>
            <span class="summary-value">{{ fieldName || '—' }}</span>
          </div>
        </div>
        <p v-if="loadError" class="load-error-text">{{ loadError }}</p>
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
import {
  fetchExamTypes,
  fetchExamLevels,
  fetchEducationLevels,
  fetchStreams,
  fetchFields,
  type Option,
} from '@/services/filtersApi'

const props = defineProps<{ form: any }>()
defineEmits(['next', 'back'])

const examTypes = ref<Option[]>([])
const examLevels = ref<Option[]>([])
const educationLevels = ref<Option[]>([])
const streams = ref<Option[]>([])
const fields = ref<Option[]>([])
const loadError = ref('')

const examTypeName = computed(
  () => examTypes.value.find((t) => t.id === props.form.classification.examType)?.name,
)
const examLevelName = computed(
  () => examLevels.value.find((l) => l.id === props.form.classification.examLevel)?.name,
)
const educationLevelName = computed(
  () => educationLevels.value.find((e) => e.id === props.form.academicMapping.educationLevel)?.name,
)
const streamName = computed(
  () => streams.value.find((s) => s.id === props.form.academicMapping.stream)?.name,
)
const fieldName = computed(
  () => fields.value.find((f) => f.id === props.form.academicMapping.field)?.name,
)

// Education Level list depends on the Exam Type chosen above.
async function loadEducationLevels() {
  if (!props.form.classification.examType) {
    educationLevels.value = []
    return
  }
  try {
    educationLevels.value = await fetchEducationLevels(props.form.classification.examType)
  } catch (err: any) {
    loadError.value = err.message || 'Failed to load education levels.'
  }
}

// Stream list depends on Exam Type + the Education Level just picked.
async function loadStreams() {
  if (!props.form.academicMapping.educationLevel) {
    streams.value = []
    return
  }
  try {
    streams.value = await fetchStreams(
      props.form.classification.examType,
      props.form.academicMapping.educationLevel,
    )
  } catch (err: any) {
    loadError.value = err.message || 'Failed to load streams.'
  }
}

// Field list depends on the Stream just picked.
async function loadFields() {
  if (!props.form.academicMapping.stream) {
    fields.value = []
    return
  }
  try {
    fields.value = await fetchFields(props.form.academicMapping.stream)
  } catch (err: any) {
    loadError.value = err.message || 'Failed to load fields.'
  }
}

onMounted(async () => {
  try {
    const [types, levels] = await Promise.all([fetchExamTypes(), fetchExamLevels()])
    examTypes.value = types
    examLevels.value = levels
  } catch (err: any) {
    loadError.value = err.message || 'Failed to load classification options.'
  }
  loadEducationLevels()
  // If the wizard was pre-filled (e.g. editing a draft), also load the
  // dependent lists so existing selections resolve to real names instead
  // of showing blank until the user touches a dropdown.
  if (props.form.academicMapping.educationLevel) loadStreams()
  if (props.form.academicMapping.stream) loadFields()
})

// Cascade: changing Exam Type invalidates Education Level -> Stream -> Field.
watch(
  () => props.form.classification.examType,
  () => {
    props.form.academicMapping.educationLevel = ''
    props.form.academicMapping.stream = ''
    props.form.academicMapping.field = ''
    streams.value = []
    fields.value = []
    loadEducationLevels()
  },
)

// Cascade: changing Education Level invalidates Stream -> Field.
watch(
  () => props.form.academicMapping.educationLevel,
  () => {
    props.form.academicMapping.stream = ''
    props.form.academicMapping.field = ''
    fields.value = []
    loadStreams()
  },
)

// Cascade: changing Stream invalidates Field.
watch(
  () => props.form.academicMapping.stream,
  () => {
    props.form.academicMapping.field = ''
    loadFields()
  },
)
</script>

<style scoped>
@import './wizard-panel.css';

.group-heading {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9CA3AF;
  margin: 0 0 10px;
}
.field select:disabled {
  background: #F9FAFB;
  color: #9CA3AF;
  cursor: not-allowed;
}
.load-error-text {
  margin-top: 10px;
  font-size: 12px;
  color: #DC2626;
}
</style>