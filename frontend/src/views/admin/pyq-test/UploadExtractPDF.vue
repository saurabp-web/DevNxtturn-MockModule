<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PYWizardStepper from './PYWizardStepper.vue'
import api from '@/api' // adjust the import path to wherever api.ts actually lives
import { pyqImport, resetPyqImport } from '@/services/pyqImportStore'

const router = useRouter()

// Wizard state starts clean every time this screen is entered fresh.
resetPyqImport()

const exams = ref([])
const examsLoading = ref(true)
const examsError = ref('')

const uploadedFile = ref(null) // { name, size } — for the "Upload Complete" card
const rawFile = ref(null) // the actual File object we send to the API
const fileInput = ref(null)
const isDragging = ref(false)

const uploading = ref(false)
const uploadError = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get('/exams/')
    exams.value = data.results ?? data
  } catch (e) {
    examsError.value = 'Could not load exams. Please refresh and try again.'
  } finally {
    examsLoading.value = false
  }
})

function triggerUpload() {
  fileInput.value?.click()
}

function setFile(file) {
  if (!file) return
  uploadError.value = ''
  rawFile.value = file
  uploadedFile.value = { name: file.name, size: `${(file.size / 1024 / 1024).toFixed(2)} MB` }
}

function onFileChange(e) {
  setFile(e.target.files?.[0])
}

function onDrop(e) {
  isDragging.value = false
  setFile(e.dataTransfer.files?.[0])
}

async function goNext() {
  if (!uploadedFile.value || !rawFile.value) return
  if (!pyqImport.examId) {
    uploadError.value = 'Please select which exam this paper belongs to.'
    return
  }

  uploading.value = true
  uploadError.value = ''

  const formData = new FormData()
  formData.append('file', rawFile.value)

  try {
    const { data } = await api.post(`/exams/${pyqImport.examId}/pyq-import/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    pyqImport.uploadId = data.upload_id
    pyqImport.fileName = data.fileName
    pyqImport.fileSize = uploadedFile.value.size
    pyqImport.summary = data.summary
    pyqImport.paperDetails = data.paperDetails

    router.push({ name: 'admin-tests-previous-map-paper-details' })
  } catch (e) {
    uploadError.value = e?.response?.data?.error || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}

function goBack() {
  router.push({ name: 'admin-tests-previous' })
}
</script>

<template>
  <div class="p-6">
    <PYWizardStepper :current-step="1" />

    <div class="mx-auto max-w-4xl">
      <h3 class="text-base font-semibold text-gray-900">Upload Question Paper PDF</h3>
      <p class="mt-1 text-xs text-gray-500">Upload the question paper PDF to extract questions automatically.</p>

      <!-- Exam picker: the backend needs to know which exam this paper belongs to
           before it can accept the upload (POST /exams/<exam_id>/pyq-import/upload/). -->
      <div class="mt-5 rounded-xl border border-gray-200 bg-white p-4">
        <label class="mb-1.5 block text-xs font-medium text-gray-600">Exam <span class="text-red-500">*</span></label>
        <select
          v-model="pyqImport.examId"
          :disabled="examsLoading"
          class="w-full max-w-sm rounded-lg border border-gray-200 px-3 py-2.5 text-xs outline-none focus:border-[#6C4CF1] disabled:bg-gray-50"
        >
          <option :value="null" disabled>{{ examsLoading ? 'Loading exams…' : 'Select an exam' }}</option>
          <option v-for="ex in exams" :key="ex.exam_id" :value="ex.exam_id">{{ ex.exam_name }}</option>
        </select>
        <p v-if="examsError" class="mt-1.5 text-[11px] text-red-500">{{ examsError }}</p>
      </div>

      <div
        class="mt-5 rounded-xl border-2 border-dashed bg-[#FAFAFF] p-16 text-center transition-colors"
        :class="isDragging ? 'border-[#6C4CF1] bg-violet-50' : 'border-[#DCD9F2]'"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
      >
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#EFEBFF] text-[#6C4CF1]">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 16l-4-4-4 4" /><path d="M12 12v9" />
            <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
          </svg>
        </div>
        <h4 class="text-sm font-semibold text-gray-800">Drag &amp; drop your PDF here</h4>
        <p class="mt-1 text-xs text-gray-400">or</p>
        <input ref="fileInput" type="file" accept="application/pdf" class="hidden" @change="onFileChange" />
        <button
          class="mt-4 rounded-lg bg-[#6C4CF1] px-5 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-[#5B3EE0]"
          @click="triggerUpload"
        >
          Choose PDF File
        </button>
        <p class="mt-3 text-[11px] text-gray-400">Max file size: 50MB &nbsp;•&nbsp; PDF only</p>
      </div>

      <div v-if="uploadedFile" class="mt-5 rounded-xl border border-gray-200 bg-white p-4">
        <p class="mb-2 text-xs font-medium text-gray-500">Uploaded File</p>
        <div class="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2.5">
          <div class="flex items-center gap-3">
            <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50 text-red-400">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </span>
            <div>
              <p class="text-xs font-medium text-gray-800">{{ uploadedFile.name }}</p>
              <p class="text-[11px] text-gray-400">{{ uploadedFile.size }}</p>
            </div>
          </div>
          <span v-if="!uploading" class="flex items-center gap-1 text-[11px] font-medium text-emerald-500">
            Ready to upload
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="8 12 11 15 16 9"/></svg>
          </span>
          <span v-else class="flex items-center gap-1 text-[11px] font-medium text-[#6C4CF1]">
            <svg class="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M21 12a9 9 0 1 1-9-9" /></svg>
            Extracting…
          </span>
        </div>
      </div>

      <p v-if="uploadError" class="mt-3 text-xs text-red-500">{{ uploadError }}</p>

      <div class="mt-6 flex justify-end gap-3">
        <button class="rounded-lg border border-gray-200 px-4 py-2.5 text-xs font-medium text-gray-600 hover:bg-gray-50" @click="goBack">
          ← Back
        </button>
        <button
          class="rounded-lg px-4 py-2.5 text-xs font-semibold text-white shadow-sm"
          :class="uploadedFile && !uploading ? 'bg-[#6C4CF1] hover:bg-[#5B3EE0]' : 'bg-gray-300 cursor-not-allowed'"
          :disabled="!uploadedFile || uploading"
          @click="goNext"
        >
          {{ uploading ? 'Extracting…' : 'Next: Process & Review →' }}
        </button>
      </div>
    </div>
  </div>
</template>