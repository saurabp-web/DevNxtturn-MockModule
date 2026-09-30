<template>
  <section class="card">
    <header class="card-head">
      <span class="card-icon">🗒️</span>
      <h3>Basic Details</h3>
    </header>

    <div class="grid-2">
      <div class="field">
        <label>Mock Test Name <span class="req">*</span></label>
        <input v-model="form.name" type="text" placeholder="Enter mock test name" />
      </div>
      <div class="field">
        <label>Year (Optional)</label>
        <select v-model="form.year">
          <option value="" disabled>Select year</option>
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
    </div>

    <div class="field">
      <label>Description (Optional)</label>
      <textarea v-model="form.description" rows="3" placeholder="Enter description about this mock test"></textarea>
    </div>

    <!-- <div class="grid-2">
      <div class="field">
        <label>Total Marks (Optional)</label>
        <input v-model="form.totalMarks" type="number" placeholder="Enter total marks" />
      </div>
      <div class="field">
        <label>Duration (Minutes) (Optional)</label>
        <input v-model="form.duration" type="number" placeholder="Enter duration in minutes" />
      </div>
    </div> -->

    <div class="field toggle-field">
      <label>Status</label>
      <div class="toggle-row">
        <button type="button" class="toggle" :class="{ on: form.active }" @click="form.active = !form.active">
          <span class="knob"></span>
        </button>
        <span>Active</span>
      </div>
    </div>

    <div class="actions actions-end">
      <button class="btn-primary" @click="$emit('next')">Next Step →</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

const props = defineProps<{ modelValue?: Record<string, any> }>()
const emit = defineEmits(['update:modelValue', 'next'])

const form = reactive({
  name: '',
  year: '',
  description: '',
  totalMarks: '',
  duration: '',
  active: true,
  ...props.modelValue
})

watch(form, (val) => emit('update:modelValue', { ...val }), { deep: true })

// Edit mode: CreateMockTestView fetches the existing mock test
// asynchronously (GET /mockexams/<id>/) and only THEN fills in
// modelValue — but `form` above was already built from an empty
// modelValue at mount time, since the fetch hadn't resolved yet. This
// watcher re-hydrates the form the moment real data arrives, exactly
// once, so it never overwrites the admin's own edits afterward.
let hydratedFromParent = !!(props.modelValue && props.modelValue.name)
watch(
  () => props.modelValue,
  (val) => {
    if (hydratedFromParent || !val) return
    if (val.name || val.description || val.year || val.totalMarks || val.duration) {
      Object.assign(form, val)
      hydratedFromParent = true
    }
  },
  { deep: true }
)

const years = Array.from({ length: 6 }, (_, i) => 2026 - i)
</script>

<style scoped>
.card { background: #fff; border: 1px solid #ecedf3; border-radius: 12px; padding: 22px 24px 26px; }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
.card-icon { font-size: 15px; }
.card-head h3 { font-size: 14.5px; margin: 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.field label { font-size: 12.5px; font-weight: 600; color: #4b4f66; }
.req { color: #ef4444; }
input, select, textarea {
  border: 1px solid #dfe1ea; border-radius: 8px; padding: 9px 12px; font-size: 13px;
  color: #1f2333; outline: none; font-family: inherit; background: #fff;
}
input:focus, select:focus, textarea:focus { border-color: #a78bfa; box-shadow: 0 0 0 3px #ede9fe; }
textarea { resize: vertical; }
.toggle-field { margin-top: 4px; }
.toggle-row { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.toggle { width: 40px; height: 22px; border-radius: 999px; background: #d8dae6; border: none; position: relative; cursor: pointer; padding: 0; transition: background 0.15s; }
.toggle.on { background: #6d28d9; }
.knob { position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform 0.15s; }
.toggle.on .knob { transform: translateX(18px); }
.actions { display: flex; margin-top: 8px; }
.actions-end { justify-content: flex-end; }
.btn-primary { background: #6d28d9; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #5b21b6; }
</style>