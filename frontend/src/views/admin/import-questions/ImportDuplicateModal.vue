<template>
  <div class="modal-overlay">
    <div class="modal-card">
      <button class="close-btn" @click="$emit('close')">
        <CloseIcon />
      </button>

      <div class="icon-wrap">
        <AlertIcon />
      </div>

      <h3 class="modal-title">Duplicate Questions Found!</h3>
      <p class="modal-body">
        {{ count }} question{{ count === 1 ? '' : 's' }} in your file
        {{ count === 1 ? 'has' : 'have' }} already appeared in
        <strong>{{ examName }}</strong>.<br />
        Do you want to map {{ count === 1 ? 'it' : 'these questions' }} to this exam anyway?
      </p>

      <div class="modal-actions">
        <button class="skip-btn" @click="$emit('choose', false)">No, Skip Them</button>
        <button class="map-btn" @click="$emit('choose', true)">Yes, Map Them</button>
      </div>

      <p class="modal-footnote">
        If you choose 'No', these questions will be skipped and will not be imported.
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  count:    { type: Number, default: 0 },
  examName: { type: String, default: '' },
})
defineEmits(['choose', 'close'])

const AlertIcon = { template: `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>` }
const CloseIcon = { template: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>` }
</script>

<style scoped>
* { box-sizing: border-box; }

.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(20, 18, 31, 0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.modal-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 32px 36px 24px;
  max-width: 420px;
  width: 90%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(20, 18, 31, 0.18);
}

.close-btn {
  position: absolute; top: 14px; right: 14px;
  width: 28px; height: 28px;
  border-radius: 50%; border: none;
  background: #F3F2F9; color: #8A879C;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
.close-btn:hover { background: #ECEAF5; }

.icon-wrap {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: #FFF3DE;
  color: #E08A00;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
}

.modal-title { font-size: 18px; font-weight: 700; color: #14121F; margin: 0 0 10px; }
.modal-body {
  font-size: 13.5px; color: #524F6B; line-height: 1.6; margin: 0 0 22px;
}
.modal-body strong { color: #14121F; }

.modal-actions {
  display: flex; gap: 12px; margin-bottom: 16px;
}
.skip-btn, .map-btn {
  flex: 1;
  padding: 11px 0;
  border-radius: 9px;
  font-size: 13.5px; font-weight: 600;
  cursor: pointer;
}
.skip-btn {
  background: #fff; border: 1px solid #ECEBF3; color: #524F6B;
}
.skip-btn:hover { background: #F6F5FB; }
.map-btn {
  background: #6C4CF1; border: none; color: #fff;
}
.map-btn:hover { background: #5B3EE0; }

.modal-footnote {
  font-size: 12px; color: #8A879C; margin: 0;
}
</style>