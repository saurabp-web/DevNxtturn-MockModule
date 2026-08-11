<template>
  <div class="action-cards">
    <div class="action-card action-card--blue">
      <div class="action-card-icon icon-blue">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
          <path d="M9 12h6M9 16h4" />
        </svg>
      </div>
      <div class="action-card-body">
        <h3>Practice Test</h3>
        <p>Sharpen your skills with topic-wise and section-wise tests.</p>
        <button class="action-btn btn-blue" @click="$emit('practice')">Start Practice</button>
      </div>
    </div>

    <div class="action-card action-card--green">
      <div class="action-card-icon icon-green">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M11 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5" />
          <path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
      </div>
      <div class="action-card-body">
        <h3>Custom Test</h3>
        <p>Create your own test by selecting topics, difficulty &amp; more.</p>
        <button class="action-btn btn-green" @click="$emit('custom')">Create Test</button>
      </div>
    </div>

    <div class="action-card action-card--purple">
      <div class="action-card-icon icon-purple">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="13" r="8" />
          <path d="M12 9v4l2.5 2.5M9 2h6M12 2v3" />
        </svg>
      </div>
      <div class="action-card-body">
        <h3>Mock Test</h3>
        <p>Attempt full-length mock tests simulating the real exam.</p>
        <button class="action-btn btn-purple" @click="$emit('mock')">Start Mock</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  (e: 'practice'): void
  (e: 'custom'): void
  (e: 'mock'): void
}>()
</script>

<style scoped>
.action-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
  align-items: stretch;
}

@media (max-width: 900px) {
  .action-cards {
    grid-template-columns: 1fr;
  }
}

.action-card {
  display: flex;
  gap: 14px;
  align-items: stretch;
  border-radius: 14px;
  padding: 18px;
}

.action-card-body {
  flex: 1;
}

.action-card--blue {
  background: #eaf2ff;
}

.action-card--green {
  background: #e9f9ef;
}

.action-card--purple {
  background: #efeaff;
}

.action-card-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  flex-shrink: 0;
  align-self: flex-start;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-card-icon svg {
  width: 22px;
  height: 22px;
}

.icon-blue {
  background: #dbeafe;
  color: #2563eb;
}

.icon-green {
  background: #d1fae5;
  color: #059669;
}

.icon-purple {
  background: #ede9fe;
  color: #7c3aed;
}

.action-card-body h3 {
  font-size: 15px;
  font-weight: 700;
  color: #1e2536;
  margin: 0 0 4px;
}

.action-card-body p {
  font-size: 12.5px;
  color: #6b7280;
  margin: 0 0 12px;
  line-height: 1.45;
}

.action-btn {
  border: none;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  margin-top: auto;
  align-self: flex-start;
}

.btn-blue {
  background: #2563eb;
}

.btn-green {
  background: #059669;
}

.btn-purple {
  background: #7c3aed;
}
</style>