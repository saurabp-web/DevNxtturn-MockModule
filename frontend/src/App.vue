<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { notificationService } from '@/services/notificationService'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

// Watcher for WebSocket connection
watch(
  () => authStore.isAuthenticated,
  (isNowAuthenticated) => {
    if (isNowAuthenticated) {
      notificationService.connect()
    } else {
      notificationService.disconnect()
    }
  },
  { immediate: true },
)

const handleStorageChange = (event: StorageEvent) => {
  if (event.key === 'authToken' && !event.newValue) {
    authStore.resetAuthState()
    router.push({ name: 'login' })
  }
}

onMounted(() => {
  window.addEventListener('storage', handleStorageChange)
})

onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange)
})
</script>

<template>
  <RouterView />
</template>
