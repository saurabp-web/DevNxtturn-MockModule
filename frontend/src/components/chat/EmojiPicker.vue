<template>
  <div
    class="emoji-picker-shell w-full max-w-[28rem] overflow-hidden rounded-[2rem] border border-emerald-200/15 bg-[#0f1d1c]/95 text-white shadow-[0_28px_90px_rgba(0,0,0,0.38)] backdrop-blur-2xl"
  >
    <div class="border-b border-white/8 bg-white/[0.03] px-4 py-3">
      <div class="flex items-center justify-between gap-3 flex-wrap sm:flex-nowrap">
        <div>
          <p class="text-[10px] font-black uppercase tracking-[0.34em] text-emerald-200/70">
            WhatsApp-style Picker
          </p>
          <p class="mt-1 text-sm font-semibold text-white/80">
            Search, recent, categories, tones, and quick send.
          </p>
        </div>

        <button
          class="grid h-10 w-10 place-items-center rounded-full bg-white/8 text-white/70 transition hover:bg-white/14 hover:text-white active:scale-95 shrink-0"
          type="button"
          aria-label="Close emoji picker"
          @click="$emit('close')"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
            <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <div class="mt-3 rounded-[1.4rem] border border-white/8 bg-black/15 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
        <div class="flex items-center gap-2 flex-col sm:flex-row">
          <div class="relative flex-1 w-full">
            <svg
              class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-100/35"
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
              class="h-11 w-full rounded-2xl border border-white/8 bg-[#0b1514] pl-10 pr-10 text-sm text-white outline-none transition placeholder:text-emerald-50/25 focus:border-emerald-300/40 focus:bg-[#0f1d1c]"
            />
            <button
              v-if="searchQuery"
              type="button"
              aria-label="Clear search"
              class="absolute right-2 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-full bg-white/6 text-white/45 transition hover:bg-white/12 hover:text-white"
              @click="searchQuery = ''"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.4" viewBox="0 0 24 24">
                <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>

          <div class="flex items-center gap-2 mt-2 sm:mt-0 shrink-0">
            <button
              v-for="tone in toneOptions"
              :key="tone.value"
              class="tone-chip"
              type="button"
              :aria-label="tone.label"
              :class="selectedTone === tone.value ? 'tone-chip--active' : ''"
              @click="selectedTone = tone.value"
            >
              <span>{{ tone.symbol }}</span>
            </button>
          </div>
        </div>

        <div class="mt-2 flex items-center justify-between px-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-emerald-100/35 flex-wrap gap-1">
          <span>Search the full catalog</span>
          <span v-if="searchQuery.trim()">{{ searchResults.length }} matches</span>
        </div>
      </div>
    </div>

    <div ref="scrollEl" class="emoji-picker-scroll max-h-[60vh] overflow-y-auto overscroll-contain px-3 py-3">
      <div v-if="recentEmojis.length" class="mb-4">
        <div class="mb-2 flex items-center justify-between px-1">
          <h3 class="text-[10px] font-black uppercase tracking-[0.28em] text-white/40">
            Recent
          </h3>
          <span class="text-[10px] font-semibold text-white/30">Frequently used</span>
        </div>
        <div class="emoji-row flex flex-wrap gap-2 sm:gap-3">
          <button
            v-for="emoji in recentEmojis"
            :key="`recent-${emoji}`"
            class="emoji-chip emoji-chip--recent"
            type="button"
            :aria-label="`Insert ${emoji}`"
            @click="selectEmoji(emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>

      <div class="mb-4 rounded-[1.5rem] border border-emerald-200/10 bg-gradient-to-br from-white/[0.05] to-white/[0.02] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
        <div class="mb-3 flex items-center justify-between gap-3 px-1">
          <div>
            <h3 class="text-[10px] font-black uppercase tracking-[0.28em] text-emerald-100/55">
              Hands & gestures
            </h3>
            <p class="mt-1 text-xs text-white/40">All the common hand reactions, ready to tap.</p>
          </div>
          <span class="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em] text-emerald-100/50">
            {{ handActionEmojis.length }} items
          </span>
        </div>
        <div class="emoji-grid emoji-grid--hands">
          <button
            v-for="emoji in handActionEmojis"
            :key="`hand-${emoji}`"
            class="emoji-card emoji-card--hand"
            type="button"
            :aria-label="`Insert ${emoji}`"
            @click="selectEmoji(emoji)"
          >
            <span>{{ emoji }}</span>
          </button>
        </div>
      </div>

      <div class="mb-4 rounded-[1.5rem] border border-white/8 bg-white/[0.03] p-3">
        <div class="mb-2 flex items-center justify-between px-1">
          <h3 class="text-[10px] font-black uppercase tracking-[0.28em] text-white/40">
            Favorites
          </h3>
          <span class="text-[10px] font-semibold text-white/30">Quick picks</span>
        </div>
        <div class="emoji-row flex flex-wrap gap-2 sm:gap-3">
          <button
            v-for="emoji in favoriteEmojis"
            :key="`favorite-${emoji}`"
            class="emoji-chip"
            type="button"
            :aria-label="`Insert ${emoji}`"
            @click="selectEmoji(emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>

      <div class="sticky top-0 z-10 mb-3 rounded-2xl border border-white/8 bg-[#102221]/90 px-2 py-2 shadow-[0_12px_30px_rgba(0,0,0,0.2)] backdrop-blur-xl">
        <div class="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
          <button
            v-for="category in categories"
            :key="category.id"
            type="button"
            class="category-pill whitespace-nowrap flex items-center gap-1 sm:gap-2"
            :class="activeCategory === category.id ? 'category-pill--active' : ''"
            @click="scrollToCategory(category.id)"
          >
            <span>{{ category.icon }}</span>
            <span class="text-xs sm:text-sm">{{ category.label }}</span>
          </button>
        </div>
      </div>

      <div v-if="searchQuery.trim()" class="mb-2 rounded-[1.4rem] border border-white/8 bg-white/[0.03] p-3">
        <div class="mb-3 flex items-center justify-between gap-3 px-1 flex-wrap">
          <div>
            <div class="text-[10px] font-black uppercase tracking-[0.28em] text-emerald-100/40">
              Search Results
            </div>
            <div class="mt-1 text-xs text-white/45">
              Showing emoji that match your query and keywords
            </div>
          </div>
          <div class="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em] text-emerald-100/55">
            {{ searchResults.length }} found
          </div>
        </div>
        <div class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.4rem))] gap-2 sm:gap-3 justify-between">
          <button
            v-for="emoji in searchResults"
            :key="`search-${emoji.alias}`"
            class="emoji-card emoji-card--search aspect-square flex items-center justify-center"
            type="button"
            :aria-label="`Insert ${emoji.native}`"
            @click="selectEmoji(resolveEmoji(emoji))"
          >
            <span>{{ resolveEmoji(emoji) }}</span>
          </button>
        </div>
        <div v-if="!searchResults.length" class="px-2 py-6 text-center">
          <div class="mx-auto grid h-12 w-12 place-items-center rounded-full bg-white/5 text-xl">🔎</div>
          <p class="mt-3 text-sm font-semibold text-white/70">No emoji found</p>
          <p class="mt-1 text-xs text-white/40">Try a different name, word, or reaction.</p>
        </div>
      </div>

      <div v-else>
        <section
          v-for="category in categories"
          :key="category.id"
          :ref="(el) => setSectionRef(category.id, el)"
          :data-category-id="category.id"
          class="mb-4"
        >
          <div class="mb-2 flex items-center gap-2 px-1">
            <span class="text-base">{{ category.icon }}</span>
            <h3 class="text-[10px] font-black uppercase tracking-[0.28em] text-white/40">
              {{ category.label }}
            </h3>
          </div>
          <div v-if="visibleSections.has(category.id)" class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3 justify-start">
            <button
              v-for="emoji in categoryEmojis(category.id)"
              :key="`${category.id}-${emoji.alias}`"
              class="emoji-card relative aspect-square flex items-center justify-center"
              type="button"
              :aria-label="`Insert ${emoji.native}`"
              @click="selectEmoji(resolveEmoji(emoji))"
            >
              <span>{{ resolveEmoji(emoji) }}</span>
              <small v-if="emoji.hasSkinTones" class="emoji-tone-dot absolute bottom-1 right-1 w-1.5 h-1.5 rounded-full bg-emerald-400"></small>
            </button>
          </div>
          <div v-else class="emoji-grid grid grid-cols-[repeat(auto-fill,minmax(3rem,3.6rem))] gap-2 sm:gap-3">
            <div
              v-for="index in 20"
              :key="`${category.id}-placeholder-${index}`"
              class="emoji-placeholder aspect-square rounded-xl bg-white/5"
            ></div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.emoji-picker-scroll::-webkit-scrollbar {
  width: 4px;
}
.emoji-picker-scroll::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.05);
  border-radius: 10px;
}
.emoji-picker-scroll::-webkit-scrollbar-thumb {
  background: rgba(210, 255, 210, 0.2);
  border-radius: 10px;
}
.scrollbar-hide {
  scrollbar-width: thin;
}
.scrollbar-hide::-webkit-scrollbar {
  height: 3px;
}

.tone-chip {
  background: rgba(255,255,240,0.03);
  border: 1px solid rgba(210,240,210,0.2);
  border-radius: 40px;
  width: 2.3rem;
  height: 2.3rem;
  font-size: 1.2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.tone-chip:hover {
  background: rgba(110, 230, 180, 0.2);
  transform: scale(1.03);
}
.tone-chip--active {
  background: #2c7a5e;
  border-color: #a3e4c6;
  box-shadow: 0 0 6px #66d9a0;
}

.emoji-chip {
  background: rgba(210,240,210,0.08);
  border: 1px solid rgba(210,240,210,0.18);
  border-radius: 18px;
  width: 3.5rem;
  height: 3.5rem;
  font-size: 1.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.12s;
  backdrop-filter: blur(2px);
}
.emoji-chip--hand {
  background: rgba(210,180,140,0.08);
}
.emoji-chip--recent {
  background: rgba(210,240,210,0.14);
}
.emoji-chip:hover,
.emoji-card:hover {
  background: rgba(140, 230, 180, 0.18);
  transform: scale(1.02);
  border-color: rgba(100, 230, 160, 0.5);
}
button:active {
  transform: scale(0.96);
}

.category-pill {
  background: rgba(255,255,240,0.04);
  border: 1px solid rgba(210,240,210,0.2);
  border-radius: 40px;
  padding: 0.45rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.15s;
}
.category-pill:hover {
  background: rgba(90, 210, 160, 0.2);
}
.category-pill--active {
  background: #1f6e58;
  border-color: #7df0bc;
  color: white;
}

.emoji-card {
  background: rgba(255,255,250,0.02);
  border-radius: 20px;
  font-size: 1.9rem;
  transition: all 0.1s ease;
  border: 1px solid rgba(210,240,200,0.08);
}

.emoji-grid--hands {
  grid-template-columns: repeat(auto-fill, minmax(3.2rem, 1fr));
  gap: 0.55rem;
}

.emoji-card--hand {
  background: linear-gradient(180deg, rgba(210, 240, 210, 0.1), rgba(255, 255, 255, 0.03));
  border-color: rgba(170, 230, 190, 0.16);
  min-height: 3.25rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.emoji-card--hand:hover {
  background: linear-gradient(180deg, rgba(140, 230, 180, 0.22), rgba(255, 255, 255, 0.06));
  border-color: rgba(140, 230, 180, 0.45);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}

.emoji-card--search {
  background: rgba(255, 255, 250, 0.04);
}

@media (max-width: 480px) {
  .emoji-card,
  .emoji-chip {
    width: 3rem;
    height: 3rem;
    font-size: 1.6rem;
  }
  .emoji-grid {
    gap: 0.5rem;
  }
  .tone-chip {
    width: 2.1rem;
    height: 2.1rem;
    font-size: 1rem;
  }
  .category-pill {
    padding: 0.4rem 0.7rem;
    font-size: 0.7rem;
  }
}

@media (max-width: 380px) {
  .emoji-card,
  .emoji-chip {
    width: 2.6rem;
    height: 2.6rem;
    font-size: 1.4rem;
  }
  .category-pill span:first-child {
    font-size: 0.9rem;
  }
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
<!--
<style scoped>
.emoji-picker-shell {
  -webkit-tap-highlight-color: transparent;
}

.emoji-picker-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(52, 211, 153, 0.28) transparent;
}

.emoji-picker-scroll::-webkit-scrollbar {
  width: 6px;
}

.emoji-picker-scroll::-webkit-scrollbar-thumb {
  background: rgba(52, 211, 153, 0.22);
  border-radius: 999px;
}

.tone-chip {
  display: grid;
  height: 2.75rem;
  width: 2.75rem;
  place-items: center;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  transition: transform 180ms ease, background 180ms ease, border-color 180ms ease;
}

.tone-chip--active {
  border-color: rgba(52, 211, 153, 0.6);
  background: rgba(16, 185, 129, 0.18);
  color: white;
  transform: translateY(-1px);
}

.emoji-row,
.emoji-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.45rem;
}

.emoji-row {
  display: flex;
  overflow-x: auto;
  gap: 0.5rem;
  padding: 0.25rem 0.15rem 0.35rem;
}

.emoji-chip {
  display: grid;
  min-width: 2.65rem;
  height: 2.65rem;
  place-items: center;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.06);
  font-size: 1.35rem;
  transition: transform 160ms ease, background 160ms ease;
}

.emoji-chip--hand {
  background: linear-gradient(180deg, rgba(16, 185, 129, 0.18), rgba(255, 255, 255, 0.05));
  border-color: rgba(110, 231, 183, 0.18);
}

.emoji-chip:hover,
.emoji-card:hover {
  transform: translateY(-2px) scale(1.04);
}

.emoji-card {
  position: relative;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: 1.05rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.04);
  font-size: clamp(1.15rem, 3vw, 1.45rem);
  transition: transform 160ms ease, background 160ms ease, box-shadow 160ms ease;
}

.emoji-card:hover {
  background: rgba(16, 185, 129, 0.16);
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.18);
}

.emoji-card--search {
  background: rgba(255, 255, 255, 0.055);
  border-color: rgba(110, 231, 183, 0.12);
}

.emoji-card--search:hover {
  background: rgba(16, 185, 129, 0.2);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.2);
}

.emoji-tone-dot {
  position: absolute;
  right: 0.4rem;
  bottom: 0.4rem;
  height: 0.38rem;
  width: 0.38rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #34d399, #10b981);
}

.category-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border-radius: 999px;
  padding: 0.65rem 0.85rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.52);
  white-space: nowrap;
  transition: background 180ms ease, color 180ms ease, transform 180ms ease;
}

.category-pill--active {
  background: rgba(16, 185, 129, 0.18);
  color: #ecfdf5;
  transform: translateY(-1px);
}

.emoji-grid--placeholder {
  gap: 0.4rem;
}

.emoji-placeholder {
  aspect-ratio: 1;
  border-radius: 1.05rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.05));
  background-size: 200% 100%;
  animation: shimmer 1.2s linear infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style> -->
