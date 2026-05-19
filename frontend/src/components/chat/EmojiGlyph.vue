<template>
  <span class="emoji-glyph" :class="{ animated }" :style="glyphStyle" :aria-label="emoji" role="img">
    {{ emoji }}
  </span>
</template>

<script>
export default {
  name: 'EmojiGlyph',
  props: {
    emoji: {
      type: String,
      required: true,
    },
    animated: {
      type: Boolean,
      default: false,
    },
    size: {
      type: [Number, String],
      default: 20,
    },
  },
  computed: {
    glyphStyle() {
      const value = typeof this.size === 'number' ? `${this.size}px` : this.size
      return {
        '--emoji-size': value,
      }
    },
  },
}
</script>

<style scoped>
.emoji-glyph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
  line-height: 1;
  font-size: var(--emoji-size);
  user-select: none;
}

.animated {
  animation: emoji-live 2.8s ease-in-out infinite;
  transform-origin: center;
}

@keyframes emoji-live {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-1px) scale(1.08);
  }
}
</style>
