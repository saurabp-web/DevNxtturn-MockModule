<template>
  <div class="step-content">
    <h2 class="step-title">3. Options &amp; Correct Answer</h2>
    <p class="step-subtitle">Add options for the question and select the correct answer.</p>

    <div class="options-layout">
      <!-- Options List -->
      <div class="options-column">
        <div
          v-for="(option, index) in options"
          :key="option.id"
          class="option-row"
        >
          <span class="option-label">{{ String.fromCharCode(65 + index) }}</span>
          <input
            v-model="option.text"
            type="text"
            class="option-input"
            :placeholder="`Enter option ${index + 1}`"
          />
          <button
            v-if="options.length > 2"
            class="remove-option-btn"
            @click="removeOption(index)"
            type="button"
            title="Remove option"
          >
            ✕
          </button>
          <div class="option-radio-spacer" v-else />
        </div>

        <button
          v-if="options.length < 6"
          class="add-option-btn"
          @click="addOption"
          type="button"
        >
          <span class="plus">+</span> Add Option
        </button>
        <p class="hint-text">You can add up to 6 options.</p>
      </div>

      <!-- Correct Answer Selector -->
      <div class="answer-column">
        <div class="form-group">
          <label class="form-label">Correct Answer <span class="required">*</span></label>
          <select v-model="correctAnswer" class="form-select">
            <option value="" disabled>Select correct option</option>
            <option
              v-for="(option, index) in filledOptions"
              :key="option.id"
              :value="option.id"
            >
              Option {{ String.fromCharCode(65 + index) }}{{ option.text ? ': ' + option.text : '' }}
            </option>
          </select>
          <p class="hint-text">Select the correct answer from the options.</p>
        </div>
      </div>
    </div>

    <div class="step-footer">
      <button class="btn btn--secondary" @click="$emit('prev')" type="button">
        ← Previous Step
      </button>
      <button
        class="btn btn--primary"
        @click="handleNext"
        :disabled="!isValid"
        type="button"
      >
        Next Step →
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['next', 'prev', 'update:modelValue'])

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

let idCounter = 0
const makeOption = (text = '') => ({ id: ++idCounter, text })

const options = ref(
  props.modelValue?.options?.length
    ? props.modelValue.options.map(o => ({ ...o, id: ++idCounter }))
    : [makeOption(), makeOption(), makeOption(), makeOption()]
)

const correctAnswer = ref(props.modelValue?.correctAnswer || '')

const filledOptions = computed(() => options.value.filter(o => o.text.trim()))

const isValid = computed(() => correctAnswer.value && filledOptions.value.length >= 2)

function addOption() {
  if (options.value.length < 6) {
    options.value.push(makeOption())
  }
}

function removeOption(index) {
  const removed = options.value.splice(index, 1)[0]
  if (correctAnswer.value === removed.id) {
    correctAnswer.value = ''
  }
}

function handleNext() {
  emit('update:modelValue', {
    options: options.value.map(o => ({ id: o.id, text: o.text })),
    correctAnswer: correctAnswer.value
  })
  emit('next')
}
</script>

<style scoped>
.step-content {
  padding: 0;
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  color: #4f46e5;
  margin: 0 0 4px;
}

.step-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 28px;
}

.options-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 48px;
  align-items: start;
}

.options-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.option-label {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  flex-shrink: 0;
}

.option-input {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  transition: border-color 0.15s;
}

.option-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
}

.remove-option-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
  transition: background 0.15s;
}

.remove-option-btn:hover {
  background: #fecaca;
}

.option-radio-spacer {
  width: 28px;
  flex-shrink: 0;
}

.add-option-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: 1.5px dashed #c4b5fd;
  border-radius: 6px;
  color: #4f46e5;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  width: fit-content;
}

.add-option-btn:hover {
  background: #f5f3ff;
  border-color: #4f46e5;
}

.plus {
  font-size: 18px;
  line-height: 1;
}

.hint-text {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

/* Answer column */
.answer-column {
  padding-top: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.required { color: #ef4444; }

.form-select {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E") no-repeat right 12px center;
  appearance: none;
  cursor: pointer;
  transition: border-color 0.15s;
}

.form-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79,70,229,0.1);
}

/* Footer */
.step-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.btn--primary {
  background: #4f46e5;
  color: #fff;
}
.btn--primary:hover:not(:disabled) { background: #4338ca; }
.btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn--secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}
.btn--secondary:hover { background: #e5e7eb; }
</style>