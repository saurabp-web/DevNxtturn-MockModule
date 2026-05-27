<template>
  <div class="emoji-picker-shell flex h-full w-full flex-col overflow-hidden rounded-2xl bg-white shadow-xl dark:bg-gray-900">
    <!-- Header -->
    <div class="border-b border-gray-100 px-4 py-4 dark:border-gray-800">
      <div class="flex items-center justify-between gap-3">
        <div class="min-w-0">
          <p class="text-[11px] font-semibold uppercase tracking-wide text-emerald-500 dark:text-emerald-400">
            {{ eyebrow }}
          </p>
          <h3 class="mt-1 text-lg font-semibold tracking-tight text-gray-900 dark:text-white">
            {{ title }}
          </h3>
        </div>

        <button
          class="flex h-8 w-8 items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
          type="button"
          aria-label="Close media picker"
          @click="$emit('close')"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <!-- Tabs -->
      <div class="mt-4 flex gap-1 rounded-xl bg-gray-100 p-1 dark:bg-gray-800">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
          :class="activeTab === tab.id ? 'bg-white text-gray-900 shadow-sm dark:bg-gray-900 dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
          @click="setTab(tab.id)"
        >
          <span>{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <!-- Search -->
      <div class="relative mt-3">
        <svg
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
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
          :placeholder="searchPlaceholder"
          class="h-10 w-full rounded-xl border border-gray-200 bg-white pl-9 pr-9 text-sm text-gray-900 outline-none transition-all placeholder:text-gray-400 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:focus:border-emerald-500"
        />
        <button
          v-if="searchQuery"
          type="button"
          aria-label="Clear search"
          class="absolute right-2 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          @click="searchQuery = ''"
        >
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <div v-if="activeTab !== 'emoji'" class="mt-2 flex items-center justify-end px-1">
        <!-- <span v-if="activeTab !== 'emoji'" class="text-[10px] font-medium text-emerald-500 dark:text-emerald-400">
          {{ displayedMedia.length }} items
        </span> -->
      </div>
    </div>

    <!-- Scrollable Content -->
    <div ref="scrollEl" class="picker-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-3">
      <!-- Emoji Tab -->
      <template v-if="activeTab === 'emoji'">
        <!-- Recent Emojis -->
        <div v-if="recentEmojis.length && !searchQuery.trim()" class="mb-5">
          <div class="mb-2 flex items-center justify-between px-1">
            <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">Recent</h4>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">Frequently used</span>
          </div>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="emoji in recentEmojis.slice(0, 12)"
              :key="`recent-${emoji}`"
              class="flex h-9 w-9 items-center justify-center rounded-lg text-xl transition-all hover:bg-gray-100 active:scale-95 dark:hover:bg-gray-800"
              type="button"
              :aria-label="`Insert ${emoji}`"
              @click="selectEmoji(emoji)"
            >
              {{ emoji }}
            </button>
          </div>
        </div>

        <!-- Smileys & People Section -->
        <div v-if="!searchQuery.trim()" class="mb-5">
          <div class="mb-2 flex items-center justify-between px-1">
            <div class="flex items-center gap-2">
              <span class="text-lg">😀</span>
              <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">Smileys & People</h4>
            </div>
            <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[9px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              {{ categoryEmojis('people').length }}
            </span>
          </div>
          <div class="emoji-grid grid grid-cols-8 gap-1">
            <button
              v-for="emoji in categoryEmojis('people')"
              :key="`smileys-${emoji.alias}`"
              class="flex aspect-square items-center justify-center rounded-lg text-xl transition-all hover:bg-gray-100 active:scale-95 dark:hover:bg-gray-800"
              type="button"
              :aria-label="`Insert ${emoji.native}`"
              @click="selectEmoji(resolveEmoji(emoji))"
            >
              {{ resolveEmoji(emoji) }}
            </button>
          </div>
        </div>

        <!-- Hand Gestures -->
        <div v-if="!searchQuery.trim()" class="mb-5">
          <div class="mb-2 flex items-center justify-between px-1">
            <div class="flex items-center gap-2">
              <span class="text-lg">🖐️</span>
              <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">Hands & Gestures</h4>
            </div>
            <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[9px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              {{ HAND_ACTION_EMOJIS.length }}
            </span>
          </div>
          <div class="emoji-grid grid grid-cols-8 gap-1">
            <button
              v-for="emoji in HAND_ACTION_EMOJIS"
              :key="`hands-${emoji}`"
              class="flex aspect-square items-center justify-center rounded-lg text-xl transition-all hover:bg-gray-100 active:scale-95 dark:hover:bg-gray-800"
              type="button"
              :aria-label="`Insert ${emoji}`"
              @click="selectEmoji(emoji)"
            >
              {{ emoji }}
            </button>
          </div>
        </div>

        <!-- Search Results -->
        <div v-if="searchQuery.trim()" class="mb-5">
          <div class="mb-2 flex items-center justify-between px-1">
            <div class="flex items-center gap-2">
              <span class="text-lg">🔍</span>
              <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">Search results</h4>
            </div>
            <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[9px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
              {{ searchResults.length }}
            </span>
          </div>
          <div class="emoji-grid grid grid-cols-8 gap-1">
            <button
              v-for="emoji in searchResults"
              :key="`search-${emoji.alias}`"
              class="flex aspect-square items-center justify-center rounded-lg text-xl transition-all hover:bg-gray-100 active:scale-95 dark:hover:bg-gray-800"
              type="button"
              :aria-label="`Insert ${emoji.native}`"
              @click="selectEmoji(resolveEmoji(emoji))"
            >
              {{ resolveEmoji(emoji) }}
            </button>
          </div>
          <div v-if="!searchResults.length" class="py-8 text-center">
            <div class="mb-2 text-3xl">🔎</div>
            <p class="text-sm text-gray-500 dark:text-gray-400">No emoji found</p>
            <p class="mt-0.5 text-xs text-gray-400 dark:text-gray-500">Try a different keyword</p>
          </div>
        </div>

        <!-- Other Categories (Virtualized with placeholder) -->
        <div v-else>
          <div
            v-for="category in otherCategories"
            :key="category.id"
            :ref="(el) => setSectionRef(category.id, el)"
            :data-category-id="category.id"
            class="mb-5"
          >
            <div class="mb-2 flex items-center gap-2 px-1">
              <span class="text-lg">{{ category.icon }}</span>
              <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">
                {{ category.label }}
              </h4>
            </div>
            <div v-if="visibleSections.has(category.id)" class="emoji-grid grid grid-cols-8 gap-1">
              <button
                v-for="emoji in categoryEmojis(category.id)"
                :key="`${category.id}-${emoji.alias}`"
                class="group relative flex aspect-square items-center justify-center rounded-lg text-xl transition-all hover:bg-gray-100 active:scale-95 dark:hover:bg-gray-800"
                type="button"
                :aria-label="`Insert ${emoji.native}`"
                @click="selectEmoji(resolveEmoji(emoji))"
              >
                <span>{{ resolveEmoji(emoji) }}</span>
                <span v-if="emoji.hasSkinTones" class="absolute bottom-0.5 right-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400 opacity-0 transition-opacity group-hover:opacity-100"></span>
              </button>
            </div>
            <div v-else class="emoji-grid grid grid-cols-8 gap-1">
              <div v-for="i in 16" :key="`${category.id}-placeholder-${i}`" class="aspect-square rounded-lg bg-gray-100 dark:bg-gray-800"></div>
            </div>
          </div>
        </div>
      </template>

      <!-- GIF / Sticker Tab -->
      <template v-else>
        <!-- Recent Media -->
        <div v-if="recentMediaItems.length && !searchQuery.trim()" class="mb-5">
          <div class="mb-2 flex items-center justify-between px-1">
            <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">
              Recent {{ activeTab === 'gif' ? 'GIFs' : 'stickers' }}
            </h4>
            <span class="text-[10px] text-gray-400 dark:text-gray-500">Quick picks</span>
          </div>
          <div class="flex gap-2 overflow-x-auto pb-1">
            <button
              v-for="item in recentMediaItems.slice(0, 6)"
              :key="`recent-${item.kind}-${item.providerId}`"
              class="relative w-24 flex-shrink-0 overflow-hidden rounded-xl border border-gray-200 bg-white transition-all hover:scale-[1.02] hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
              type="button"
              :aria-label="`Send ${item.title}`"
              @click="selectMedia(item)"
            >
              <div class="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-700">
                <img
                  :src="item.stillUrl || item.previewUrl"
                  :alt="item.title"
                  class="h-full w-full object-cover"
                  loading="lazy"
                />
              </div>
              <div class="truncate px-2 py-1.5 text-center text-[10px] font-medium text-gray-600 dark:text-gray-400">
                {{ item.title.slice(0, 20) }}
              </div>
            </button>
          </div>
        </div>

        <!-- Media Grid -->
        <div class="rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-gray-800 dark:bg-gray-800/30">
          <div class="mb-3 flex items-center justify-between">
            <div>
              <h4 class="text-xs font-semibold text-gray-700 dark:text-gray-300">
                {{ activeTab === 'gif' ? 'GIFs' : 'Stickers' }}
              </h4>
              <p class="mt-0.5 text-[10px] text-gray-400 dark:text-gray-500">
                {{ activeTab === 'gif' ? 'Powered by GIPHY' : 'Powered by GIPHY' }}
              </p>
            </div>
            <span v-if="loading" class="text-[10px] font-medium text-gray-400 dark:text-gray-500">Loading...</span>
            <span v-else-if="hasMore" class="text-[10px] font-medium text-gray-400 dark:text-gray-500">Scroll for more</span>
          </div>

          <div v-if="loadError" class="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600 dark:bg-red-500/10 dark:text-red-400">
            {{ loadError }}
          </div>

          <!-- GIF Grid -->
          <div v-if="activeTab === 'gif'">
            <div v-if="!displayedMedia.length && loading" class="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <div v-for="i in 6" :key="`skeleton-${i}`" class="overflow-hidden rounded-xl bg-gray-200 dark:bg-gray-700">
                <div class="aspect-square animate-pulse"></div>
              </div>
            </div>
            <div v-else class="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <button
                v-for="item in displayedMedia"
                :key="`${item.kind}-${item.providerId}`"
                class="group relative overflow-hidden rounded-xl bg-gray-100 transition-all hover:scale-[1.02] hover:shadow-md dark:bg-gray-800"
                type="button"
                @click="selectMedia(item)"
              >
                <div class="relative aspect-square">
                  <video
                    v-if="item.kind === 'gif' && item.sendUrl?.toLowerCase().endsWith('.mp4')"
                    class="h-full w-full object-cover"
                    :src="item.sendUrl"
                    autoplay
                    loop
                    muted
                    playsinline
                    preload="metadata"
                    @loadeddata="markLoaded(item.providerId)"
                  ></video>
                  <img
                    v-else
                    class="h-full w-full object-cover"
                    :src="item.previewUrl"
                    :alt="item.title"
                    loading="lazy"
                    @load="markLoaded(item.providerId)"
                  />
                  <div v-if="!loadedItems.has(item.providerId)" class="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800">
                    <div class="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-transparent dark:border-gray-600"></div>
                  </div>
                  <div class="absolute left-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-[9px] font-bold uppercase text-white">GIF</div>
                </div>
                <div class="truncate px-2 py-1.5 text-center text-[10px] font-medium text-gray-600 dark:text-gray-400">
                  {{ item.title }}
                </div>
              </button>
            </div>
          </div>

          <!-- Sticker Grid -->
          <div v-else>
            <div v-if="!displayedMedia.length && loading" class="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
              <div v-for="i in 10" :key="`sticker-skeleton-${i}`" class="aspect-square rounded-xl bg-gray-200 dark:bg-gray-700"></div>
            </div>
            <div v-else class="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
              <button
                v-for="item in displayedMedia"
                :key="`${item.kind}-${item.providerId}`"
                class="group flex aspect-square items-center justify-center rounded-xl bg-gray-100 p-2 transition-all hover:scale-[1.02] hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
                type="button"
                @click="selectMedia(item)"
              >
                <img
                  :src="item.previewUrl"
                  :alt="item.title"
                  class="max-h-full max-w-full object-contain"
                  loading="lazy"
                  @load="markLoaded(item.providerId)"
                />
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="!displayedMedia.length && !loading" class="py-8 text-center">
            <div class="mb-2 text-3xl">{{ activeTab === 'gif' ? '🎞' : '🎟' }}</div>
            <p class="text-sm text-gray-500 dark:text-gray-400">No {{ activeTab === 'gif' ? 'GIFs' : 'stickers' }} found</p>
            <p class="mt-0.5 text-xs text-gray-400 dark:text-gray-500">Try a different search term</p>
          </div>

          <!-- Sentinel for infinite scroll -->
          <div ref="sentinel" class="h-4"></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CATEGORY_EMOJIS,
  EMOJI_CATEGORIES,
  HAND_ACTION_EMOJIS,
  getEmojiNative,
  getRecentEmojis,
  normalizeEmojiInput,
  saveRecentEmoji,
  searchEmojiCatalog,
  type EmojiRecord,
  type EmojiToneIndex,
} from './emoji-catalog'
import {
  type ChatMediaItem,
  getRecentMediaItems,
  saveRecentMediaItem,
} from './chatMediaCatalog'
import {
  fetchGiphySearch,
  fetchGiphyTrending,
  getGiphyErrorMessage,
  type GiphyKind,
} from '@/services/giphy'

type PickerTab = 'emoji' | 'gif' | 'sticker'

const props = withDefaults(
  defineProps<{
    open: boolean
    mode?: 'emoji' | 'composer'
  }>(),
  {
    mode: 'emoji',
  },
)

const emit = defineEmits<{
  (event: 'select', emoji: string): void
  (event: 'pick-media', item: ChatMediaItem): void
  (event: 'close'): void
}>()

const scrollEl = ref<HTMLElement | null>(null)
const sentinel = ref<HTMLElement | null>(null)
const searchQuery = ref('')
const debouncedQuery = ref('')
const selectedTone = ref<EmojiToneIndex>(0)
const activeTab = ref<PickerTab>('emoji')
const recentEmojis = ref<string[]>(getRecentEmojis())
const visibleSections = ref(new Set<string>())
const sectionRefs = new Map<string, HTMLElement>()
const mediaItems = ref<ChatMediaItem[]>([])
const recentMediaItems = ref<ChatMediaItem[]>([])
const loadedItems = ref(new Set<string>())
const loading = ref(false)
const hasMore = ref(true)
const offset = ref(0)
const loadError = ref('')

let searchTimer: number | null = null
let scrollObserver: IntersectionObserver | null = null
let sentinelObserver: IntersectionObserver | null = null

const categories = EMOJI_CATEGORIES
const otherCategories = computed(() => categories.filter((category) => category.id !== 'people'))

const tabs = computed(() => {
  if (props.mode !== 'composer') return [{ id: 'emoji' as const, label: 'Emoji', icon: '😀' }]
  return [
    { id: 'emoji' as const, label: 'Emoji', icon: '😀' },
    { id: 'gif' as const, label: 'GIF', icon: '🎞' },
    { id: 'sticker' as const, label: 'Sticker', icon: '🎟' },
  ]
})

const searchResults = computed(() => searchEmojiCatalog(debouncedQuery.value))
const displayedMedia = computed(() => mediaItems.value)

const eyebrow = computed(() => {
  if (activeTab.value === 'gif') return 'GIFs'
  if (activeTab.value === 'sticker') return 'Stickers'
  return props.mode === 'composer' ? 'Compose' : 'React'
})

const title = computed(() => {
  if (activeTab.value === 'gif') return 'Find the perfect GIF'
  if (activeTab.value === 'sticker') return 'Find a sticker'
  return props.mode === 'composer' ? 'Express yourself' : 'React with an emoji'
})

const searchPlaceholder = computed(() => {
  if (activeTab.value === 'gif') return 'Search GIFs...'
  if (activeTab.value === 'sticker') return 'Search stickers...'
  return 'Search emojis...'
})

function setTab(tab: PickerTab) {
  activeTab.value = tab
  if (tab === 'emoji') {
    loadError.value = ''
    mediaItems.value = []
    return
  }
  resetMedia()
}

function resetMedia() {
  mediaItems.value = []
  loadedItems.value = new Set<string>()
  loading.value = false
  hasMore.value = true
  offset.value = 0
  loadError.value = ''
  void loadMedia(true)
}

function categoryEmojis(categoryId: string) {
  return (CATEGORY_EMOJIS[categoryId] || []).slice(0, 64)
}

function resolveEmoji(record: EmojiRecord) {
  return record.hasSkinTones ? getEmojiNative(record.alias, selectedTone.value) : record.native
}

function selectEmoji(rawEmoji: string) {
  const emoji = normalizeEmojiInput(rawEmoji)
  if (!emoji) return
  saveRecentEmoji(emoji)
  recentEmojis.value = getRecentEmojis()
  emit('select', emoji)
  emit('close')
}

function selectMedia(item: ChatMediaItem) {
  if (!item) return
  saveRecentMediaItem(item)
  recentMediaItems.value = getRecentMediaItems(item.kind)
  emit('pick-media', item)
  emit('close')
}

async function loadMedia(reset = false) {
  if (activeTab.value === 'emoji') return
  if (loading.value) return

  loading.value = true
  loadError.value = ''

  if (reset) {
    mediaItems.value = []
    loadedItems.value = new Set<string>()
    offset.value = 0
    hasMore.value = true
  }

  try {
    const kind = activeTab.value as GiphyKind
    const query = debouncedQuery.value.trim()
    const response = query
      ? await fetchGiphySearch(kind, query, offset.value, 24)
      : await fetchGiphyTrending(kind, offset.value, 24)

    const nextItems = response.items || []
    mediaItems.value = reset ? nextItems : [...mediaItems.value, ...nextItems]
    offset.value += nextItems.length
    hasMore.value = offset.value < response.totalCount && nextItems.length > 0
    recentMediaItems.value = getRecentMediaItems(kind)
  } catch (error) {
    loadError.value = getGiphyErrorMessage(error)
    hasMore.value = false
  } finally {
    loading.value = false
  }
}

function markLoaded(providerId: string) {
  if (!providerId) return
  if (loadedItems.value.has(providerId)) return
  loadedItems.value = new Set([...loadedItems.value, providerId])
}

function categorySectionCallback(entries: IntersectionObserverEntry[]) {
  for (const entry of entries) {
    const target = entry.target as HTMLElement
    const categoryId = target.dataset.categoryId
    if (!categoryId) continue
    if (entry.isIntersecting) {
      visibleSections.value = new Set([...visibleSections.value, categoryId])
    }
  }
}

function setSectionRef(categoryId: string, el: HTMLElement | null | unknown) {
  const element = el instanceof HTMLElement ? el : null
  if (element) {
    sectionRefs.set(categoryId, element)
    scrollObserver?.observe(element)
    return
  }

  const existing = sectionRefs.get(categoryId)
  if (existing && scrollObserver) {
    scrollObserver.unobserve(existing)
  }
  sectionRefs.delete(categoryId)
}

function setupSentinelObserver() {
  if (sentinelObserver) sentinelObserver.disconnect()
  if (!sentinel.value) return

  sentinelObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && !loading.value && hasMore.value && activeTab.value !== 'emoji') {
        void loadMedia()
      }
    },
    { root: scrollEl.value, threshold: 0.1, rootMargin: '0px 0px 200px 0px' },
  )
  sentinelObserver.observe(sentinel.value)
}

watch(searchQuery, (value) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    debouncedQuery.value = value
  }, 300)
})

watch(
  () => debouncedQuery.value,
  () => {
    if (activeTab.value === 'emoji') return
    resetMedia()
  },
)

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return
    recentEmojis.value = getRecentEmojis()
    recentMediaItems.value = getRecentMediaItems(activeTab.value === 'emoji' ? 'gif' : (activeTab.value as GiphyKind))
    if (activeTab.value !== 'emoji') {
      resetMedia()
    }
    nextTick(() => {
      setupSentinelObserver()
    })
  },
  { immediate: true },
)

watch(
  () => props.mode,
  (mode) => {
    if (mode !== 'composer') {
      activeTab.value = 'emoji'
    }
  },
  { immediate: true },
)

watch(
  () => activeTab.value,
  (tab) => {
    if (tab === 'emoji') {
      recentEmojis.value = getRecentEmojis()
      loadError.value = ''
      mediaItems.value = []
      hasMore.value = false
      offset.value = 0
      return
    }
    resetMedia()
    nextTick(() => {
      setupSentinelObserver()
    })
  },
)

onMounted(async () => {
  await nextTick()
  if (scrollEl.value) {
    scrollEl.value.addEventListener('scroll', handleScroll, { passive: true })
  }

  scrollObserver = new IntersectionObserver(categorySectionCallback, {
    root: scrollEl.value,
    threshold: 0.1,
  })
  sectionRefs.forEach((el) => scrollObserver?.observe(el))

  setupSentinelObserver()

  if (props.mode === 'composer' && activeTab.value !== 'emoji') {
    resetMedia()
  }
})

function handleScroll() {
  // Handled by sentinel observer now
}

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
  if (scrollEl.value) {
    scrollEl.value.removeEventListener('scroll', handleScroll)
  }
  scrollObserver?.disconnect()
  sentinelObserver?.disconnect()
  sectionRefs.clear()
})
</script>

<style scoped>
.picker-scroll {
  scroll-behavior: smooth;
}

/* Custom scrollbar */
.picker-scroll::-webkit-scrollbar {
  width: 4px;
}

.picker-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.picker-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 999px;
}

.dark .picker-scroll::-webkit-scrollbar-thumb {
  background: #334155;
}

/* Smooth transitions */
.emoji-grid button,
.media-grid button,
.sticker-grid button {
  transition: all 0.15s ease;
}

/* Recent media horizontal scroll */
.flex.gap-2.overflow-x-auto {
  scrollbar-width: thin;
}

.flex.gap-2.overflow-x-auto::-webkit-scrollbar {
  height: 3px;
}

.flex.gap-2.overflow-x-auto::-webkit-scrollbar-track {
  background: transparent;
}

.flex.gap-2.overflow-x-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 999px;
}

.dark .flex.gap-2.overflow-x-auto::-webkit-scrollbar-thumb {
  background: #475569;
}
</style>
