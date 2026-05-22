<template>
  <span
    class="animated-emoji"
    :class="[motionClass, animated ? 'animated-emoji--active' : '']"
    :style="{
      width: `${size}px`,
      height: `${size}px`,
      fontSize: `${size}px`,
    }"
    aria-hidden="true"
  >
    <span class="animated-emoji__glyph">{{ emoji }}</span>
    <span v-if="isFire" class="animated-emoji__glow"></span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    emoji: string
    size?: number
    animated?: boolean
  }>(),
  {
    size: 20,
    animated: true,
  },
)

const isHeart = computed(() =>
  ['❤️', '❤', '💖', '💘', '💗', '💓', '💞', '💕', '😍', '🥰'].includes(props.emoji),
)
const isLaugh = computed(() => ['😂', '🤣'].includes(props.emoji))
const isFire = computed(() => ['🔥'].includes(props.emoji))
const isParty = computed(() => ['🎉', '🥳'].includes(props.emoji))

const motionClass = computed(() => {
  if (isHeart.value) return 'motion-heart'
  if (isLaugh.value) return 'motion-laugh'
  if (isFire.value) return 'motion-fire'
  if (isParty.value) return 'motion-party'
  return 'motion-generic'
})
</script>

<style scoped>
.animated-emoji {
  position: relative;
  display: inline-grid;
  place-items: center;
  line-height: 1;
  user-select: none;
  transform-origin: center center;
  will-change: transform, opacity, filter;
}

.animated-emoji__glyph {
  position: relative;
  z-index: 1;
  display: inline-block;
  transform-origin: center center;
  text-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
}

.animated-emoji--active.motion-generic {
  animation: emoji-pop 2.5s ease-in-out infinite;
}

.animated-emoji--active.motion-heart {
  animation: heart-beat 1.08s ease-in-out infinite;
  filter: drop-shadow(0 8px 16px rgba(244, 63, 94, 0.16));
}

.animated-emoji--active.motion-laugh {
  animation: laugh-wiggle 0.95s ease-in-out infinite;
}

.animated-emoji--active.motion-fire {
  animation: fire-flicker 0.9s ease-in-out infinite;
}

.animated-emoji--active.motion-party {
  animation: party-pop 1.25s cubic-bezier(0.34, 1.56, 0.64, 1) infinite;
}

.animated-emoji__glow {
  position: absolute;
  inset: 12%;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(251, 146, 60, 0.5), rgba(251, 146, 60, 0));
  filter: blur(6px);
  opacity: 0.7;
  transform: scale(0.9);
  animation: glow-pulse 1s ease-in-out infinite;
}

@keyframes emoji-pop {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes heart-beat {
  0%,
  100% {
    transform: scale(1);
  }
  18% {
    transform: scale(1.14);
  }
  36% {
    transform: scale(0.98);
  }
  54% {
    transform: scale(1.08);
  }
  72% {
    transform: scale(1);
  }
}

@keyframes laugh-wiggle {
  0%,
  100% {
    transform: rotate(0deg) scale(1);
  }
  20% {
    transform: rotate(-6deg) scale(1.03);
  }
  40% {
    transform: rotate(6deg) scale(1.06);
  }
  60% {
    transform: rotate(-4deg) scale(1.03);
  }
  80% {
    transform: rotate(4deg) scale(1.05);
  }
}

@keyframes fire-flicker {
  0%,
  100% {
    transform: scale(1) translateY(0);
    filter: saturate(1);
  }
  50% {
    transform: scale(1.08) translateY(-1px);
    filter: saturate(1.15);
  }
}

@keyframes party-pop {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  35% {
    transform: translateY(-2px) scale(1.1);
  }
  65% {
    transform: translateY(0) scale(1.03);
  }
}

@keyframes glow-pulse {
  0%,
  100% {
    opacity: 0.65;
    transform: scale(0.88);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}
</style>
