<template>
  <div
    class="emoji-picker-shell w-full max-w-[28rem] overflow-hidden rounded-2xl border border-slate-200/50 bg-white/95 shadow-xl backdrop-blur-xl dark:border-slate-700/50 dark:bg-slate-900/95"
  >
    <div class="border-b border-slate-200/50 bg-white/50 px-4 py-3 dark:border-slate-700/50 dark:bg-slate-800/50">
      <div class="flex flex-wrap items-center justify-between gap-3 sm:flex-nowrap">
        <div>
          <p class="text-[10px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Express yourself
          </p>
          <p class="mt-1 text-sm font-semibold text-slate-700 dark:text-slate-300">
            Choose an emoji to react
          </p>
        </div>

        <button
          class="grid h-8 w-8 place-items-center rounded-lg bg-slate-100 text-slate-500 transition-all hover:bg-slate-200 hover:text-slate-700 active:scale-95 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
          type="button"
          aria-label="Close emoji picker"
          @click="$emit('close')"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
            <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <div class="mt-3">
        <div class="relative">
          <svg
            class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path d="M21 21l-4.3-4.3" stroke-linecap="round" />
            <circle cx="11" cy="11" r="7" />
          </svg>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search emoji or keyword"
            class="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-9 text-sm text-slate-700 outline-none transition-all placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:placeholder:text-slate-500 dark:focus:border-blue-500"
          />
          <button
            v-if="searchQuery"
            type="button"
            aria-label="Clear search"
            class="absolute right-2 top-1/2 grid h-6 w-6 -translate-y-1/2 place-items-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700"
            @click="searchQuery = ''"
          >
            <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2.4" viewBox="0 0 24 24">
              <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>

        <div class="mt-2 flex items-center justify-between px-1">
          <span class="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Search the full catalog
          </span>
          <span v-if="searchQuery.trim()" class="text-[10px] font-semibold text-blue-600 dark:text-blue-400">
            {{ searchResults.length }} matches
          </span>
        </div>
      </div>
    </div>

    <div ref="scrollEl" class="emoji-picker-scroll max-h-[60vh] overflow-y-auto overscroll-contain px-3 py-3">
      <!-- Recently Used -->
      <div v-if="recentEmojis.length" class="mb-4">
        <div class="mb-2 flex items-center justify-between px-1">
          <h3 class="text-[10px] font-black uppercase tracking-wider text-slate-400">
            Recent
          </h3>
          <span class="text-[10px] font-medium text-slate-400">Frequently used</span>
        </div>
        <div class="emoji-row flex flex-wrap gap-2">
          <button
            v-for="emoji in recentEmojis"
            :key="`recent-${emoji}`"
            class="emoji-chip emoji-chip--recent flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-2xl transition-all hover:scale-105 hover:bg-slate-200 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700 sm:h-14 sm:w-14"
            type="button"
            :aria-label="`Insert ${emoji}`"
            @click="selectEmoji(emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>

      <!-- Quick Reactions Section -->
      <div class="mb-4 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-3 dark:border-slate-700 dark:from-slate-800/50 dark:to-slate-800/30">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-[10px] font-black uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Hands & gestures
            </h3>
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
              All the common hand reactions, ready to tap.
            </p>
          </div>
          <span class="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[9px] font-black uppercase tracking-wider text-slate-500 dark:border-slate-700 dark:bg-slate-800">
            {{ handActionEmojis.length }} items
          </span>
        </div>
        <div class="emoji-grid emoji-grid--hands grid grid-cols-[repeat(auto-fill,minmax(3rem,1fr))] gap-2 sm:gap-3">
          <button
            v-for="emoji in handActionEmojis"
            :key="`hand-${emoji}`"
            class="emoji-card emoji-card--hand flex aspect-square items-center justify-center rounded-xl bg-gradient-to-br from-slate-50 to-white text-2xl transition-all hover:scale-105 hover:bg-slate-100 active:scale-95 dark:from-slate-800 dark:to-slate-800/50 dark:hover:bg-slate-700"
            type="button"
            :aria-label="`Insert ${emoji}`"
            @click="selectEmoji(emoji)"
          >
            <span>{{ emoji }}</span>
          </button>
        </div>
      </div>

      <!-- Favorites Section -->
      <div class="mb-4 rounded-xl border border-slate-200 bg-white/50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
        <div class="mb-2 flex items-center justify-between px-1">
          <h3 class="text-[10px] font-black uppercase tracking-wider text-slate-400">
            Favorites
          </h3>
          <span class="text-[10px] font-medium text-slate-400">Quick picks</span>
        </div>
        <div class="emoji-row flex flex-wrap gap-2">
          <button
            v-for="emoji in favoriteEmojis"
            :key="`favorite-${emoji}`"
            class="emoji-chip flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-2xl transition-all hover:scale-105 hover:bg-slate-200 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700 sm:h-14 sm:w-14"
            type="button"
            :aria-label="`Insert ${emoji}`"
            @click="selectEmoji(emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>

      <!-- Category Navigation -->
      <div class="sticky top-0 z-10 mb-3 -mx-1 rounded-xl bg-white/80 px-1 backdrop-blur-md dark:bg-slate-900/80">
        <div class="flex gap-1 overflow-x-auto pb-2 scrollbar-hide">
          <button
            v-for="category in categories"
            :key="category.id"
            type="button"
            class="category-pill flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium transition-all"
            :class="activeCategory === category.id ? 'bg-blue-600 text-white shadow-md shadow-blue-200 dark:shadow-none' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'"
            @click="scrollToCategory(category.id)"
          >
            <span class="text-base">{{ category.icon }}</span>
            <span class="text-xs sm:text-sm">{{ category.label }}</span>
          </button>
        </div>
      </div>

      <!-- Search Results -->
      <div v-if="searchQuery.trim()" class="mb-2 rounded-xl border border-slate-200 bg-white/50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <div class="text-[10px] font-black uppercase tracking-wider text-slate-400">
              Search Results
            </div>
            <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Showing emoji that match your query and keywords
            </div>
          </div>
          <div class="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[9px] font-black uppercase tracking-wider text-slate-500 dark:border-slate-700 dark:bg-slate-800">
            {{ searchResults.length }} found
          </div>
        </div>
        <div class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.4rem))] gap-2 sm:gap-3">
          <button
            v-for="emoji in searchResults"
            :key="`search-${emoji.alias}`"
            class="emoji-card emoji-card--search flex aspect-square items-center justify-center rounded-xl bg-slate-50 text-2xl transition-all hover:scale-105 hover:bg-blue-50 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700"
            type="button"
            :aria-label="`Insert ${emoji.native}`"
            @click="selectEmoji(resolveEmoji(emoji))"
          >
            <span>{{ resolveEmoji(emoji) }}</span>
          </button>
        </div>
        <div v-if="!searchResults.length" class="px-2 py-6 text-center">
          <div class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-2xl dark:bg-slate-800">
            🔎
          </div>
          <p class="text-sm font-semibold text-slate-600 dark:text-slate-400">No emoji found</p>
          <p class="mt-1 text-xs text-slate-400">Try a different name, word, or reaction.</p>
        </div>
      </div>

      <!-- Category Emojis -->
      <div v-else>
        <section
          v-for="category in categories"
          :key="category.id"
          :ref="(el) => setSectionRef(category.id, el)"
          :data-category-id="category.id"
          class="mb-4"
        >
          <div class="mb-2 flex items-center gap-2 px-1">
            <span class="text-lg">{{ category.icon }}</span>
            <h3 class="text-[10px] font-black uppercase tracking-wider text-slate-400">
              {{ category.label }}
            </h3>
          </div>
          <div v-if="visibleSections.has(category.id)" class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3">
            <button
              v-for="emoji in categoryEmojis(category.id)"
              :key="`${category.id}-${emoji.alias}`"
              class="emoji-card group relative flex aspect-square items-center justify-center rounded-xl bg-slate-50 text-2xl transition-all hover:scale-105 hover:bg-blue-50 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700"
              type="button"
              :aria-label="`Insert ${emoji.native}`"
              @click="selectEmoji(resolveEmoji(emoji))"
            >
              <span>{{ resolveEmoji(emoji) }}</span>
              <small v-if="emoji.hasSkinTones" class="emoji-tone-dot absolute bottom-1 right-1 h-1.5 w-1.5 rounded-full bg-blue-400 opacity-0 transition-opacity group-hover:opacity-100"></small>
            </button>
          </div>
          <div v-else class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3">
            <div
              v-for="index in 20"
              :key="`${category.id}-placeholder-${index}`"
              class="emoji-placeholder aspect-square rounded-xl bg-slate-100 dark:bg-slate-800"
            ></div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar */
.emoji-picker-scroll::-webkit-scrollbar {
  width: 4px;
}

.emoji-picker-scroll::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
}

.emoji-picker-scroll::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
}

.emoji-picker-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* Dark mode scrollbar */
.dark .emoji-picker-scroll::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.dark .emoji-picker-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.dark .emoji-picker-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Hide scrollbar for category navigation */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Smooth scrolling */
.emoji-picker-scroll {
  scroll-behavior: smooth;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .emoji-chip,
  .emoji-card {
    width: 2.8rem;
    height: 2.8rem;
    font-size: 1.5rem;
  }

  .emoji-grid {
    gap: 0.5rem;
  }

  .category-pill {
    padding: 0.35rem 0.75rem;
    font-size: 0.7rem;
  }

  .category-pill span:first-child {
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .emoji-chip,
  .emoji-card {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.3rem;
  }
}

/* Active state animation */
button:active {
  transform: scale(0.95);
}

/* Hover effects */
.emoji-card:hover,
.emoji-chip:hover {
  transform: scale(1.05);
}

/* Transition for all interactive elements */
button,
.emoji-card,
.emoji-chip,
.category-pill {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>



<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CATEGORY_EMOJIS,
  EMOJI_CATEGORIES,
  HAND_ACTION_EMOJIS,
  FAVORITE_EMOJIS,
  getEmojiNative,
  getRecentEmojis,
  normalizeEmojiInput,
  saveRecentEmoji,
  searchEmojiCatalog,
  type EmojiRecord,
  type EmojiToneIndex,
} from './emoji-catalog'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (event: 'select', emoji: string): void
  (event: 'close'): void
}>()

const scrollEl = ref<HTMLElement | null>(null)
const searchQuery = ref('')
const debouncedQuery = ref('')
const selectedTone = ref<EmojiToneIndex>(0)
const recentEmojis = ref<string[]>(getRecentEmojis())
const visibleSections = ref(new Set<string>())
const activeCategory = ref(EMOJI_CATEGORIES[0]?.id || 'people')
const sectionRefs = new Map<string, HTMLElement>()
let observer: IntersectionObserver | null = null
let searchTimer: number | null = null

const toneOptions = [
  { value: 0, label: 'Default tone', symbol: '✋' },
  { value: 1, label: 'Light skin tone', symbol: '🏻' },
  { value: 2, label: 'Medium-light skin tone', symbol: '🏼' },
  { value: 3, label: 'Medium skin tone', symbol: '🏽' },
  { value: 4, label: 'Medium-dark skin tone', symbol: '🏾' },
  { value: 5, label: 'Dark skin tone', symbol: '🏿' },
] as const

const categories = EMOJI_CATEGORIES
const favoriteEmojis = FAVORITE_EMOJIS
const handActionEmojis = HAND_ACTION_EMOJIS

const searchResults = computed(() => searchEmojiCatalog(debouncedQuery.value))

function refreshRecent() {
  recentEmojis.value = getRecentEmojis()
}

watch(searchQuery, (value) => {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }

  searchTimer = window.setTimeout(() => {
    debouncedQuery.value = value
  }, 140)
})

function categoryEmojis(categoryId: string) {
  return (CATEGORY_EMOJIS[categoryId] || []).slice(0, 84)
}

function resolveEmoji(record: EmojiRecord) {
  return record.hasSkinTones ? getEmojiNative(record.alias, selectedTone.value) : record.native
}

function setSectionRef(categoryId: string, el: HTMLElement | null | unknown) {
  const element = el instanceof HTMLElement ? el : null
  if (element) {
    sectionRefs.set(categoryId, element)
    observer?.observe(element)
    return
  }

  const existing = sectionRefs.get(categoryId)
  if (existing && observer) {
    observer.unobserve(existing)
  }
  sectionRefs.delete(categoryId)
}

function scrollToCategory(categoryId: string) {
  const el = sectionRefs.get(categoryId)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  activeCategory.value = categoryId
}

function selectEmoji(rawEmoji: string) {
  const emoji = normalizeEmojiInput(rawEmoji)
  if (!emoji) return
  saveRecentEmoji(emoji)
  refreshRecent()
  emit('select', emoji)
}

onMounted(async () => {
  await nextTick()
  if (!scrollEl.value) return

  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        const target = entry.target as HTMLElement
        const categoryId = target.dataset.categoryId
        if (!categoryId) continue

        if (entry.isIntersecting) {
          visibleSections.value = new Set([...visibleSections.value, categoryId])
          activeCategory.value = categoryId
        }
      }
    },
    {
      root: scrollEl.value,
      threshold: 0.14,
    },
  )

  sectionRefs.forEach((el) => observer?.observe(el))
  visibleSections.value = new Set(categories.slice(0, 2).map((item) => item.id))
})

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return
    refreshRecent()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (searchTimer) window.clearTimeout(searchTimer)
  observer?.disconnect()
  observer = null
  sectionRefs.clear()
})
</script>
