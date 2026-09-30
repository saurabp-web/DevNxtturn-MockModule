<template>
  <div class="wizard-panel">
    <div class="panel-head-row">
      <div>
        <h2 class="panel-title" style="margin-bottom:2px">Exam Boards</h2>
        <p class="panel-sub" style="margin:0">Manage boards associated with this exam.</p>
      </div>
      <button class="btn btn-primary" @click="addBoard">+ Add Board</button>
    </div>

    <div class="search-box">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input v-model="search" type="text" placeholder="Search boards..." />
    </div>

    <table class="board-table">
      <thead>
        <tr><th>Board Name</th><th>Applicable Region</th><th>Status</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="(b, i) in filteredBoards" :key="i">
          <td>{{ b.name }}</td>
          <td>{{ b.region }}</td>
          <td>
            <span class="status-badge" :class="b.status.toLowerCase()">{{ b.status }}</span>
          </td>
          <td class="row-actions">
            <button class="icon-btn">⋮</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ form: any }>()
const search = ref('')

const filteredBoards = computed(() => {
  if (!search.value.trim()) return props.form.examBoards
  return props.form.examBoards.filter((b: any) =>
    b.name.toLowerCase().includes(search.value.toLowerCase()),
  )
})

function addBoard() {
  props.form.examBoards.push({ name: 'New Board', region: 'All India', status: 'Active' })
}
</script>

<style scoped>
@import './wizard-panel.css';

.panel-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18px;
}
.panel-sub { font-size: 12px; color: #9CA3AF; }

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 16px;
  max-width: 320px;
}
.search-box input { border: none; outline: none; font-size: 13px; flex: 1; }

.board-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.board-table th {
  text-align: left;
  color: #9CA3AF;
  font-weight: 600;
  padding: 8px 10px;
  border-bottom: 1px solid #F3F4F6;
  text-transform: uppercase;
  font-size: 10px;
}
.board-table td { padding: 12px 10px; border-bottom: 1px solid #F3F4F6; color: #374151; }

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  display: inline-block;
}
.status-badge.active { background: #D1FAE5; color: #059669; }
.status-badge.review { background: #FEF3C7; color: #D97706; }
.status-badge.inactive { background: #FEE2E2; color: #DC2626; }

.icon-btn { background: none; border: none; cursor: pointer; color: #9CA3AF; font-size: 16px; }
</style>