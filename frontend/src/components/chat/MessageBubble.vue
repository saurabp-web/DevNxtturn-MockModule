<template>
  <div
    :class="['mb-3 flex w-full', isMe ? 'justify-end' : 'justify-start']"
    :data-message-id="message?.id"
    @dblclick="toggleReactions"
    @pointerdown="onPointerDown"
    @pointerup="onPointerUp"
    @pointercancel="onPointerCancel"
    @pointermove="onPointerMove"
    @contextmenu="onContextMenu"
  >
    <div :class="['flex max-w-[85%] flex-col gap-1.5', isMe ? 'items-end' : 'items-start']">
      <!-- Reactions Popup -->
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
          class="z-30 inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-[#1e1e1e]/95 px-3 py-2 shadow-[0_18px_40px_rgba(0,0,0,0.28)] backdrop-blur-xl"
        >
          <button
            v-for="emoji in quickEmojis"
            :key="emoji"
            class="flex h-8 w-8 items-center justify-center rounded-full text-xl transition-transform duration-150 hover:scale-110 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/25"
            type="button"
            :aria-label="`React with ${emoji} emoji`"
            @click="selectReaction(emoji)"
          >
            <span class="reaction-emoji">{{ emoji }}</span>
          </button>
          <button
            class="flex h-8 w-8 items-center justify-center rounded-full text-[20px] font-medium leading-none text-white/90 transition-transform duration-150 hover:scale-110 hover:bg-white/10 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/25"
            type="button"
            aria-label="Open emoji palette"
            @click="toggleEmojiPalette"
          >
            +
          </button>
        </div>
      </transition>

      <div class="relative">
        <!-- Reply Preview -->
        <div
          v-if="replyToMessage"
          class="mb-1.5 rounded-lg border-l-4 border-purple-500 bg-white px-3 py-2 text-xs shadow-sm"
          :class="isMe ? 'mr-2' : 'ml-2'"
        >
          <div class="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-purple-600">
            Replying to {{ replyToMessage.sender_username }}
          </div>
          <div class="line-clamp-2 text-[11px] font-medium text-slate-600">
            {{ replyPreviewText(replyToMessage) }}
          </div>
        </div>

        <!-- Main Message Card -->
        <div
          class="relative overflow-hidden rounded-2xl shadow-sm transition-all duration-200 group"
          :class="[
            isDeleted
              ? 'bg-slate-100/80 px-4 py-2.5 backdrop-blur-sm'
              : isEmojiOnlyMessage
                ? 'bg-transparent px-0 py-0 shadow-none overflow-visible'
                : isChatMediaMessage
                  ? 'bg-transparent px-0 py-0 shadow-none overflow-visible'
                : 'px-4 py-2.5',
            !isDeleted && !isMediaOnly && !isEmojiOnlyMessage && !isChatMediaMessage && !isMe
              ? 'border border-slate-200/80 bg-white/90 backdrop-blur-sm'
              : '',
            isMe && !isDeleted && !isMediaOnly && !isEmojiOnlyMessage && !isChatMediaMessage
              ? 'bg-purple-500 text-white shadow-md shadow-purple-200/40'
              : 'text-slate-900',
            isMe && !isDeleted && !isMediaOnly && !isEmojiOnlyMessage && !isChatMediaMessage
              ? 'rounded-br-md'
              : 'rounded-bl-md',
          ]"
        >
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
            <template v-if="isChatMediaMessage">
              <ChatMediaMessage
                :kind="messageType === 'gif' ? 'gif' : 'sticker'"
                :source-url="chatMediaSourceUrl"
                :title="chatMediaTitle"
                :label="chatMediaLabel"
                :animated="Boolean(message?.animated)"
                :compact="isMe"
                :show-meta="messageType === 'gif'"
              />
            </template>

            <!-- Text Content -->
            <div
              v-if="hasText"
              :class="[
                'text-sm leading-relaxed break-words',
                hasMedia ? 'mb-2' : '',
                isEmojiOnlyMessage ? 'emoji-only-message' : '',
              ]"
            >
              <template v-if="isEmojiOnlyMessage">
                <div class="emoji-only-message__row">
                  <AnimatedEmoji
                    v-for="(emoji, index) in emojiOnlyEmojis"
                    :key="`${emoji}-${index}`"
                    :emoji="emoji"
                    :size="emojiOnlySize"
                    :animated="true"
                  />
                </div>
              </template>
              <template v-else>
                <AnimatedMessage :text="message.content" />
              </template>
            </div>

            <!-- Media Content -->
            <div v-if="hasMedia" class="group/media relative overflow-hidden rounded-xl bg-slate-100">
              <div
                v-if="mediaLoading"
                class="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm"
              >
                <div class="h-8 w-8 animate-spin rounded-full border-2 border-purple-400 border-t-transparent"></div>
              </div>

              <img
                v-if="isImage(media)"
                v-show="!mediaLoading"
                :src="cachedMediaUrl"
                alt="Shared media"
                class="block max-h-[300px] min-h-[200px] w-full cursor-pointer object-cover transition-transform hover:scale-105"
                @click="openImage(cachedMediaUrl)"
                @load="onMediaLoad"
                @error="onMediaError"
              />

              <video
                v-else-if="isVideo(media)"
                :src="cachedMediaUrl"
                controls
                class="block max-h-[300px] min-h-[200px] w-full rounded-xl bg-black"
                @loadeddata="onMediaLoad"
                @error="onMediaError"
              />

              <div
                v-else-if="mediaError"
                class="flex items-center justify-center rounded-xl bg-rose-50 p-6"
              >
                <div class="text-center">
                  <svg
                    class="mx-auto h-8 w-8 text-rose-400"
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
                  <p class="mt-1 text-xs text-rose-500">Failed to load</p>
                </div>
              </div>

              <a
                v-else
                :href="cachedMediaUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center gap-3 rounded-xl bg-slate-50 p-3 transition-colors hover:bg-slate-100"
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
            <div class="mt-1.5 flex items-center gap-2" :class="isMe ? 'justify-end' : 'justify-start'">
              <span class="text-[10px] font-medium" :class="isMe ? 'text-purple-100' : 'text-slate-400'">
                {{ formattedTime }}
              </span>
              <span
                v-if="message.edited_at"
                class="text-[9px] font-medium"
                :class="isMe ? 'text-purple-100' : 'text-slate-400'"
              >
                Edited
              </span>
              <span
                v-if="isMe && !isDeleted"
                class="inline-flex items-center gap-1 text-[9px] font-semibold"
                :class="statusClass"
                :aria-label="statusLabel"
              >
                <svg
                  v-if="deliveryState !== 'seen'"
                  class="h-3 w-3"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  viewBox="0 0 24 24"
                >
                  <path d="M4 12.5l5 5L20 6.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <svg
                  v-else
                  class="h-3 w-3"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  viewBox="0 0 24 24"
                >
                  <path d="M4 12.5l5 5L20 6.5" stroke-linecap="round" stroke-linejoin="round" />
                  <path d="M10 12.5l5 5L20 10" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <button
                v-if="!isDeleted"
                class="opacity-0 transition-opacity duration-200 group-hover:opacity-100 focus:opacity-100"
                type="button"
                @click="emitReply"
              >
                <svg
                  class="h-3.5 w-3.5"
                  :class="isMe ? 'text-purple-100 hover:text-white' : 'text-slate-400 hover:text-purple-500'"
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
          class="mt-1 flex flex-wrap gap-1"
          :class="isMe ? 'justify-end' : 'justify-start'"
        >
          <button
            v-for="reaction in visibleReactions"
            :key="reaction.emoji"
            class="flex cursor-pointer items-center gap-1 rounded-full border border-slate-200/80 bg-white/90 px-2 py-0.5 text-xs font-medium text-slate-600 shadow-sm backdrop-blur-sm transition-all hover:scale-105 hover:bg-white hover:shadow-md"
            type="button"
            :aria-label="`React with ${reaction.emoji}`"
            @click="selectReaction(reaction.emoji)"
          >
            <span class="reaction-emoji reaction-emoji--small">{{ reaction.emoji }}</span>
            <span>{{ reaction.count }}</span>
          </button>
        </div>

        <!-- More Reactions Panel -->
        <transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 translate-y-1 scale-95"
          enter-to-class="opacity-100 translate-y-0 scale-100"
          leave-active-class="transition duration-120 ease-in"
          leave-from-class="opacity-100 translate-y-0 scale-100"
          leave-to-class="opacity-0 translate-y-1 scale-95"
        >
          <div
            v-if="showEmojiPalette"
            ref="emojiPalette"
            class="mt-2 flex"
            :class="isMe ? 'justify-end' : 'justify-start'"
            @click.stop
          >
            <EmojiPicker
              :open="showEmojiPalette"
              @select="selectReactionFromPalette"
              @close="showEmojiPalette = false"
            />
          </div>
        </transition>
      </div>
    </div>

    <!-- Context Menu -->
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
          class="fixed z-[120] w-56 overflow-hidden rounded-xl border border-purple-100/80 bg-white/95 py-1 shadow-xl backdrop-blur-xl"
          :style="actionMenuStyle"
          role="menu"
          @click.stop
        >
          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-purple-50"
            type="button"
            @click="emitReply"
          >
            <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path
                d="M3 10l7-7v4c8 0 11 5 11 13-3-5-7-6-11-6v4l-7-8z"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Reply
          </button>

          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-purple-50"
            type="button"
            @click="copyMessage"
          >
            <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M8 8h10v12H8z" stroke-linejoin="round" />
              <path
                d="M6 16H5a2 2 0 01-2-2V5a2 2 0 012-2h9a2 2 0 012 2v1"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            Copy
          </button>

          <div v-if="isMe && !isDeleted" class="my-1 border-t border-purple-100"></div>

          <button
            v-if="isMe && !isDeleted && canEdit && !isChatMediaMessage"
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-purple-50"
            type="button"
            @click="emitEdit"
          >
            <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
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
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50"
            type="button"
            @click="emitDelete"
          >
            <svg class="h-4 w-4 text-rose-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
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
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-4 backdrop-blur-md"
        @click.self="closeImage"
        @keydown.escape="closeImage"
      >
        <div class="relative max-h-[90vh] max-w-[90vw]">
          <img
            :src="previewUrl"
            alt="Full screen preview"
            class="max-h-[90vh] max-w-[90vw] rounded-2xl object-contain shadow-2xl"
          />
          <button
            class="absolute -top-12 right-0 text-2xl text-white/80 transition-colors hover:text-white"
            type="button"
            @click.stop="closeImage"
          >
            ×
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import AnimatedEmoji from './AnimatedEmoji.vue'
import AnimatedMessage from './AnimatedMessage.vue'
import EmojiPicker from './EmojiPicker.vue'
import ChatMediaMessage from './ChatMediaMessage.vue'
import { describeMediaItem } from './chatMediaCatalog'
import { buildMediaUrl } from '@/utils/avatars'
import { isEmojiOnlyMessage, tokenizeMessageText } from './emoji-parser'

const QUICK_EMOJIS = ['👍', '❤️', '😂', '😮', '😢', '🙏']
const EXTRA_REACTION_EMOJIS = [
  '😀',
  '😄',
  '😁',
  '😆',
  '😉',
  '😊',
  '😍',
  '😘',
  '🥳',
  '😎',
  '😇',
  '🤝',
  '👏',
  '🙏',
  '💯',
  '🔥',
  '💖',
  '💘',
  '❤️',
  '👍',
  '👀',
  '🎉',
  '😮',
  '😂',
]

export default {
  name: 'MessageBubble',
  components: {
    AnimatedEmoji,
    AnimatedMessage,
    EmojiPicker,
    ChatMediaMessage,
  },
  emits: ['react', 'reply', 'edit', 'delete', 'media-load', 'media-error', 'open-reaction-picker'],
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
      pressTimer: null,
      pointerIsDown: false,
      activePointerType: '',
      showImagePreview: false,
      previewUrl: '',
      showActions: false,
      showEmojiPalette: false,
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
    emojiTokens() {
      return tokenizeMessageText(this.message?.content || '')
    },
    isEmojiOnlyText() {
      return isEmojiOnlyMessage(this.emojiTokens)
    },
    emojiOnlyEmojis() {
      return this.emojiTokens.filter((token) => token.type === 'emoji').map((token) => token.value)
    },
    emojiOnlySize() {
      switch (this.emojiOnlyEmojis.length) {
        case 1:
          return 58
        case 2:
          return 46
        case 3:
          return 38
        default:
          return 28
      }
    },
    reactions() {
      return this.message?.reactions || []
    },
    visibleReactions() {
      return this.reactions.slice(0, 2)
    },
    deliveryState() {
      if (!this.isMe || this.isDeleted) return 'none'
      return this.message?.is_read ? 'seen' : 'delivered'
    },
    statusLabel() {
      if (this.deliveryState === 'seen') return 'Seen'
      if (this.deliveryState === 'delivered') return 'Delivered'
      return 'Sent'
    },
    statusClass() {
      if (this.deliveryState === 'seen') return 'text-emerald-200'
      if (this.deliveryState === 'delivered') return 'text-blue-100'
      return 'text-blue-100/80'
    },
    isDeleted() {
      return Boolean(this.message?.is_deleted)
    },
    hasText() {
      return Boolean(this.message?.content?.trim()) && !this.isDeleted && !this.isChatMessage
    },
    isEmojiOnlyMessage() {
      return this.hasText && this.isEmojiOnlyText && !this.hasMedia
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
    messageType() {
      return String(this.message?.message_type || 'text').toLowerCase()
    },
    isChatMessage() {
      return this.messageType === 'gif' || this.messageType === 'sticker'
    },
    isChatMediaMessage() {
      return this.isChatMessage && !this.isDeleted
    },
    chatMediaKindLabel() {
      return this.messageType === 'gif' ? 'GIF' : this.messageType === 'sticker' ? 'Sticker' : ''
    },
    chatMediaTitle() {
      if (!this.isChatMessage) return ''
      return this.message?.media_title || this.message?.provider_id || this.message?.providerId || this.chatMediaKindLabel
    },
    chatMediaSourceUrl() {
      if (this.messageType === 'gif') return this.message?.gif_url || this.message?.external_url || ''
      if (this.messageType === 'sticker') return this.message?.sticker_url || this.message?.external_url || ''
      return ''
    },
    chatMediaLabel() {
      return describeMediaItem({
        kind: this.messageType === 'gif' ? 'gif' : 'sticker',
        title: this.chatMediaTitle,
      })
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
      return Boolean(this.message?.can_edit) && !this.isChatMediaMessage
    },
    replyToMessage() {
      return this.message?.reply_to_message || null
    },
    cachedMediaUrl() {
      if (!this.hasMedia) return ''
      if (this._cachedMediaUrl) return this._cachedMediaUrl

      const raw = this.media?.media_url || this.media?.media || ''
      if (!raw) return ''
      this._cachedMediaUrl = buildMediaUrl(raw)
      return this._cachedMediaUrl
    },
  },
  methods: {
    replyPreviewText(message) {
      if (!message) return ''
      const type = String(message?.message_type || 'text').toLowerCase()
      if (type === 'gif' || type === 'sticker') {
        return describeMediaItem({
          kind: type,
          title: message?.media_title || message?.provider_id || type,
        })
      }
      return message.content || ''
    },
    onContextMenu(event) {
      if (this.isDeleted) return
      event.preventDefault()
      const offset = 12
      const menuWidth = 192
      const menuHeight = this.isMe ? 210 : 140
      const pane = this.$el?.closest?.('[data-chat-pane]') || document.documentElement
      const paneRect = pane.getBoundingClientRect?.()
      const leftBound = paneRect ? paneRect.left + offset : offset
      const topBound = paneRect ? paneRect.top + offset : offset
      const rightBound = paneRect ? paneRect.right - menuWidth - offset : window.innerWidth - menuWidth - offset
      const bottomBound = paneRect ? paneRect.bottom - menuHeight - offset : window.innerHeight - menuHeight - offset

      this.actionMenuX = Math.max(leftBound, Math.min(event.clientX + offset, rightBound))
      this.actionMenuY = Math.max(topBound, Math.min(event.clientY + offset, bottomBound))
      this.showActions = true
      this.showReactions = false
    },
    closeActions(event) {
      if (
        event &&
        ((this.$refs.actionMenu && this.$refs.actionMenu.contains(event.target)) ||
          (this.$refs.emojiPalette && this.$refs.emojiPalette.contains(event.target)) ||
          (this.$el && this.$el.contains(event.target)))
      ) {
        return
      }
      this.showActions = false
      this.showReactions = false
      this.showEmojiPalette = false
    },
    handleScroll() {
      if (this.showActions) this.showActions = false
    },
    onKeydown(event) {
      if (event.key === 'Escape') this.closeActions()
    },
    onPointerDown(event) {
      if (this.isDeleted) return
      this.pointerIsDown = true
      this.activePointerType = event.pointerType || ''
      if (this.activePointerType === 'mouse') return
      if (this.pressTimer) clearTimeout(this.pressTimer)
      this.pressTimer = window.setTimeout(() => {
        this.showReactions = true
        this.showActions = false
        if (navigator.vibrate) navigator.vibrate(12)
      }, 420)
    },
    onPointerUp() {
      this.pointerIsDown = false
      if (this.pressTimer) {
        clearTimeout(this.pressTimer)
        this.pressTimer = null
      }
    },
    onPointerCancel() {
      this.pointerIsDown = false
      if (this.pressTimer) {
        clearTimeout(this.pressTimer)
        this.pressTimer = null
      }
      this.wasScrolling = false
    },
    onPointerMove() {
      if (this.pointerIsDown) {
        this.wasScrolling = true
      }
    },
    handlePreviewKeydown(event) {
      if (event.key === 'Escape') this.closeImage()
    },
    isImage(message) {
      const mediaType = message?.media_type || ''
      if (mediaType.startsWith('image/')) return true
      const url = this.cachedMediaUrl.toLowerCase()
      return (
        url.endsWith('.jpg') ||
        url.endsWith('.jpeg') ||
        url.endsWith('.png') ||
        url.endsWith('.gif') ||
        url.endsWith('.webp')
      )
    },
    isVideo(message) {
      const mediaType = message?.media_type || ''
      if (mediaType.startsWith('video/')) return true
      const url = this.cachedMediaUrl.toLowerCase()
      return url.endsWith('.mp4') || url.endsWith('.webm') || url.endsWith('.ogg') || url.endsWith('.mov')
    },
    onMediaLoad() {
      this.mediaLoading = false
      this.mediaError = false
      this.$emit('media-load', { messageId: this.message.id })
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
      this.showEmojiPalette = false
      this.showActions = false
    },
    toggleReactions() {
      if (this.isDeleted) return
      this.showReactions = !this.showReactions
      this.showEmojiPalette = false
      if (this.showActions) this.showActions = false
    },
    toggleEmojiPalette() {
      if (this.isDeleted) return
      this.showEmojiPalette = !this.showEmojiPalette
      this.showReactions = true
      if (this.showActions) this.showActions = false
    },
    selectReactionFromPalette(emoji) {
      this.selectReaction(emoji)
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
        (this.isChatMediaMessage
          ? describeMediaItem({
              kind: this.messageType === 'gif' ? 'gif' : 'sticker',
              title: this.chatMediaTitle,
            })
          : this.message?.content?.trim()) ||
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
    document.addEventListener('scroll', this.handleScroll, true)
    document.addEventListener('wheel', this.handleScroll, { passive: true })
    document.addEventListener('touchmove', this.handleScroll, { passive: true })
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeActions)
    document.removeEventListener('keydown', this.onKeydown)
    document.removeEventListener('keydown', this.handlePreviewKeydown)
    document.removeEventListener('scroll', this.handleScroll, true)
    document.removeEventListener('wheel', this.handleScroll)
    document.removeEventListener('touchmove', this.handleScroll)
    if (this.pressTimer) clearTimeout(this.pressTimer)
  },
}
</script>

<style scoped>
.animated-message :deep(.animated-message__link),
.animated-message .animated-message__link {
  color: #2563eb;
}

.emoji-only-message {
  display: flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-width: 0;
  max-width: 100%;
}

.emoji-only-message__row {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.1rem;
  flex-wrap: wrap;
}

.emoji-only-message :deep(.animated-message) {
  line-height: 1;
}

.emoji-only-message :deep(.animated-emoji) {
  filter: drop-shadow(0 10px 26px rgba(59, 130, 246, 0.14));
}

.chat-media-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: fit-content;
  max-width: min(100%, 18rem);
}

.chat-media-message--me {
  margin-left: auto;
}

.chat-media-message--them {
  margin-right: auto;
}

.chat-media-message__frame {
  position: relative;
  overflow: hidden;
  border-radius: 1.4rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(241, 245, 249, 0.92));
  box-shadow:
    0 18px 40px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  padding: 0.55rem;
}

.chat-media-message__image {
  display: block;
  width: min(18rem, 100%);
  max-width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 1.05rem;
}

.chat-media-message__fallback {
  display: grid;
  place-items: center;
  width: 12rem;
  height: 12rem;
  border-radius: 1.05rem;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(226, 232, 240, 0.92));
}

.reaction-emoji {
  display: inline-block;
  font-family:
    'Apple Color Emoji',
    'Segoe UI Emoji',
    'Segoe UI Symbol',
    'Noto Color Emoji',
    sans-serif;
  font-variant-emoji: emoji;
  line-height: 1;
}

.reaction-emoji--small {
  font-size: 0.95rem;
}
</style>
