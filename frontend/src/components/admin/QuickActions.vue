<template>
  <div class="qa-card">
    <h3 class="qa-title">Quick Actions</h3>
    <div class="qa-grid">
      <button v-for="action in actions" :key="action.label" class="qa-btn">
        <span class="qa-icon" :style="{ color: action.color }" v-html="action.icon"></span>
        <span class="qa-label">{{ action.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const actions = [
  {
    label: 'Create Exam',
    color: '#7C3AED',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>`,
  },
  {
    label: 'Create Test',
    color: '#2563EB',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>`,
  },
  {
    label: 'Add Subject',
    color: '#059669',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="12" y1="7" x2="12" y2="13"/><line x1="9" y1="10" x2="15" y2="10"/></svg>`,
  },
  {
    label: 'Import Exams',
    color: '#D97706',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
  },
  {
    label: 'Manage Categories',
    color: '#7C3AED',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
  },
  {
    label: 'Manage Boards',
    color: '#2563EB',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="22" x2="21" y2="22"/><line x1="6" y1="18" x2="6" y2="11"/><line x1="10" y1="18" x2="10" y2="5"/><line x1="14" y1="18" x2="14" y2="8"/><line x1="18" y1="18" x2="18" y2="2"/></svg>`,
  },
  {
    label: 'Manage Pattern',
    color: '#DC2626',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
  },
  {
    label: 'View Reports',
    color: '#059669',
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  },
]
</script>

<style scoped>
.qa-card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px 24px;
}
.qa-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 16px; }

.qa-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.qa-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 8px;
  background: #FAFAFA;
  border: 1px solid #F3F4F6;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.qa-btn:hover {
  background: #F5F3FF;
  border-color: #DDD6FE;
  box-shadow: 0 2px 8px rgba(124,58,237,0.08);
}

.qa-icon { display: flex; }
.qa-label { font-size: 11px; font-weight: 600; color: #374151; text-align: center; line-height: 1.3; }
</style>