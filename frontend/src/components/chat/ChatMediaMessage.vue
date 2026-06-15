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
  '--chat-media-width': props.kind === 'gif' ? 'clamp(11rem, 32vw, 15.5rem)' : 'clamp(5.75rem, 20vw, 8rem)',
  '--chat-media-aspect': props.kind === 'gif' ? '4 / 3' : '1 / 1',
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
  max-width: 100%;
}

.chat-media-message__frame {
  position: relative;
  overflow: hidden;
  width: min(var(--chat-media-width, 15.5rem), 100%);
  aspect-ratio: var(--chat-media-aspect, 4 / 3);
  max-height: min(36vh, 14rem);
  border-radius: 0.9rem;
  background: linear-gradient(135deg, rgba(240, 249, 255, 0.98), rgba(238, 242, 255, 0.94));
  box-shadow:
    0 1px 1px rgba(15, 23, 42, 0.04),
    0 8px 22px rgba(79, 70, 229, 0.07);
}

.chat-media-message--sticker .chat-media-message__frame {
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.dark .chat-media-message__frame {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.9));
  box-shadow:
    0 18px 40px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.dark .chat-media-message--sticker .chat-media-message__frame {
  background: transparent;
  box-shadow: none;
}

.chat-media-message__media {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: inherit;
  background: rgba(255, 255, 255, 0.02);
}

.chat-media-message--sticker .chat-media-message__media {
  object-fit: contain;
  padding: 0;
}

@media (max-width: 480px) {
  .chat-media-message {
    width: fit-content;
  }

  .chat-media-message__frame {
    width: min(var(--chat-media-width, 15.5rem), calc(100vw - 2rem));
    border-radius: 0.85rem;
  }
}

.chat-media-message__skeleton {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
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
