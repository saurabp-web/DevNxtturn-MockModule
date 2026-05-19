<template>
  <div
    :class="['flex w-full mb-3', isMe ? 'justify-end' : 'justify-start']"
    @dblclick="toggleReactions"
    @touchend="onTouchEnd"
    @touchmove="onTouchMove"
    @contextmenu="onContextMenu"
  >
    <div :class="['flex max-w-[85%] flex-col gap-1.5', isMe ? 'items-end' : 'items-start']">
      <!-- Reactions popup - Matching your chat theme -->
      <transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="transform scale-95 opacity-0 -translate-y-2"
        enter-to-class="transform scale-100 opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="transform scale-100 opacity-100 translate-y-0"
        leave-to-class="transform scale-95 opacity-0 -translate-y-2"
      >
        <div
          v-if="showReactions"
          class="z-30 inline-flex gap-2 rounded-2xl border border-white/80 bg-white/95 p-2 shadow-xl backdrop-blur-xl"
        >
          <button
            v-for="emoji in quickEmojis"
            :key="emoji"
            class="flex h-9 w-9 items-center justify-center rounded-xl text-xl transition-all hover:bg-slate-100 hover:scale-110 active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            type="button"
            :aria-label="`React with ${emoji} emoji`"
            @click="selectReaction(emoji)"
          >
            <EmojiGlyph :emoji="emoji" animated :size="22" />
          </button>
        </div>
      </transition>

      <!-- Message Bubble -->
      <div class="relative">
        <!-- Reply Preview -->
        <div
          v-if="replyToMessage"
          class="mb-1.5 rounded-xl border-l-2 border-blue-400 bg-slate-50/80 px-3 py-2 text-xs backdrop-blur-sm"
          :class="isMe ? 'mr-2' : 'ml-2'"
        >
          <div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-600">
            Replying to {{ replyToMessage.sender_username }}
          </div>
          <div class="truncate text-[11px] font-medium text-slate-600">
            {{ replyToMessage.content }}
          </div>
        </div>

        <!-- Main Message Card -->
        <div
          class="relative group transition-all duration-200"
          :class="[
            isDeleted
              ? 'bg-slate-100/80 rounded-2xl px-4 py-2.5 backdrop-blur-sm'
              : 'rounded-2xl overflow-hidden shadow-sm',
            !isDeleted && !isMediaOnly ? 'px-4 py-2.5' : '',
            !isDeleted && !isMediaOnly && !isMe
              ? 'border border-slate-200/80 bg-white/90 backdrop-blur-sm'
              : '',
            isMe && !isDeleted && !isMediaOnly
              ? 'bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-md shadow-blue-200/50'
              : 'text-slate-900',
            isMe && !isDeleted && !isMediaOnly ? 'rounded-br-md' : 'rounded-bl-md',
          ]"
        >
          <!-- Deleted Message -->
          <div v-if="isDeleted" class="flex items-center gap-2">
            <svg
              class="h-4 w-4 text-slate-400"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                d="M12 9v4m0 4h.01M10.29 3.86l-8.1 14A2 2 0 004.1 21h15.8a2 2 0 001.91-2.14l-8.1-14a2 2 0 00-3.42 0z"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <span class="italic text-sm text-slate-500">This message was deleted</span>
          </div>

          <template v-else>
            <!-- Text Content -->
            <div
              v-if="hasText"
              class="chat-message-content break-words leading-relaxed text-sm"
              :class="[hasMedia ? 'mb-2' : '']"
              v-html="linkedContent"
            ></div>

            <!-- Media Content -->
            <div v-if="hasMedia" class="group/media relative rounded-xl overflow-hidden">
              <div
                v-if="mediaLoading"
                class="absolute inset-0 flex items-center justify-center bg-slate-100"
              >
                <div
                  class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"
                ></div>
              </div>

              <img
                v-show="!mediaLoading"
                v-if="isImage(media)"
                :src="cachedMediaUrl"
                alt="Shared media"
                class="block max-h-[250px] w-full cursor-pointer object-cover transition-transform hover:scale-105"
                @click="openImage(cachedMediaUrl)"
                @load="onMediaLoad"
                @error="onMediaError"
              />

              <video
                v-else-if="isVideo(media)"
                :src="cachedMediaUrl"
                controls
                class="block max-h-[250px] w-full rounded-xl"
                @loadeddata="onMediaLoad"
                @error="onMediaError"
              />

              <div
                v-else-if="mediaError"
                class="flex items-center justify-center p-6 bg-red-50/80 rounded-xl backdrop-blur-sm"
              >
                <div class="text-center">
                  <svg
                    class="mx-auto h-8 w-8 text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  <p class="mt-1 text-xs text-red-500">Failed to load</p>
                </div>
              </div>

              <a
                v-else
                :href="cachedMediaUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center gap-3 rounded-xl bg-slate-50/80 p-3 backdrop-blur-sm hover:bg-slate-100 transition-colors"
              >
                <svg
                  class="h-8 w-8 text-slate-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <div class="flex-1">
                  <div class="text-sm font-medium text-slate-700">File attachment</div>
                  <div class="text-xs text-slate-500">Click to download</div>
                </div>
              </a>

            </div>

            <!-- Timestamp and Actions -->
            <div
              class="flex items-center gap-2 mt-1.5"
              :class="isMe ? 'justify-end' : 'justify-start'"
            >
              <span
                class="text-[10px] font-medium"
                :class="isMe ? 'text-blue-100' : 'text-slate-400'"
              >
                {{ formattedTime }}
              </span>
              <span
                v-if="message.edited_at"
                class="text-[9px]"
                :class="isMe ? 'text-blue-100' : 'text-slate-400'"
              >
                Edited
              </span>
              <!-- Reply button that appears on hover -->
              <button
                v-if="!isDeleted"
                class="opacity-0 group-hover:opacity-100 transition-opacity"
                @click="emitReply"
              >
                <svg
                  class="h-3.5 w-3.5"
                  :class="
                    isMe ? 'text-blue-100 hover:text-white' : 'text-slate-400 hover:text-blue-600'
                  "
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M3 10l7-7v4c8 0 11 5 11 13-3-5-7-6-11-6v4l-7-8z"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                  />
                </svg>
              </button>
            </div>
          </template>
        </div>

        <!-- Reactions Display -->
        <div
          v-if="!isDeleted && reactions.length > 0"
          class="flex flex-wrap gap-1 mt-1"
          :class="isMe ? 'justify-end' : 'justify-start'"
        >
          <div
            v-for="reaction in reactions"
            :key="reaction.emoji"
            class="flex items-center gap-1 rounded-full border border-slate-200/80 bg-white/90 px-2 py-0.5 text-xs font-medium text-slate-600 shadow-sm backdrop-blur-sm cursor-pointer transition hover:scale-105 hover:bg-white"
            @click="selectReaction(reaction.emoji)"
          >
            <span>{{ reaction.emoji }}</span>
            <span>{{ reaction.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Context Menu - Matching your theme -->
    <teleport to="body">
      <transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition duration-120 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="showActions"
          ref="actionMenu"
          class="fixed z-[120] w-48 overflow-hidden rounded-xl bg-white/95  shadow-xl border border-slate-200/80 py-1 backdrop-blur-xl"
          :style="actionMenuStyle"
          role="menu"
          @click.stop
        >


          <button
            class="flex w-full items-center gap-3 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            @click="emitReply"
          >
            <svg
              class="h-4 w-4 text-slate-500"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                d="M3 10l7-7v4c8 0 11 5 11 13-3-5-7-6-11-6v4l-7-8z"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Reply
          </button>
          <button
            class="flex w-full items-center gap-3 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            @click="copyMessage"
          >
            <svg
              class="h-4 w-4 text-slate-500"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path d="M8 8h10v12H8z" stroke-linejoin="round" />
              <path
                d="M6 16H5a2 2 0 01-2-2V5a2 2 0 012-2h9a2 2 0 012 2v1"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Copy
          </button>
          <div v-if="isMe && !isDeleted" class="my-1 border-t border-slate-100"></div>
          <button
            v-if="isMe && !isDeleted && canEdit"
            class="flex w-full items-center gap-3 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            @click="emitEdit"
          >
            <svg
              class="h-4 w-4 text-slate-500"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                d="M4 20h4l10-10a2.5 2.5 0 10-4-4L4 16v4z"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Edit
          </button>
          <button
            v-if="isMe && !isDeleted"
            class="flex w-full items-center gap-3 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
            @click="emitDelete"
          >
            <svg
              class="h-4 w-4 text-red-500"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                d="M6 7h12M9 7V5h6v2m-8 0l1 14h6l1-14"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Delete
          </button>
        </div>
      </transition>
    </teleport>

    <!-- Image Preview Modal -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showImagePreview"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/95 p-4 backdrop-blur-md"
        @click.self="closeImage"
        @keydown.escape="closeImage"
      >
        <div class="relative max-h-[90vh] max-w-[90vw]">
          <img
            :src="previewUrl"
            alt="Full screen preview"
            class="max-h-[90vh] max-w-[90vw] object-contain rounded-2xl shadow-2xl"
          />
          <button
            class="absolute -top-12 right-0 text-white text-2xl hover:text-slate-300 transition-colors"
            @click.stop="closeImage"
          >
            ✕
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import EmojiGlyph from './EmojiGlyph.vue'
import { buildMediaUrl } from '@/utils/avatars'

const QUICK_EMOJIS = ['👍', '❤️', '😂', '😮', '😢', '🔥']
const TEXT_EMOJI_REGEX =
  /(?:\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?(?:\u200D\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?)*|[#*0-9]\uFE0F?\u20E3|\p{Regional_Indicator}{2})/gu

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function emojiMarkup(emoji) {
  const escaped = escapeHtml(emoji)
  return `<span class="emoji-inline emoji-inline--text" aria-label="${escaped}" role="img">${escaped}</span>`
}

export default {
  name: 'MessageBubble',
  components: {
    EmojiGlyph,
  },
  emits: ['react', 'reply', 'edit', 'delete', 'media-error'],
  props: {
    message: {
      type: Object,
      required: true,
    },
    isMe: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showReactions: false,
      lastTap: 0,
      wasScrolling: false,
      showImagePreview: false,
      previewUrl: '',
      showActions: false,
      actionMenuX: 0,
      actionMenuY: 0,
      mediaLoading: true,
      mediaError: false,
      _cachedTimestamp: null,
      _cachedFormattedTime: null,
      _cachedMediaUrl: null,
    }
  },
  computed: {
    quickEmojis() {
      return QUICK_EMOJIS
    },
    reactions() {
      return this.message?.reactions || []
    },
    isDeleted() {
      return Boolean(this.message?.is_deleted)
    },
    hasText() {
      return Boolean(this.message?.content) && !this.isDeleted
    },
    sanitizedContent() {
      if (!this.hasText) return ''
      return this.message.content
    },
    linkedContent() {
      if (!this.hasText) return ''

      const rawText = String(this.message?.content || '')
      const urlPattern = /((https?:\/\/|www\.)[^\s<]+)/gi
      const pieces = []
      let lastIndex = 0

      rawText.replace(urlPattern, (rawUrl, _protocol, _www, offset) => {
        pieces.push(escapeHtml(rawText.slice(lastIndex, offset)).replace(/\n/g, '<br>'))

        let href = rawUrl
        let trailing = ''

        while (/[),.!?:;]$/.test(href)) {
          trailing = href.slice(-1) + trailing
          href = href.slice(0, -1)
        }

        const finalHref = href.startsWith('http') ? href : `https://${href}`
        try {
          const parsed = new URL(finalHref)
          if (!['http:', 'https:'].includes(parsed.protocol)) {
            pieces.push(escapeHtml(rawUrl))
            lastIndex = offset + rawUrl.length
            return rawUrl
          }
        } catch {
          pieces.push(escapeHtml(rawUrl))
          lastIndex = offset + rawUrl.length
          return rawUrl
        }

        pieces.push(
          `<a href="${escapeHtml(finalHref)}" target="_blank" rel="noopener noreferrer" class="chat-link">${escapeHtml(href)}</a>${escapeHtml(trailing)}`,
        )
        lastIndex = offset + rawUrl.length
        return rawUrl
      })

      pieces.push(escapeHtml(rawText.slice(lastIndex)))

      return pieces
        .join('')
        .replace(TEXT_EMOJI_REGEX, (emoji) => emojiMarkup(emoji))
        .replace(/\n/g, '<br>')
    },
    media() {
      return this.message || null
    },
    hasMedia() {
      return Boolean((this.media?.media_url || this.media?.media) && !this.isDeleted)
    },
    isMediaOnly() {
      return this.hasMedia && !this.hasText
    },
    formattedTime() {
      const ts = this.message?.timestamp
      if (!ts) return ''

      if (this._cachedTimestamp === ts && this._cachedFormattedTime) {
        return this._cachedFormattedTime
      }

      this._cachedTimestamp = ts
      this._cachedFormattedTime = new Date(ts).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
      return this._cachedFormattedTime
    },
    actionMenuStyle() {
      return {
        left: `${this.actionMenuX}px`,
        top: `${this.actionMenuY}px`,
      }
    },
    canEdit() {
      return Boolean(this.message?.can_edit)
    },
    replyToMessage() {
      return this.message?.reply_to_message || null
    },
    cachedMediaUrl() {
      if (!this.hasMedia) return ''
      if (this._cachedMediaUrl) return this._cachedMediaUrl

      let raw = this.media?.media_url || this.media?.media || ''
      if (!raw) return ''
      this._cachedMediaUrl = buildMediaUrl(raw)
      return this._cachedMediaUrl
    },
  },
  methods: {
    onContextMenu(event) {
      if (this.isDeleted) return
      event.preventDefault()
      const offset = 12
      const menuWidth = 192
      const menuHeight = this.isMe ? 210 : 140
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight

      this.actionMenuX = Math.max(
        offset,
        Math.min(event.clientX + offset, viewportWidth - menuWidth - offset),
      )
      this.actionMenuY = Math.max(
        offset,
        Math.min(event.clientY + offset, viewportHeight - menuHeight - offset),
      )
      this.showActions = true
      this.showReactions = false
    },
    closeActions(event) {
      if (event && this.$refs.actionMenu && this.$refs.actionMenu.contains(event.target)) {
        return
      }
      this.showActions = false
    },
    onKeydown(event) {
      if (event.key === 'Escape') {
        this.closeActions()
      }
    },
    handlePreviewKeydown(event) {
      if (event.key === 'Escape') {
        this.closeImage()
      }
    },
    isImage(m) {
      const mt = m?.media_type || ''
      if (mt.startsWith('image/')) return true
      const url = this.cachedMediaUrl.toLowerCase()
      return (
        url.endsWith('.jpg') ||
        url.endsWith('.jpeg') ||
        url.endsWith('.png') ||
        url.endsWith('.gif') ||
        url.endsWith('.webp')
      )
    },
    isVideo(m) {
      const mt = m?.media_type || ''
      if (mt.startsWith('video/')) return true
      const url = this.cachedMediaUrl.toLowerCase()
      return (
        url.endsWith('.mp4') ||
        url.endsWith('.webm') ||
        url.endsWith('.ogg') ||
        url.endsWith('.mov')
      )
    },
    onMediaLoad() {
      this.mediaLoading = false
      this.mediaError = false
    },
    onMediaError() {
      this.mediaLoading = false
      this.mediaError = true
      this.$emit('media-error', { messageId: this.message.id })
    },
    openImage(url) {
      if (!url) return
      this.previewUrl = url
      this.showImagePreview = true
      document.addEventListener('keydown', this.handlePreviewKeydown)
    },
    closeImage() {
      this.showImagePreview = false
      this.previewUrl = ''
      document.removeEventListener('keydown', this.handlePreviewKeydown)
    },
    selectReaction(emoji) {
      if (this.isDeleted) return
      this.$emit('react', { messageId: this.message.id, emoji })
      this.showReactions = false
      this.showActions = false
    },
    toggleReactions() {
      if (this.isDeleted) return
      this.showReactions = !this.showReactions
      if (this.showActions) this.showActions = false
    },
    onTouchEnd(event) {
      if (this.isDeleted) return
      if (event.cancelable) {
        event.preventDefault()
      }
      const now = Date.now()
      const delta = now - this.lastTap
      this.lastTap = now
      if (delta > 0 && delta < 300 && !this.wasScrolling) {
        this.toggleReactions()
      }
      this.wasScrolling = false
    },
    onTouchMove() {
      this.wasScrolling = true
    },
    emitEdit() {
      this.closeActions()
      this.$emit('edit', this.message)
    },
    emitDelete() {
      this.closeActions()
      this.$emit('delete', this.message)
    },
    emitReply() {
      this.closeActions()
      this.$emit('reply', this.message)
    },
    async writeToClipboard(text) {
      if (!text) return false
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text)
        return true
      }

      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      return true
    },
    async copyMessage() {
      const text =
        this.message?.content?.trim() ||
        this.cachedMediaUrl ||
        this.message?.media_url ||
        this.message?.media ||
        ''
      if (!text) {
        this.closeActions()
        return
      }
      try {
        await this.writeToClipboard(text)
      } catch (error) {
        console.error('Failed to copy:', error)
      } finally {
        this.closeActions()
      }
    },
  },
  mounted() {
    document.addEventListener('click', this.closeActions)
    document.addEventListener('keydown', this.onKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeActions)
    document.removeEventListener('keydown', this.onKeydown)
    document.removeEventListener('keydown', this.handlePreviewKeydown)
  },
}
</script>

<style scoped>
/* Clickable links inside messages */
.chat-message-content :deep(.chat-link),
.chat-message-content .chat-link {
  color: #2563eb;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
  word-break: break-word;
}

.chat-message-content :deep(.chat-link:hover),
.chat-message-content .chat-link:hover {
  color: #1d4ed8;
}

.chat-message-content :deep(.emoji-inline),
.chat-message-content .emoji-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1em;
  height: 1.1em;
  vertical-align: -0.15em;
}

.chat-message-content :deep(.emoji-inline--image),
.chat-message-content .emoji-inline--image {
  object-fit: contain;
}

.chat-message-content :deep(.emoji-inline--text),
.chat-message-content .emoji-inline--text {
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  animation: emoji-live 2.8s ease-in-out infinite;
  transform-origin: center;
}

@keyframes emoji-live {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-1px) scale(1.05);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

/* Smooth transitions */
.list-enter-active,
.list-leave-active {
  transition: all 0.2s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(5px);
}
</style>
