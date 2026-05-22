<!-- AnimatedMessage.vue -->

<template>
  <div
    class="animated-message"
    :class="{
      'emoji-only': isEmojiOnly,
    }"
  >
    <template
      v-for="(token, index) in tokens"
      :key="index"
    >
      <!-- TEXT -->
      <span
        v-if="token.type === 'text'"
        class="message-text"
      >
        {{ token.value }}
      </span>

      <!-- LINK -->
      <a
        v-else-if="token.type === 'link'"
        :href="token.href"
        target="_blank"
        rel="noopener noreferrer"
        class="message-link"
      >
        {{ token.value }}
      </a>

      <!-- EMOJI -->
      <AnimatedEmoji
        v-else-if="token.type === 'emoji'"
        :emoji="token.value"
        :size="emojiSize"
        :animated="isEmojiOnly"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AnimatedEmoji from './AnimatedEmoji.vue'
import {
  tokenizeMessageText,
  isEmojiOnlyMessage,
  getEmojiCount,
} from './emoji-parser'

const props = defineProps<{
  text: string
}>()

const tokens = computed(() =>
  tokenizeMessageText(props.text),
)

const isEmojiOnly = computed(() =>
  isEmojiOnlyMessage(tokens.value),
)

const emojiCount = computed(() =>
  getEmojiCount(tokens.value),
)

const emojiSize = computed(() => {
  // Normal inline emoji
  if (!isEmojiOnly.value) {
    return 22
  }

  // WhatsApp-like scaling
  switch (emojiCount.value) {
    case 1:
      return 58

    case 2:
      return 46

    case 3:
      return 38

    default:
      return 28
  }
})
</script>

<style scoped>
.animated-message {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  line-height: 1.4;
  word-break: break-word;
}

.emoji-only {
  justify-content: center;
  padding: 2px 0;
}

.message-text {
  color: inherit;
  font-size: 15px;
  line-height: 1.4;
}

.message-link {
  color: #22c55e;
  text-decoration: underline;
  font-weight: 600;
}
</style>
