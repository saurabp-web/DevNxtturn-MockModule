<template>
  <div class="exam-layout">
    <header class="exam-layout-header" v-if="$slots.header || title">
      <slot name="header">
        <h1 class="exam-layout-title">{{ title }}</h1>
      </slot>
    </header>

    <div class="exam-layout-body">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
  }>(),
  {
    title: '',
  },
)
</script>

<style scoped>
.exam-layout {
  max-width: 1500px;
  margin: 0 auto;
  padding: 20px;
}

.exam-layout-header {
  margin-bottom: 18px;
}

.exam-layout-title {
  font-size: 22px;
  font-weight: 800;
  color: #1e2536;
  margin: 0;
}

.exam-layout-body {
  width: 100%;
}
</style>