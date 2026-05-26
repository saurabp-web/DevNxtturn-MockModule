<template>
  <div class="emoji-picker-shell w-full max-w-[30rem] overflow-hidden rounded-[1.75rem] border border-slate-200/70 bg-white/96 shadow-[0_24px_80px_rgba(15,23,42,0.18)] backdrop-blur-2xl dark:border-slate-700/60 dark:bg-slate-950/96">
    <div class="border-b border-slate-200/70 bg-white/70 px-4 py-4 dark:border-slate-700/60 dark:bg-slate-900/80">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="text-[10px] font-black uppercase tracking-[0.28em] text-slate-400 dark:text-slate-500">
            {{ eyebrow }}
          </p>
          <h3 class="mt-1 text-lg font-extrabold tracking-tight text-slate-900 dark:text-white">
            {{ title }}
          </h3>
        </div>

        <button
          class="grid h-9 w-9 place-items-center rounded-full border border-slate-200 bg-white text-slate-500 transition-all hover:-translate-y-0.5 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-800 active:scale-95 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          type="button"
          aria-label="Close media picker"
          @click="$emit('close')"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
            <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <div class="mt-4 flex gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="picker-tab flex-1 rounded-2xl px-3 py-2.5 text-xs font-black uppercase tracking-[0.18em] transition-all"
          :class="activeTab === tab.id ? 'bg-blue-600 text-white shadow-lg shadow-blue-200/70 dark:shadow-none' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'"
          @click="setTab(tab.id)"
        >
          {{ tab.label }}
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
            :placeholder="searchPlaceholder"
            class="h-11 w-full rounded-2xl border border-slate-200 bg-white pl-9 pr-10 text-sm text-slate-700 outline-none transition-all placeholder:text-slate-400 focus:border-blue-400 focus:ring-4 focus:ring-blue-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:placeholder:text-slate-500 dark:focus:border-blue-500"
          />
          <button
            v-if="searchQuery"
            type="button"
            aria-label="Clear search"
            class="absolute right-2 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            @click="searchQuery = ''"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2.4" viewBox="0 0 24 24">
              <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
        <div class="mt-2 flex items-center justify-between px-1">
          <span class="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">
            {{ searchHint }}
          </span>
          <span v-if="activeTab !== 'emoji'" class="text-[10px] font-bold uppercase tracking-[0.22em] text-blue-600 dark:text-blue-400">
            {{ displayedMedia.length }} items
          </span>
        </div>
      </div>
    </div>

    <div ref="scrollEl" class="picker-scroll max-h-[70vh] overflow-y-auto overscroll-contain px-3 py-3">
      <template v-if="activeTab === 'emoji'">
        <div class="mb-4 rounded-[1.5rem] border border-slate-200/80 bg-gradient-to-br from-slate-50 to-white p-3 shadow-[0_12px_28px_rgba(15,23,42,0.05)] dark:border-slate-700/70 dark:from-slate-900/80 dark:to-slate-900/60">
          <div class="mb-3 flex items-center justify-between gap-2 px-1">
            <div>
              <h4 class="text-[10px] font-black uppercase tracking-[0.22em] text-blue-600 dark:text-blue-400">
                Hands &amp; Gestures
              </h4>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Quick reactions and hand signs for fast replies.
              </p>
            </div>
            <span class="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.22em] text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
              {{ HAND_ACTION_EMOJIS.length }} items
            </span>
          </div>
          <div class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3">
            <button
              v-for="emoji in HAND_ACTION_EMOJIS"
              :key="`hands-${emoji}`"
              class="emoji-card flex aspect-square items-center justify-center rounded-2xl bg-slate-50 text-2xl transition-all hover:-translate-y-0.5 hover:bg-blue-50 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700"
              type="button"
              :aria-label="`Insert ${emoji}`"
              @click="selectEmoji(emoji)"
            >
              {{ emoji }}
            </button>
          </div>
        </div>

        <div v-if="recentEmojis.length && !searchQuery.trim()" class="mb-4">
          <div class="mb-2 flex items-center justify-between px-1">
            <h4 class="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">Recent</h4>
            <span class="text-[10px] font-medium text-slate-400">Frequently used</span>
          </div>
          <div class="emoji-row flex flex-wrap gap-2">
            <button
              v-for="emoji in recentEmojis"
              :key="`recent-${emoji}`"
              class="emoji-chip flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-2xl transition-all hover:-translate-y-0.5 hover:bg-slate-200 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700"
              type="button"
              :aria-label="`Insert ${emoji}`"
              @click="selectEmoji(emoji)"
            >
              {{ emoji }}
            </button>
          </div>
        </div>

        <div v-if="searchQuery.trim()" class="mb-4 rounded-[1.5rem] border border-slate-200 bg-white/70 p-3 dark:border-slate-700 dark:bg-slate-900/70">
          <div class="mb-3 flex items-center justify-between gap-2">
            <div>
              <div class="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">Search results</div>
              <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">Emoji that match names or keywords</div>
            </div>
            <div class="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.22em] text-slate-500 dark:border-slate-700 dark:bg-slate-800">
              {{ searchResults.length }} found
            </div>
          </div>
          <div class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.4rem))] gap-2 sm:gap-3">
            <button
              v-for="emoji in searchResults"
              :key="`search-${emoji.alias}`"
              class="emoji-card flex aspect-square items-center justify-center rounded-2xl bg-slate-50 text-2xl transition-all hover:-translate-y-0.5 hover:bg-blue-50 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700"
              type="button"
              :aria-label="`Insert ${emoji.native}`"
              @click="selectEmoji(resolveEmoji(emoji))"
            >
              {{ resolveEmoji(emoji) }}
            </button>
          </div>
          <div v-if="!searchResults.length" class="px-2 py-6 text-center">
            <div class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-2xl dark:bg-slate-800">🔎</div>
            <p class="text-sm font-semibold text-slate-600 dark:text-slate-400">No emoji found</p>
          </div>
        </div>

        <div v-else>
          <section v-for="category in categories" :key="category.id" :ref="(el) => setSectionRef(category.id, el)" :data-category-id="category.id" class="mb-4">
            <div class="mb-2 flex items-center gap-2 px-1">
              <span class="text-lg">{{ category.icon }}</span>
              <h4 class="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">
                {{ category.label }}
              </h4>
            </div>
            <div v-if="visibleSections.has(category.id)" class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3">
              <button
                v-for="emoji in categoryEmojis(category.id)"
                :key="`${category.id}-${emoji.alias}`"
                class="emoji-card group relative flex aspect-square items-center justify-center rounded-2xl bg-slate-50 text-2xl transition-all hover:-translate-y-0.5 hover:bg-blue-50 active:scale-95 dark:bg-slate-800 dark:hover:bg-slate-700"
                type="button"
                :aria-label="`Insert ${emoji.native}`"
                @click="selectEmoji(resolveEmoji(emoji))"
              >
                <span>{{ resolveEmoji(emoji) }}</span>
                <small v-if="emoji.hasSkinTones" class="absolute bottom-1 right-1 h-1.5 w-1.5 rounded-full bg-blue-400 opacity-0 transition-opacity group-hover:opacity-100"></small>
              </button>
            </div>
            <div v-else class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3">
              <div v-for="index in 20" :key="`${category.id}-placeholder-${index}`" class="aspect-square rounded-2xl bg-slate-100 dark:bg-slate-800"></div>
            </div>
          </section>
        </div>
      </template>

      <template v-else>
        <div v-if="recentMediaItems.length && !searchQuery.trim()" class="mb-4">
          <div class="mb-2 flex items-center justify-between px-1">
            <h4 class="text-[10px] font-black uppercase tracking-[0.22em] text-slate-400">
              Recent {{ activeTab === 'gif' ? 'GIFs' : 'stickers' }}
            </h4>
            <span class="text-[10px] font-medium text-slate-400">Quick picks</span>
          </div>
          <div class="media-row flex gap-2 overflow-x-auto pb-1">
            <button
              v-for="item in recentMediaItems"
              :key="`recent-${item.kind}-${item.providerId}`"
              class="media-card-shrink min-w-[7.25rem] max-w-[7.25rem] overflow-hidden rounded-[1.4rem] border border-slate-200 bg-white p-2 text-left transition-all hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md dark:border-slate-700 dark:bg-slate-900"
              type="button"
              :aria-label="`Send ${item.title}`"
              @click="selectMedia(item)"
            >
              <div class="media-preview-frame media-preview-frame--recent" :style="mediaAspectStyle(item)">
                <img
                  :src="item.stillUrl || item.previewUrl"
                  :alt="item.title"
                  class="media-preview"
                  loading="lazy"
                  decoding="async"
                />
              </div>
              <div class="mt-2 truncate px-1 text-[11px] font-semibold text-slate-600 dark:text-slate-300">
                {{ item.title }}
              </div>
            </button>
          </div>
        </div>

        <div class="mb-4 rounded-[1.5rem] border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-3 dark:border-slate-700 dark:from-slate-900/80 dark:to-slate-900/60">
          <div class="mb-3 flex items-center justify-between gap-2">
            <div>
              <h4 class="text-[10px] font-black uppercase tracking-[0.22em] text-blue-600 dark:text-blue-400">
                {{ activeTab === 'gif' ? 'GIF search' : 'Sticker search' }}
              </h4>
              <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {{ activeTab === 'gif' ? 'Search trending reaction GIFs from GIPHY.' : 'Search transparent sticker packs from GIPHY.' }}
              </p>
            </div>
            <div class="rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[9px] font-black uppercase tracking-[0.22em] text-slate-500 dark:border-slate-700 dark:bg-slate-800">
              {{ loading ? 'Loading' : hasMore ? 'More' : 'End' }}
            </div>
          </div>

          <div v-if="loadError" class="mb-3 rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-600 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300">
            {{ loadError }}
          </div>

          <div v-if="activeTab === 'gif'">
            <div v-if="!displayedMedia.length && loading" class="media-grid media-grid--gif">
              <div v-for="index in 8" :key="`skeleton-${index}`" class="media-tile media-tile--gif media-tile--skeleton">
                <div class="media-tile__preview animate-pulse"></div>
                <div class="media-tile__meta">
                  <div class="h-3 w-3/4 animate-pulse rounded-full bg-slate-200/90 dark:bg-slate-700/70"></div>
                  <div class="mt-2 h-2.5 w-1/2 animate-pulse rounded-full bg-slate-200/90 dark:bg-slate-700/70"></div>
                </div>
              </div>
            </div>

            <div v-else class="media-grid media-grid--gif">
              <button
                v-for="item in displayedMedia"
                :key="`${item.kind}-${item.providerId}`"
                class="media-tile media-tile--gif group"
                type="button"
                :aria-label="`Send ${item.title}`"
                @click="selectMedia(item)"
              >
                <div class="media-preview-frame media-preview-frame--gif" :style="mediaAspectStyle(item)">
                  <video
                    v-if="item.kind === 'gif' && item.sendUrl.toLowerCase().endsWith('.mp4')"
                    class="media-preview"
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
                    :src="item.previewUrl"
                    :alt="item.title"
                    class="media-preview"
                    loading="lazy"
                    decoding="async"
                    @load="markLoaded(item.providerId)"
                  />

                  <div v-if="!loadedItems.has(item.providerId)" class="absolute inset-0 bg-slate-100/80 backdrop-blur-sm dark:bg-slate-900/70">
                    <div class="absolute inset-0 animate-pulse bg-gradient-to-br from-transparent via-white/50 to-transparent"></div>
                  </div>

                  <div class="media-tile__badge">GIF</div>
                </div>

                <div class="media-tile__meta">
                  <div class="truncate text-[11px] font-semibold text-slate-700 dark:text-slate-200">
                    {{ item.title }}
                  </div>
                  <div class="mt-1 flex items-center justify-between gap-2 text-[10px] uppercase tracking-[0.16em] text-slate-400">
                    <span>{{ item.animated ? 'Animated' : 'Static' }}</span>
                    <span class="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
                      Send
                    </span>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <div v-else>
            <div v-if="!displayedMedia.length && loading" class="sticker-grid">
              <div v-for="index in 12" :key="`sticker-skeleton-${index}`" class="sticker-tile sticker-tile--skeleton">
                <div class="sticker-tile__preview animate-pulse"></div>
              </div>
            </div>

            <div v-else class="sticker-grid">
              <button
                v-for="item in displayedMedia"
                :key="`${item.kind}-${item.providerId}`"
                class="sticker-tile group"
                type="button"
                :aria-label="`Send ${item.title}`"
                @click="selectMedia(item)"
              >
                <div class="sticker-preview-frame" :style="mediaAspectStyle(item)">
                  <img
                    :src="item.previewUrl"
                    :alt="item.title"
                    class="sticker-preview"
                    loading="lazy"
                    decoding="async"
                    @load="markLoaded(item.providerId)"
                  />
                  <div v-if="!loadedItems.has(item.providerId)" class="absolute inset-0 grid place-items-center">
                    <div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300/70 border-t-transparent dark:border-slate-600/70"></div>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <div v-if="!displayedMedia.length && !loading" class="px-2 py-8 text-center">
            <div class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-2xl dark:bg-slate-800">🔎</div>
            <p class="text-sm font-semibold text-slate-600 dark:text-slate-400">No {{ activeTab === 'gif' ? 'GIF' : 'sticker' }} found</p>
            <p class="mt-1 text-xs text-slate-400">Try a different keyword or browse trending items.</p>
          </div>

          <div ref="sentinel" class="h-8"></div>

          <div class="mt-3 flex items-center justify-between px-1 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500">
            <span>Powered by GIPHY</span>
            <span v-if="loading">{{ activeTab === 'gif' ? 'Loading GIFs' : 'Loading stickers' }}</span>
          </div>
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
  FAVORITE_EMOJIS,
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

type PickerMode = 'emoji' | 'composer'
type PickerTab = 'emoji' | 'gif' | 'sticker'

const props = withDefaults(
  defineProps<{
    open: boolean
    mode?: PickerMode
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

const categories = EMOJI_CATEGORIES
const favoriteEmojis = FAVORITE_EMOJIS

type PickerTabOption = {
  id: PickerTab
  label: string
}

const tabs = computed<PickerTabOption[]>(() => {
  if (props.mode !== 'composer') return [{ id: 'emoji', label: '😀 Emoji' }]
  return [
    { id: 'emoji', label: '😀 Emoji' },
    { id: 'gif', label: '🎞 GIF' },
    { id: 'sticker', label: '🎟 Sticker' },
  ] as const
})

const isComposerMode = computed(() => props.mode === 'composer')

const searchResults = computed(() => searchEmojiCatalog(debouncedQuery.value))
const displayedMedia = computed(() => mediaItems.value)

const eyebrow = computed(() => {
  if (activeTab.value === 'gif') return 'Gif mode'
  if (activeTab.value === 'sticker') return 'Sticker mode'
  return isComposerMode.value ? 'Compose' : 'React'
})

const title = computed(() => {
  if (activeTab.value === 'gif') return 'Search and send GIFs'
  if (activeTab.value === 'sticker') return 'Search and send stickers'
  return isComposerMode.value ? 'Pick an emoji, GIF, or sticker' : 'Choose an emoji to react'
})

const searchPlaceholder = computed(() => {
  if (activeTab.value === 'gif') return 'Search GIFs'
  if (activeTab.value === 'sticker') return 'Search stickers'
  return 'Search emoji or keyword'
})

const searchHint = computed(() => {
  if (activeTab.value === 'gif') return 'Search the GIPHY GIF library'
  if (activeTab.value === 'sticker') return 'Search the GIPHY sticker library'
  return 'Search the emoji catalog'
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
  return (CATEGORY_EMOJIS[categoryId] || []).slice(0, 84)
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
  const next = new Set(loadedItems.value)
  next.add(providerId)
  loadedItems.value = next
}

function mediaAspectStyle(item: ChatMediaItem) {
  const ratio = Number(item?.layoutRatio || 1)
  const clamped = Number.isFinite(ratio) && ratio > 0 ? Math.min(1.45, Math.max(0.72, ratio)) : 1
  return {
    aspectRatio: `${clamped} / 1`,
  }
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

function scrollToCategory(categoryId: string) {
  const el = sectionRefs.get(categoryId)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function handleScroll() {
  if (activeTab.value === 'emoji') return
  const el = scrollEl.value
  if (!el || loading.value || !hasMore.value) return

  const remaining = el.scrollHeight - el.scrollTop - el.clientHeight
  if (remaining < 220) {
    void loadMedia()
  }
}

watch(searchQuery, (value) => {
  if (searchTimer) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    debouncedQuery.value = value
  }, 160)
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
  },
)

onMounted(async () => {
  await nextTick()
  if (scrollEl.value) {
    scrollEl.value.addEventListener('scroll', handleScroll, { passive: true })
  }

  scrollObserver = new IntersectionObserver(categorySectionCallback, {
    root: scrollEl.value,
    threshold: 0.14,
  })
  sectionRefs.forEach((el) => scrollObserver?.observe(el))

  if (props.mode === 'composer' && activeTab.value !== 'emoji') {
    resetMedia()
  }
})

onBeforeUnmount(() => {
  if (searchTimer) window.clearTimeout(searchTimer)
  if (scrollEl.value) {
    scrollEl.value.removeEventListener('scroll', handleScroll)
  }
  scrollObserver?.disconnect()
  scrollObserver = null
  sectionRefs.clear()
})
</script>

<style scoped>
.picker-scroll {
  scroll-behavior: smooth;
}

.media-row {
  scrollbar-width: thin;
  scrollbar-color: rgba(100, 116, 139, 0.3) transparent;
}

.media-row::-webkit-scrollbar {
  height: 4px;
}

.media-row::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.28);
  border-radius: 999px;
}

.media-row::-webkit-scrollbar-track {
  background: transparent;
}

.dark .media-row::-webkit-scrollbar-thumb {
  background: rgba(226, 232, 240, 0.16);
}

.media-card-shrink {
  position: relative;
  border: 1px solid rgba(226, 232, 240, 0.86) !important;
  background: rgba(255, 255, 255, 0.95) !important;
  box-shadow:
    0 10px 24px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.dark .media-card-shrink {
  border-color: rgba(51, 65, 85, 0.82) !important;
  background: rgba(15, 23, 42, 0.96) !important;
  box-shadow:
    0 14px 28px rgba(0, 0, 0, 0.26),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.media-card-shrink:hover {
  border-color: rgba(96, 165, 250, 0.45) !important;
  box-shadow: 0 18px 32px rgba(59, 130, 246, 0.12);
}

.media-card-shrink img,
.media-card-shrink video {
  display: block;
  width: 100%;
  height: 7.5rem;
  object-fit: cover;
  border-radius: 1rem;
  background: linear-gradient(135deg, rgba(241, 245, 249, 0.95), rgba(226, 232, 240, 0.92));
}

.media-card-shrink::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 1.35rem;
  background: linear-gradient(180deg, transparent 70%, rgba(15, 23, 42, 0.06));
  opacity: 0;
  transition: opacity 180ms ease;
}

.media-card-shrink:hover::after {
  opacity: 1;
}

.media-card-shrink .truncate {
  color: #334155;
}

.dark .media-card-shrink .truncate {
  color: #e2e8f0;
}

.media-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.88) !important;
  background: rgba(255, 255, 255, 0.96) !important;
  box-shadow:
    0 12px 28px rgba(15, 23, 42, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.dark .media-card {
  border-color: rgba(51, 65, 85, 0.82) !important;
  background: rgba(15, 23, 42, 0.96) !important;
  box-shadow:
    0 16px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.media-card:hover {
  border-color: rgba(96, 165, 250, 0.45) !important;
  box-shadow: 0 20px 36px rgba(59, 130, 246, 0.12);
}

.media-preview-frame {
  position: relative;
  overflow: hidden;
  border-radius: 1rem;
  background: radial-gradient(circle at top, rgba(59, 130, 246, 0.08), rgba(15, 23, 42, 0.03));
}

.media-preview-frame--gif {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.08), rgba(255, 255, 255, 0.8));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.media-preview-frame--recent {
  border-radius: 0.95rem;
}

.media-preview {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.media-card > div:first-child {
  overflow: hidden;
}

.media-card > div:last-child {
  padding-top: 0.8rem;
}

.media-grid--gif {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

@media (min-width: 640px) {
  .media-grid--gif {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.media-tile--gif {
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.88) !important;
  background: rgba(255, 255, 255, 0.96) !important;
  box-shadow:
    0 12px 28px rgba(15, 23, 42, 0.07),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.dark .media-tile--gif {
  border-color: rgba(51, 65, 85, 0.82) !important;
  background: rgba(15, 23, 42, 0.96) !important;
}

.media-tile--gif .media-tile__preview {
  aspect-ratio: 1 / 1;
}

.media-tile__preview {
  min-height: 7rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, rgba(226, 232, 240, 0.95), rgba(241, 245, 249, 0.95));
}

.media-tile__meta {
  padding: 0.75rem 0.8rem 0.82rem;
}

.media-tile__badge {
  position: absolute;
  left: 0.6rem;
  top: 0.6rem;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.92);
  padding: 0.28rem 0.5rem;
  font-size: 0.62rem;
  font-weight: 900;
  letter-spacing: 0.18em;
  color: #fff;
  text-transform: uppercase;
}

.media-tile--skeleton .media-tile__preview {
  min-height: 9rem;
}

.sticker-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.6rem;
}

@media (min-width: 480px) {
  .sticker-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.7rem;
  }
}

@media (min-width: 640px) {
  .sticker-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 0.75rem;
  }
}

.sticker-tile {
  display: grid;
  place-items: center;
  min-height: 5.5rem;
  padding: 0.12rem;
  border-radius: 1.2rem;
  border: 1px solid transparent;
  background: transparent;
  box-shadow: none;
  transition:
    transform 180ms cubic-bezier(0.4, 0, 0.2, 1),
    border-color 180ms cubic-bezier(0.4, 0, 0.2, 1),
    background-color 180ms cubic-bezier(0.4, 0, 0.2, 1);
}

.sticker-tile:hover {
  transform: translateY(-2px) scale(1.01);
  border-color: rgba(96, 165, 250, 0.18);
  background: rgba(148, 163, 184, 0.04);
}

.dark .sticker-tile:hover {
  background: rgba(255, 255, 255, 0.03);
}

.sticker-preview-frame {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  padding: 0;
  background: transparent;
}

.sticker-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 10px 18px rgba(15, 23, 42, 0.12));
}

.sticker-tile--skeleton {
  min-height: 5.5rem;
}

.sticker-tile--skeleton .sticker-tile__preview {
  width: 58%;
  height: 58%;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(226, 232, 240, 0.72), rgba(241, 245, 249, 0.72));
}

.dark .sticker-tile--skeleton .sticker-tile__preview {
  background: linear-gradient(135deg, rgba(51, 65, 85, 0.72), rgba(30, 41, 59, 0.72));
}

.media-card .truncate {
  color: #334155;
}

.dark .media-card .truncate {
  color: #e2e8f0;
}

.media-card .mt-2.h-3,
.media-card .mt-2.h-3.w-2\/3,
.media-card .h-40 {
  border-radius: 0.85rem;
}

.media-card::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 1.4rem;
  background: linear-gradient(180deg, transparent 72%, rgba(15, 23, 42, 0.05));
  opacity: 0;
  transition: opacity 180ms ease;
}

.media-card:hover::before {
  opacity: 1;
}

.media-empty {
  margin-top: 1rem;
  display: grid;
  place-items: center;
  padding: 2.25rem 1rem 2.4rem;
  border-radius: 1.5rem;
  border: 1px dashed rgba(148, 163, 184, 0.42);
  background: rgba(248, 250, 252, 0.7);
  text-align: center;
}

.dark .media-empty {
  border-color: rgba(71, 85, 105, 0.7);
  background: rgba(15, 23, 42, 0.72);
}

.media-empty__icon {
  margin-bottom: 0.8rem;
  display: grid;
  height: 3rem;
  width: 3rem;
  place-items: center;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  font-size: 1.25rem;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
}

.dark .media-empty__icon {
  background: rgba(15, 23, 42, 0.95);
}

.dark .media-empty__icon,
.dark .media-card-shrink,
.dark .media-card {
  color: #e2e8f0;
}

.picker-tab,
.emoji-card,
.emoji-chip,
.media-card,
.media-card-shrink {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.emoji-card:hover,
.emoji-chip:hover,
.media-card:hover,
.media-card-shrink:hover {
  transform: translateY(-2px);
}

button:active {
  transform: scale(0.96);
}

.dark .picker-scroll::-webkit-scrollbar,
.picker-scroll::-webkit-scrollbar {
  width: 4px;
}

.picker-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.picker-scroll::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.28);
  border-radius: 999px;
}

.dark .picker-scroll::-webkit-scrollbar-thumb {
  background: rgba(226, 232, 240, 0.18);
}
</style>
