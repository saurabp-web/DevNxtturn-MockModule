<template>
  <header class="topbar">
    <button class="menu-btn" @click="$emit('toggleSidebar')">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>

    <div class="search-box">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" placeholder="Search exams, categories, tests..." v-model="search" />
      <kbd>⌘ K</kbd>
    </div>

    <div class="topbar-right">
      <button class="icon-btn notif-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        <span class="notif-badge">3</span>
      </button>

      <div class="user-chip">
        <div class="user-avatar">SP</div>
        <div class="user-info">
          <span class="user-name">Saurabh Patil</span>
          <span class="user-role">Super Admin</span>
        </div>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
defineEmits(['toggleSidebar'])
const search = ref('')
</script>

<style scoped>
.topbar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.menu-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  color: #6B7280;
  display: flex;
  align-items: center;
}
.menu-btn:hover { background: #F3F4F6; }

.search-box {
  flex: 1;
  max-width: 380px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 0 12px;
  height: 36px;
}
.search-box input {
  border: none;
  background: none;
  outline: none;
  font-size: 13px;
  color: #374151;
  flex: 1;
}
.search-box input::placeholder { color: #9CA3AF; }
kbd {
  font-size: 11px;
  color: #9CA3AF;
  background: #E5E7EB;
  border-radius: 4px;
  padding: 2px 5px;
  font-family: monospace;
}

.topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  color: #6B7280;
  position: relative;
  display: flex;
}
.icon-btn:hover { background: #F3F4F6; }

.notif-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  background: #EF4444;
  color: #fff;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
}
.user-chip:hover { background: #F3F4F6; }

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7C3AED, #3B82F6);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info { display: flex; flex-direction: column; }
.user-name { font-size: 13px; font-weight: 600; color: #111827; }
.user-role { font-size: 11px; color: #9CA3AF; }
</style>