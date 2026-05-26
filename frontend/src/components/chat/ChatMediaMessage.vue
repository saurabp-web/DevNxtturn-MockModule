<template>
  <div
    class="chat-media-message"
    :class="[`chat-media-message--${kind}`, compact ? 'chat-media-message--compact' : '']"
    :style="mediaStyle"
  >
    <div class="chat-media-message__frame">
      <div v-if="isLoading" class="chat-media-message__skeleton">
        <div class="chat-media-message__skeleton-shimmer"></div>
      </div>

      <video
        v-if="isGif && shouldUseVideo"
        :src="sourceUrl"
        class="chat-media-message__media"
        autoplay
        loop
        muted
        playsinline
        preload="metadata"
        @loadeddata="isLoading = false"
        @error="handleError"
      ></video>

      <img
        v-else
        :src="sourceUrl"
        :alt="title"
        class="chat-media-message__media"
        loading="lazy"
        decoding="async"
        @load="isLoading = false"
        @error="handleError"
      />
    </div>
    <div v-if="showMeta && isGif" class="mt-2 flex items-center justify-between gap-3 px-1">
      <div class="min-w-0">
        <div class="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
          {{ label }}
        </div>
        <div class="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
          Tap to reply, react, or share.
        </div>
      </div>
      <span
        class="shrink-0 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.2em] text-slate-500 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
      >
        {{ kindLabel }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    kind: 'gif' | 'sticker'
    sourceUrl: string
    previewUrl?: string
    title?: string
    label?: string
    animated?: boolean
    compact?: boolean
    showMeta?: boolean
  }>(),
  {
    title: '',
    label: '',
    animated: true,
    compact: false,
    showMeta: true,
  },
)

const isLoading = ref(true)
const hasError = ref(false)

const isGif = computed(() => props.kind === 'gif')
const kindLabel = computed(() => (props.kind === 'gif' ? 'GIF' : 'Sticker'))
const shouldUseVideo = computed(() => props.sourceUrl.toLowerCase().endsWith('.mp4'))
const label = computed(() => props.label || props.title || kindLabel.value)
const mediaStyle = computed(() => ({
  '--chat-media-max-width': props.kind === 'gif' ? '20rem' : '12.5rem',
  '--chat-media-max-height': props.kind === 'gif' ? '22rem' : '14rem',
  '--chat-media-min-width': props.compact ? '10rem' : props.kind === 'gif' ? '11.5rem' : '8.5rem',
}))

watch(
  () => props.sourceUrl,
  () => {
    isLoading.value = true
    hasError.value = false
  },
  { immediate: true },
)

function handleError() {
  hasError.value = true
  isLoading.value = false
}
</script>

<style scoped>
.chat-media-message {
  display: flex;
  flex-direction: column;
  width: fit-content;
  max-width: min(100%, var(--chat-media-max-width, 18.5rem));
  min-width: var(--chat-media-min-width, 0);
}

.chat-media-message--gif {
  max-width: min(100%, 19rem);
}

.chat-media-message--sticker {
  max-width: min(100%, 12.5rem);
}

.chat-media-message--compact {
  max-width: min(100%, 14rem);
}

.chat-media-message__frame {
  position: relative;
  overflow: hidden;
  border-radius: 1.5rem;
  background: linear-gradient(135deg, rgba(248, 250, 252, 0.98), rgba(226, 232, 240, 0.92));
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  padding: 0.55rem;
}

.chat-media-message--sticker .chat-media-message__frame {
  padding: 0.15rem;
  border-radius: 1.1rem;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.88)),
    radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.16) 1px, transparent 0);
  background-size: auto, 12px 12px;
  box-shadow:
    0 10px 24px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.dark .chat-media-message__frame {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.9));
  box-shadow:
    0 18px 40px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.chat-media-message__media {
  display: block;
  width: auto;
  max-width: 100%;
  max-height: var(--chat-media-max-height, 20rem);
  object-fit: cover;
  border-radius: 1.05rem;
  aspect-ratio: auto;
  background: rgba(255, 255, 255, 0.02);
}

.chat-media-message--sticker .chat-media-message__media {
  max-height: var(--chat-media-max-height, 14rem);
  object-fit: contain;
}

.chat-media-message__skeleton {
  position: absolute;
  inset: 0.55rem;
  overflow: hidden;
  border-radius: 1.05rem;
  background: rgba(148, 163, 184, 0.15);
}

.chat-media-message__skeleton-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, transparent 15%, rgba(255, 255, 255, 0.25) 35%, transparent 55%);
  animation: shimmer 1.6s linear infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}
</style>
