<script lang="ts">
import { defineComponent } from 'vue'
import AnimatedEmoji from './AnimatedEmoji.vue'

export default defineComponent({
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
})
</script>

<template>
  <AnimatedEmoji :emoji="emoji" :animated="animated" :size="Number(size)" class="emoji-glyph" />
</template>

<style scoped>
.emoji-glyph {
  user-select: none;
}
</style>
