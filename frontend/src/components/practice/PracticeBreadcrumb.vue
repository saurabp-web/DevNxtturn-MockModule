<template>
  <div class="pt-breadcrumb">
    <template v-for="(crumb, i) in crumbs" :key="crumb.label">
      <RouterLink
        v-if="crumb.to && i < activeIndex"
        :to="crumb.to"
        class="crumb crumb-link"
      >
        {{ crumb.label }}
      </RouterLink>
      <span v-else class="crumb" :class="{ active: i === activeIndex }">
        {{ crumb.label }}
      </span>
      <span v-if="i < crumbs.length - 1" class="sep">&rsaquo;</span>
    </template>
  </div>
</template>

<script setup lang="ts">
interface Crumb {
  label: string
  to?: { name: string }
}

defineProps<{
  crumbs: Crumb[]
  activeIndex: number
}>()
</script>

<style scoped>
.pt-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: #9ca3af;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.crumb {
  color: #9ca3af;
  user-select: none;
}

.crumb-link {
  color: #7c3aed;
  text-decoration: none;
  font-weight: 600;
  user-select: none;
}

.crumb-link:hover {
  text-decoration: underline;
}

.crumb.active {
  color: #1e2536;
  font-weight: 700;
}

.sep {
  color: #d1d5db;
}
</style>