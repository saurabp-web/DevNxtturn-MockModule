<template>
  <AnimatedEmoji :emoji="emoji" :animated="animated" :size="size" class="emoji-glyph" />
</template>

<script>
import AnimatedEmoji from './AnimatedEmoji.vue'

export default {
  name: 'EmojiGlyph',
  components: {
    AnimatedEmoji,
  },
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
}
</script>

<style scoped>
.emoji-glyph {
  user-select: none;
}
</style>
