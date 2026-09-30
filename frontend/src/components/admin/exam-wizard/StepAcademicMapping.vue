<template>
  <div class="wizard-panel">
    <h2 class="panel-title">3. Academic Mapping</h2>
    <div class="panel-grid">
      <div class="col">
        <div class="field">
          <label>Education Level <span class="req">*</span></label>
          <select v-model="form.academicMapping.educationLevel" :disabled="!form.classification.examType">
            <option value="" disabled>
              {{ form.classification.examType ? 'Select education level' : 'Select an Exam Type first (Step 2)' }}
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
        <!-- Sub Field removed — not required per current requirements.
             form.academicMapping.subField is left in the shared form
             shape (still sent to the backend as null) so nothing else
             breaks, it's just no longer collected in the UI. -->
      </div>

      <div class="col">
        <div class="summary-card">
          <p class="summary-card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5-10-5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/></svg>
            Selected Academic Mapping
          </p>
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
import { fetchEducationLevels, fetchStreams, fetchFields, type Option } from '@/services/filtersApi'

const props = defineProps<{ form: any }>()
defineEmits(['next', 'back'])

const educationLevels = ref<Option[]>([])
const streams = ref<Option[]>([])
const fields = ref<Option[]>([])
const loadError = ref('')

const educationLevelName = computed(
  () => educationLevels.value.find((e) => e.id === props.form.academicMapping.educationLevel)?.name,
)
const streamName = computed(
  () => streams.value.find((s) => s.id === props.form.academicMapping.stream)?.name,
)
const fieldName = computed(
  () => fields.value.find((f) => f.id === props.form.academicMapping.field)?.name,
)

// Education Level list depends on the Exam Type chosen back in Step 2.
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

onMounted(() => {
  loadEducationLevels()
  // If the wizard was pre-filled (e.g. editing a draft), also load the
  // dependent lists so the existing selections resolve to real names
  // instead of showing blank until the user touches a dropdown.
  if (props.form.academicMapping.educationLevel) loadStreams()
  if (props.form.academicMapping.stream) loadFields()
})

// Cascade: changing Exam Type (back in Step 2) invalidates Education
// Level -> Stream -> Field, since all three are scoped to it.
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