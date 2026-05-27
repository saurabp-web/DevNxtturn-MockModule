<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { RouterView } from 'vue-router'
import { storeToRefs } from 'pinia'
import TopNavBar from '@/components/layout/TopNavBar.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const authStore = useAuthStore()
const profileStore = useProfileStore()
const { currentUser } = storeToRefs(authStore)
const { currentProfile } = storeToRefs(profileStore)

async function ensureProfileLoaded() {
  const username = currentUser.value?.username
  if (!username) return
  if (!currentProfile.value || currentProfile.value.user?.username !== username) {
    await profileStore.fetchProfile(username)
  }
}

onMounted(async () => {
  await authStore.initializeAuth()
  await ensureProfileLoaded()
})

watch(currentUser, async () => {
  await ensureProfileLoaded()
})
</script>

<template>
  <div class="bg-gray-50 min-h-screen flex flex-col">
    <TopNavBar />
    <main class="container mx-auto flex min-h-0 flex-1 max-w-7xl overflow-hidden px-4 pt-20 pb-0 sm:px-6 lg:px-8 lg:pb-0">
      <div class="min-h-0 min-w-0 flex-1">
        <RouterView />
      </div>
    </main>
    <MobileBottomNav />
  </div>
</template>

<style scoped>
</style>
