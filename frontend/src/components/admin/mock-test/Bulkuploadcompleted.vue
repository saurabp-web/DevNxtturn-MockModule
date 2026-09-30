<template>
  <div class="completed-page">
    <div class="completed-card">
      <h2>Bulk Upload Completed</h2>
      <p class="completed-sub">You can now continue with other details or review the questions.</p>

      <div class="completed-illustration">
        <div class="illustration-badge">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2">
            <path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="12" cy="12" r="9" stroke-linecap="round" />
          </svg>
        </div>
      </div>

      <p class="completed-title">All done!</p>
      <p class="completed-detail">{{ importedCount }} questions are successfully added to this mock test.</p>

      <div class="completed-actions">
        <button class="btn btn-outline" @click="$emit('review-questions')">Review Questions</button>
        <button class="btn btn-primary" @click="$emit('next-step')">Next Step →</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  importedCount: {
    type: [Number, String],
    default: 0
  }
})

defineEmits(['review-questions', 'next-step'])
</script>

<style scoped>
.completed-page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 480px;
  padding: 24px;
}

.completed-card {
  text-align: center;
  max-width: 420px;
  width: 100%;
}

.completed-card h2 {
  font-size: 20px;
  margin: 0 0 6px;
  color: #14161f;
}

.completed-sub {
  font-size: 13.5px;
  color: #8a8fa3;
  margin: 0 0 32px;
}

.completed-illustration {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.illustration-badge {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: #e6f9ee;
  display: flex;
  align-items: center;
  justify-content: center;
}

.completed-title {
  font-size: 17px;
  font-weight: 700;
  color: #1f2430;
  margin: 0 0 6px;
}

.completed-detail {
  font-size: 13.5px;
  color: #6b7086;
  margin: 0 0 28px;
}

.completed-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn {
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn-outline { background: #fff; border-color: #e4e6ef; color: #4a4f61; }
.btn-outline:hover { background: #f6f7fb; }
.btn-primary { background: #6c4bf4; color: #fff; }
.btn-primary:hover { background: #5c3ce0; }
</style>