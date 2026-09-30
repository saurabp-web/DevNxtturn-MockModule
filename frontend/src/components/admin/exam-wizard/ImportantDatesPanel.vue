<template>
  <div class="wizard-panel">
    <h2 class="panel-title">Important Dates</h2>
    <p class="panel-sub">Add key dates for this exam.</p>

    <table class="dates-table">
      <thead><tr><th>Event</th><th>Date</th></tr></thead>
      <tbody>
        <tr>
          <td>Application Start Date</td>
          <td><input v-model="form.importantDates.applicationStart" type="date" /></td>
        </tr>
        <tr>
          <td>Application End Date</td>
          <td><input v-model="form.importantDates.applicationEnd" type="date" /></td>
        </tr>
        <tr>
          <td>Admit Card Release</td>
          <td><input v-model="form.importantDates.admitCardRelease" type="date" /></td>
        </tr>
        <tr>
          <td>Exam Date</td>
          <td><input v-model="form.importantDates.examDate" type="date" /></td>
        </tr>
        <tr>
          <td>Result Date</td>
          <td><input v-model="form.importantDates.resultDate" type="date" /></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{ form: any }>()
</script>

<style scoped>
@import './wizard-panel.css';

.panel-sub { font-size: 12px; color: #9CA3AF; margin: -14px 0 18px; }

.dates-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.dates-table th {
  text-align: left;
  color: #9CA3AF;
  font-weight: 600;
  padding: 8px 0;
  border-bottom: 1px solid #F3F4F6;
  text-transform: uppercase;
  font-size: 10px;
}
.dates-table td { padding: 12px 0; border-bottom: 1px solid #F3F4F6; color: #374151; }
.dates-table td:first-child { width: 50%; }
.dates-table input {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  width: 100%;
  max-width: 220px;
}
.dates-table input:focus { outline: none; border-color: #7C3AED; }
</style>