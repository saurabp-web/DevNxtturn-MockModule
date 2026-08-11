<template>
  <div class="bg-gray-50 min-h-screen">
    <TopNavBar />
    <main class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-safe-mobile lg:pb-0">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import TopNavBar from '@/components/layout/TopNavBar.vue'
</script>

<style scoped>
.pb-safe-mobile {
  padding-bottom: 3rem;
}

@media (max-width: 768px) {
  .pb-safe-mobile {
    padding-bottom: calc(3rem + env(safe-area-inset-bottom, 0));
  }
}
</style>