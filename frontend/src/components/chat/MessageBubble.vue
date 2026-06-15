<template>
  <div :class="['mb-3 flex w-full', isMe ? 'justify-end' : 'justify-start']" :data-message-id="message?.id"
    @dblclick="toggleReactions" @pointerdown="onPointerDown" @pointerup="onPointerUp" @pointercancel="onPointerCancel"
    @pointermove="onPointerMove" @contextmenu="onContextMenu">
    <div :class="[
      'message-bubble-shell flex min-w-0 flex-col gap-1.5',
      isMe ? 'message-bubble-shell--me items-end' : 'items-start',
      hasMedia ? 'message-bubble-shell--media' : 'message-bubble-shell--text',
      hasMedia && hasText ? 'message-bubble-shell--captioned' : '',
      isChatMediaMessage ? 'message-bubble-shell--chat-media' : '',
    ]">
      <div class="relative min-w-0 max-w-full">
        <!-- Reactions Popup -->
        <transition enter-active-class="transition duration-200 ease-out"
          enter-from-class="transform scale-95 opacity-0 translate-y-1"
          enter-to-class="transform scale-100 opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="transform scale-100 opacity-100 translate-y-0"
          leave-to-class="transform scale-95 opacity-0 translate-y-1">
          <div v-if="showReactions" ref="reactionsPopup"
            class="absolute bottom-full z-40 mb-1.5 inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-[#1e1e1e]/95 px-3 py-2 shadow-[0_18px_40px_rgba(0,0,0,0.28)] backdrop-blur-xl"
            :class="isMe ? 'right-0' : 'left-0'" @click.stop>
            <button v-for="emoji in quickEmojis" :key="emoji"
              class="flex h-8 w-8 items-center justify-center rounded-full text-xl transition-all duration-150 hover:scale-110 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/25"
              :class="myReaction === emoji ? 'bg-white/20 ring-2 ring-white/30' : ''" type="button"
              :aria-label="`React with ${emoji} emoji`" @click.stop="selectReaction(emoji)">
              <span class="reaction-emoji">{{ emoji }}</span>
            </button>
            <button
              class="flex h-8 w-8 items-center justify-center rounded-full text-[20px] font-medium leading-none text-white/90 transition-transform duration-150 hover:scale-110 hover:bg-white/10 active:scale-95 focus:outline-none focus:ring-2 focus:ring-white/25"
              type="button" aria-label="Open emoji palette" @click.stop="toggleEmojiPalette">
              +
            </button>
          </div>
        </transition>

        <!-- Reply Preview -->
        <div v-if="showReplyPreview"
          class="reply-preview-bubble mb-1.5 max-w-full overflow-hidden rounded-xl border text-xs shadow-sm"
          :class="isMe ? 'mr-2' : 'ml-2'">
          <div class="flex min-w-0 gap-2 px-2.5 py-2">
            <div class="h-auto w-1 flex-shrink-0 rounded-full"
              :class="replyToMessage.is_deleted ? 'bg-slate-300' : isMe ? 'bg-sky-500' : 'bg-violet-500'"></div>
            <div class="min-w-0 flex-1">
              <div class="truncate text-[11px] font-black"
                :class="replyToMessage.is_deleted ? 'text-slate-500' : isMe ? 'text-sky-700' : 'text-violet-700'">
                {{ replySenderName(replyToMessage) }}
              </div>
              <div class="reply-preview-text mt-0.5 line-clamp-2 text-[12px] font-medium leading-snug"
                :class="replyToMessage.is_deleted ? 'italic text-slate-400' : 'text-slate-600'">
                {{ replyPreviewText(replyToMessage) }}
              </div>
            </div>
            <div v-if="replyPreviewMedia(replyToMessage)"
              class="h-10 w-10 flex-shrink-0 overflow-hidden rounded-lg bg-slate-100 ring-1 ring-white/80">
              <img v-if="replyPreviewMedia(replyToMessage).kind !== 'video'"
                :src="replyPreviewMedia(replyToMessage).url" alt="" class="h-full w-full object-cover" />
              <video v-else :src="replyPreviewMedia(replyToMessage).url" class="h-full w-full object-cover" muted
                playsinline preload="metadata"></video>
            </div>
          </div>
        </div>

        <!-- Main Message Card -->
        <div data-message-card
          class="message-card relative min-w-0 max-w-full overflow-hidden rounded-2xl shadow-sm transition-all duration-200 group"
          :class="[
            isDeleted
              ? 'bg-slate-100/80 px-4 py-2.5 backdrop-blur-sm'
              : isEmojiOnlyMessage
                ? 'bg-transparent px-0 py-0 shadow-none overflow-visible'
                : isChatMediaMessage
                  ? 'message-card--chat-media bg-transparent px-0 py-0 shadow-none overflow-visible'
                  : hasMedia
                    ? 'message-card--media'
                    : 'px-4 py-2.5',
            hasMedia && hasText ? 'message-card--captioned-media' : '',
            hasMedia && !hasText ? 'message-card--media-only' : '',
            hasMedia && isMe ? 'message-card--me-media' : '',
            hasMedia && !isMe ? 'message-card--their-media' : '',
            hasMedia ? `message-card--media-${mediaOrientation}` : '',
            !hasMedia && !isMe && !isDeleted && !isEmojiOnlyMessage && !isChatMediaMessage ? 'message-card--their-text' : '',
            !isDeleted && !hasMedia && !isEmojiOnlyMessage && !isChatMediaMessage && !isMe
              ? ''
              : '',
            isMe && !isDeleted && !hasMedia && !isEmojiOnlyMessage && !isChatMediaMessage
              ? 'border border-sky-200/80 bg-sky-50 text-slate-900 shadow-sm shadow-sky-100/70'
              : 'text-slate-900',
            isMe && !isDeleted && !hasMedia && !isEmojiOnlyMessage && !isChatMediaMessage
              ? 'rounded-br-md'
              : 'rounded-bl-md',
          ]">
          <div v-if="isDeleted" class="flex items-center gap-2">
            <svg class="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path
                d="M12 9v4m0 4h.01M10.29 3.86l-8.1 14A2 2 0 004.1 21h15.8a2 2 0 001.91-2.14l-8.1-14a2 2 0 00-3.42 0z"
                stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span class="italic text-sm text-slate-500">{{ deletedMessageText }}</span>
          </div>

          <template v-else>
            <template v-if="isChatMediaMessage">
              <ChatMediaMessage :kind="messageType === 'gif' ? 'gif' : 'sticker'" :source-url="chatMediaSourceUrl"
                :title="chatMediaTitle" :label="chatMediaLabel" :animated="Boolean(message?.animated)" :compact="isMe"
                :show-meta="false" />
            </template>

            <!-- Media Content -->
            <div v-if="hasMedia" class="message-media-frame group/media" :class="[
              isVideo(media) ? 'message-media-frame--video' : 'message-media-frame--image',
              hasText ? 'message-media-frame--with-caption' : 'message-media-frame--solo',
              `message-media-frame--${mediaOrientation}`,
            ]">
              <div v-if="mediaLoading && (isImage(media) || isVideo(media))"
                class="absolute inset-0 z-10 flex items-center justify-center bg-white/80 backdrop-blur-sm">
                <div class="h-8 w-8 animate-spin rounded-full border-2 border-violet-400 border-t-transparent"></div>
              </div>

              <div v-if="mediaError" class="flex h-full w-full items-center justify-center bg-rose-50 p-6">
                <div class="text-center">
                  <svg class="mx-auto h-8 w-8 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p class="mt-1 text-xs text-rose-500">Failed to load</p>
                </div>
              </div>

              <img v-else-if="isImage(media)" v-show="!mediaLoading" :src="cachedMediaUrl" alt="Shared media"
                class="message-media-content cursor-pointer transition-transform hover:scale-105"
                @click="openMediaPreview('image', cachedMediaUrl)" @load="onMediaLoad" @error="onMediaError" />

              <video v-else-if="isVideo(media)" :src="cachedMediaUrl" controls class="message-media-content bg-black"
                @loadedmetadata="onMediaLoad" @error="onMediaError" />

              <!-- <button v-if="!mediaError && !mediaLoading && (isImage(media) || isVideo(media))"
                class="message-media-expand" type="button" aria-label="Open media full view"
                @click.stop="openMediaPreview(isVideo(media) ? 'video' : 'image', cachedMediaUrl)">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                  <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3m8 0h3a2 2 0 002-2v-3"
                    stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button> -->

              <a v-if="!isImage(media) && !isVideo(media) && !mediaError" :href="cachedMediaUrl" target="_blank"
                rel="noopener noreferrer"
                class="flex h-full w-full items-center gap-3 bg-slate-50 p-3 transition-colors hover:bg-slate-100">
                <svg class="h-8 w-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div class="flex-1">
                  <div class="text-sm font-medium text-slate-700">File attachment</div>
                  <div class="text-xs text-slate-500">Click to download</div>
                </div>
              </a>
            </div>

            <!-- Text Content -->
            <div v-if="hasText" :class="[
              'message-text text-sm leading-relaxed',
              hasMedia ? 'message-text--caption' : 'message-text--standalone',
              isEmojiOnlyMessage ? 'emoji-only-message' : '',
            ]">
              <template v-if="isEmojiOnlyMessage">
                <div class="emoji-only-message__row">
                  <AnimatedEmoji v-for="(emoji, index) in emojiOnlyEmojis" :key="`${emoji}-${index}`" :emoji="emoji"
                    :size="emojiOnlySize" :animated="true" />
                </div>
              </template>
              <template v-else>
                <AnimatedMessage :text="message.content" />
              </template>
            </div>

            <!-- Timestamp and Actions -->
            <div class="message-meta mt-1.5 flex items-center gap-1.5" :class="isMe ? 'justify-end' : 'justify-start'">
              <span class="text-[10px] font-semibold" :class="isMe ? 'text-slate-500' : 'text-slate-400'">
                {{ formattedTime }}
              </span>
              <span v-if="message.edited_at" class="text-[9px] font-medium"
                :class="isMe ? 'text-slate-500' : 'text-slate-400'">
                Edited
              </span>
              <span v-if="isMe && !isDeleted" class="message-delivery-ticks" :class="statusClass"
                :aria-label="statusLabel">
                <svg class="h-3.5 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path d="M2.8 13.3l4.3 4.3L16.8 7.9" stroke-linecap="round" stroke-linejoin="round" />
                  <path d="M8.1 13.3l4.3 4.3 8.8-9.7" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
            </div>
          </template>
        </div>

        <!-- Reactions Display -->
        <div v-if="!isDeleted && reactions.length > 0" class="mt-1 flex flex-wrap gap-1"
          :class="isMe ? 'justify-end' : 'justify-start'">
          <button v-for="reaction in visibleReactions" :key="reaction.emoji"
            class="flex cursor-pointer items-center gap-1 rounded-full border border-slate-200/80 bg-white/90 px-2 py-0.5 text-xs font-medium text-slate-600 shadow-sm backdrop-blur-sm transition-all hover:scale-105 hover:bg-white hover:shadow-md"
            :class="myReaction === reaction.emoji ? '!border-violet-300 !bg-violet-50 text-violet-700 ring-1 ring-violet-200' : ''"
            type="button" :aria-label="`React with ${reaction.emoji}`" @click.stop="selectReaction(reaction.emoji)">
            <span class="reaction-emoji reaction-emoji--small">{{ reaction.emoji }}</span>
            <span>{{ reaction.count }}</span>
          </button>
        </div>

      </div>
    </div>

    <!-- More Reactions Panel -->
    <teleport to="body">
      <transition enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 translate-y-2 scale-95" enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-120 ease-in" leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-2 scale-95">
        <div v-if="showEmojiPalette" ref="emojiPalette"
          class="fixed z-[260] h-[min(28rem,70vh)] w-[min(22rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-2xl shadow-slate-900/20"
          :style="emojiPaletteStyle" @click.stop>
          <EmojiPicker :open="showEmojiPalette" @select="selectReactionFromPalette" @close="showEmojiPalette = false" />
        </div>
      </transition>
    </teleport>

    <!-- Context Menu -->
    <teleport to="body">
      <transition enter-active-class="transition duration-150 ease-out" enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-120 ease-in"
        leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
        <div v-if="showActions" ref="actionMenu"
          class="fixed z-[120] w-56 overflow-hidden rounded-xl border border-violet-100/80 bg-white/95 py-1 shadow-xl shadow-violet-100/50 backdrop-blur-xl"
          :style="actionMenuStyle" role="menu" @click.stop>
          <button
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-violet-50"
            type="button" @click="emitReply">
            <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M3 10l7-7v4c8 0 11 5 11 13-3-5-7-6-11-6v4l-7-8z" stroke-linecap="round"
                stroke-linejoin="round" />
            </svg>
            Reply
          </button>

          <button v-if="canCopy"
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-violet-50"
            type="button" @click="copyMessage">
            <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M8 8h10v12H8z" stroke-linejoin="round" />
              <path d="M6 16H5a2 2 0 01-2-2V5a2 2 0 012-2h9a2 2 0 012 2v1" stroke-linecap="round"
                stroke-linejoin="round" />
            </svg>
            Copy
          </button>

          <div v-if="isMe && !isDeleted" class="my-1 border-t border-violet-100"></div>

          <button v-if="isMe && !isDeleted && canEdit"
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-violet-50"
            type="button" @click="emitEdit">
            <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M4 20h4l10-10a2.5 2.5 0 10-4-4L4 16v4z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Edit
          </button>

          <button v-if="isMe && !isDeleted"
            class="flex w-full items-center gap-3 px-4 py-2.5 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50"
            type="button" @click="emitDelete">
            <svg class="h-4 w-4 text-rose-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M6 7h12M9 7V5h6v2m-8 0l1 14h6l1-14" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Delete
          </button>
        </div>
      </transition>
    </teleport>

    <teleport to="body">
      <!-- Media Preview Modal -->
      <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100"
        leave-to-class="opacity-0">
        <div v-if="showImagePreview"
          class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/90 p-4 backdrop-blur-md"
          @click.self="closeMediaPreview" @keydown.escape="closeMediaPreview">
          <div class="media-preview-shell">
            <img v-if="previewType === 'image'" :src="previewUrl" alt="Full screen preview"
              class="media-preview-content" />
            <div v-else-if="previewType === 'video'" class="media-preview-video">
              <video ref="previewVideo" :src="previewUrl" class="media-preview-content bg-black" autoplay playsinline
                @click="togglePreviewVideo" @loadedmetadata="onPreviewVideoLoaded"
                @timeupdate="onPreviewVideoTimeUpdate" @play="previewVideoPaused = false"
                @pause="previewVideoPaused = true" @ended="previewVideoPaused = true" />
            </div>
            <button class="media-preview-close" type="button" aria-label="Close media full view"
              @click.stop="closeMediaPreview">
              ×
            </button>
          </div>
        </div>
      </transition>
    </teleport>
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
    currentUserId: {
      type: [Number, String],
      default: '',
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
      previewType: 'image',
      previewVideoPaused: true,
      previewVideoCurrentTime: 0,
      previewVideoDuration: 0,
      mediaOrientation: 'landscape',
      showActions: false,
      showEmojiPalette: false,
      actionMenuX: 0,
      actionMenuY: 0,
      emojiPaletteX: 12,
      emojiPaletteY: 12,
      mediaLoading: true,
      mediaError: false,
      _cachedTimestamp: null,
      _cachedFormattedTime: null,
      _cachedMediaUrl: null,
      _previousBodyOverflow: '',
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
      const firstReactions = this.reactions.slice(0, 2)
      if (!this.myReaction || firstReactions.some((reaction) => reaction.emoji === this.myReaction)) {
        return firstReactions
      }
      const selectedReaction = this.reactions.find((reaction) => reaction.emoji === this.myReaction)
      if (!selectedReaction) return firstReactions
      return firstReactions.length >= 2
        ? [firstReactions[0], selectedReaction]
        : [...firstReactions, selectedReaction]
    },
    myReaction() {
      return String(this.message?.my_reaction || '').trim()
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
      if (this.deliveryState === 'seen') return 'text-sky-500'
      if (this.deliveryState === 'delivered') return 'text-slate-400'
      return 'text-slate-400'
    },
    isDeleted() {
      return Boolean(this.message?.is_deleted)
    },
    deletedMessageText() {
      return this.isMe ? 'You deleted this message' : 'This message was deleted'
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
    formattedPreviewVideoTime() {
      return `${this.formatVideoTime(this.previewVideoCurrentTime)} / ${this.formatVideoTime(this.previewVideoDuration)}`
    },
    actionMenuStyle() {
      return {
        left: `${this.actionMenuX}px`,
        top: `${this.actionMenuY}px`,
      }
    },
    emojiPaletteStyle() {
      return {
        left: `${this.emojiPaletteX}px`,
        top: `${this.emojiPaletteY}px`,
      }
    },
    canEdit() {
      if (this.isChatMediaMessage) return false
      return Boolean(this.message?.can_edit) || this.hasEditableMediaCaption
    },
    isVisualMediaMessage() {
      return this.hasMedia && (this.isImage(this.media) || this.isVideo(this.media))
    },
    hasEditableMediaCaption() {
      return this.isMe && this.isVisualMediaMessage && Boolean(this.message?.content?.trim())
    },
    copyableText() {
      if (this.isChatMediaMessage) return ''
      return this.message?.content?.trim() || ''
    },
    canCopy() {
      return Boolean(this.copyableText)
    },
    replyToMessage() {
      return this.message?.reply_to_message || null
    },
    showReplyPreview() {
      return Boolean(this.replyToMessage) && !this.isDeleted
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
  watch: {
    'message.id'() {
      this.mediaOrientation = 'landscape'
      this.mediaLoading = true
      this.mediaError = false
      this._cachedMediaUrl = null
    },
    cachedMediaUrl() {
      this.mediaOrientation = 'landscape'
      this.mediaLoading = true
      this.mediaError = false
    },
  },
  methods: {
    replyPreviewText(message) {
      if (!message) return ''
      if (message.is_deleted) return 'Message deleted'
      const type = String(message?.message_type || message?.type || 'text').toLowerCase()
      if (type === 'gif') return 'GIF'
      if (type === 'sticker') return 'Sticker'
      if (message.content?.trim()) return message.content.trim()
      const media = this.replyPreviewMedia(message)
      if (media?.kind === 'video') return 'Video'
      if (media?.kind === 'image') return 'Photo'
      return ''
    },
    replyPreviewMedia(message) {
      if (!message || message.is_deleted) return null
      const type = String(message?.message_type || message?.type || 'text').toLowerCase()
      const mediaType = String(message?.media_type || '').toLowerCase()
      const preview = message?.media_preview || message?.preview || message?.last_message_preview || null
      const raw =
        type === 'gif'
          ? message?.gif_url || message?.external_url || preview?.url || ''
          : type === 'sticker'
            ? message?.sticker_url || message?.external_url || preview?.url || ''
            : message?.media_url || message?.media || preview?.url || ''
      const url = buildMediaUrl(raw || '')
      if (!url) return null
      if (type === 'gif') return { kind: 'gif', url }
      if (type === 'sticker') return { kind: 'sticker', url }
      const isVideo =
        preview?.kind === 'video' ||
        mediaType.startsWith('video/') ||
        /\.(mp4|webm|ogg|mov)(\?|#|$)/i.test(String(url))
      return { kind: isVideo ? 'video' : 'image', url }
    },
    replySenderName(message) {
      if (!message) return 'Message'
      if (String(message.sender_id ?? '') === String(this.currentUserId ?? '')) return 'You'
      return message.sender_display_name || message.sender_username || 'Message'
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
          (this.$refs.reactionsPopup && this.$refs.reactionsPopup.contains(event.target)))
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
    onMediaLoad(event) {
      const target = event?.target
      const width = target?.naturalWidth || target?.videoWidth || 0
      const height = target?.naturalHeight || target?.videoHeight || 0
      if (width > 0 && height > 0) {
        const ratio = width / height
        if (ratio > 1.15) {
          this.mediaOrientation = 'landscape'
        } else if (ratio < 0.86) {
          this.mediaOrientation = 'portrait'
        } else {
          this.mediaOrientation = 'square'
        }
      }
      this.mediaLoading = false
      this.mediaError = false
      this.$emit('media-load', { messageId: this.message.id })
    },
    onMediaError() {
      this.mediaLoading = false
      this.mediaError = true
      this.$emit('media-error', { messageId: this.message.id })
    },
    formatVideoTime(seconds) {
      const totalSeconds = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0
      const minutes = Math.floor(totalSeconds / 60)
      const remainingSeconds = totalSeconds % 60
      return `${minutes}:${String(remainingSeconds).padStart(2, '0')}`
    },
    onPreviewVideoLoaded(event) {
      this.previewVideoDuration = event.target?.duration || 0
      this.previewVideoCurrentTime = event.target?.currentTime || 0
      this.previewVideoPaused = Boolean(event.target?.paused)
    },
    onPreviewVideoTimeUpdate(event) {
      this.previewVideoCurrentTime = event.target?.currentTime || 0
    },
    togglePreviewVideo() {
      const video = this.$refs.previewVideo
      if (!video) return
      if (video.paused) {
        video.play?.()
      } else {
        video.pause?.()
      }
    },
    seekPreviewVideo(event) {
      const video = this.$refs.previewVideo
      const nextTime = Number(event.target?.value || 0)
      this.previewVideoCurrentTime = nextTime
      if (video) video.currentTime = nextTime
    },
    openImage(url) {
      this.openMediaPreview('image', url)
    },
    openMediaPreview(type, url) {
      if (!url) return
      this.previewUrl = url
      this.previewType = type === 'video' ? 'video' : 'image'
      this.previewVideoPaused = this.previewType === 'video'
      this.previewVideoCurrentTime = 0
      this.previewVideoDuration = 0
      this._previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      document.activeElement?.blur?.()
      this.showImagePreview = true
      document.addEventListener('keydown', this.handlePreviewKeydown)
    },
    closeImage() {
      this.closeMediaPreview()
    },
    closeMediaPreview() {
      this.$refs.previewVideo?.pause?.()
      this.showImagePreview = false
      this.previewUrl = ''
      this.previewType = 'image'
      this.previewVideoPaused = true
      this.previewVideoCurrentTime = 0
      this.previewVideoDuration = 0
      document.body.style.overflow = this._previousBodyOverflow || ''
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
      if (!this.showEmojiPalette) {
        this.positionEmojiPalette()
        this.showEmojiPalette = true
      } else {
        this.showEmojiPalette = false
      }
      this.showReactions = true
      if (this.showActions) this.showActions = false
    },
    positionEmojiPalette() {
      const bubble = this.$el?.querySelector?.('[data-message-card]') || this.$el
      const rect = bubble?.getBoundingClientRect?.()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight
      const panelWidth = Math.min(352, viewportWidth - 24)
      const panelHeight = Math.min(448, Math.round(viewportHeight * 0.7))
      const gutter = 12

      if (!rect) {
        this.emojiPaletteX = gutter
        this.emojiPaletteY = gutter
        return
      }

      const preferredLeft = this.isMe ? rect.right - panelWidth : rect.left
      const left = Math.max(gutter, Math.min(preferredLeft, viewportWidth - panelWidth - gutter))
      const aboveTop = rect.top - panelHeight - gutter
      const belowTop = rect.bottom + gutter
      const top =
        aboveTop >= gutter
          ? aboveTop
          : Math.min(belowTop, viewportHeight - panelHeight - gutter)

      this.emojiPaletteX = left
      this.emojiPaletteY = Math.max(gutter, top)
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
      const text = this.copyableText
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
    if (this.showImagePreview) {
      document.body.style.overflow = this._previousBodyOverflow || ''
    }
    if (this.pressTimer) clearTimeout(this.pressTimer)
  },
}
</script>

<style scoped>
.animated-message :deep(.animated-message__link),
.animated-message .animated-message__link {
  color: #7c3aed;
}

.message-bubble-shell {
  width: fit-content;
  max-width: min(78%, 40rem);
}

.message-bubble-shell--media {
  max-width: min(84%, 28rem);
}

.message-bubble-shell--captioned {
  width: fit-content;
  max-width: calc(100% - 0.25rem);
}

.message-bubble-shell--chat-media {
  width: fit-content;
  max-width: min(76%, 18rem);
}

.message-card {
  width: 100%;
  overflow-wrap: anywhere;
}

.message-card--their-text {
  border: 1px solid rgba(221, 214, 254, 0.88);
  background:
    linear-gradient(180deg, rgba(250, 245, 255, 0.98), rgba(245, 243, 255, 0.94));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.78),
    0 1px 1px rgba(76, 29, 149, 0.03),
    0 10px 24px rgba(109, 40, 217, 0.08);
  backdrop-filter: blur(12px);
}

.reply-preview-bubble {
  border-color: rgba(221, 214, 254, 0.78);
  background:
    linear-gradient(135deg, rgba(250, 245, 255, 0.96), rgba(245, 243, 255, 0.9));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.74),
    0 8px 18px rgba(109, 40, 217, 0.06);
}

.message-bubble-shell--me .reply-preview-bubble {
  border-color: rgba(125, 211, 252, 0.52);
  background:
    linear-gradient(135deg, rgba(240, 249, 255, 0.98), rgba(224, 242, 254, 0.9));
}

.message-card--chat-media {
  width: fit-content;
  max-width: 100%;
}

.message-card--media {
  width: fit-content;
  max-width: 100%;
  padding: 0.25rem;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    0 1px 1px rgba(15, 23, 42, 0.04),
    0 8px 22px rgba(15, 23, 42, 0.07);
  backdrop-filter: blur(10px);
}

.message-card--me-media {
  border-color: rgba(125, 211, 252, 0.72);
  background: linear-gradient(180deg, rgba(240, 249, 255, 0.98), rgba(224, 242, 254, 0.92));
  box-shadow:
    0 1px 1px rgba(14, 165, 233, 0.05),
    0 8px 22px rgba(14, 165, 233, 0.09);
}

.message-card--their-media {
  border-color: rgba(221, 214, 254, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 243, 255, 0.9));
}

.message-card--captioned-media {
  width: fit-content;
  max-width: 100%;
  padding-bottom: 0.35rem;
}

.message-card--media-only {
  width: fit-content;
}

.message-card--media-landscape {
  width: fit-content;
}

.message-card--media-portrait {
  width: fit-content;
}

.message-card--media-square {
  width: fit-content;
}

.message-card--media-landscape .message-text--caption {
  max-width: clamp(13rem, 42vw, 22rem);
}

.message-card--media-portrait .message-text--caption {
  max-width: clamp(9.5rem, 28vw, 14rem);
}

.message-card--media-square .message-text--caption {
  max-width: clamp(11rem, 34vw, 17rem);
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

.message-text,
.message-text :deep(.animated-message),
.reply-preview-text {
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.message-text--standalone {
  white-space: pre-wrap;
}

.message-text--caption {
  width: 100%;
  padding: 0.45rem 0.45rem 0.05rem;
  color: #1e293b;
  font-size: 0.9rem;
  line-height: 1.45;
  white-space: pre-wrap;
}

.message-card--me-media .message-text--caption {
  color: #0f172a;
}

.message-meta {
  clear: both;
  min-height: 1rem;
  line-height: 1;
  white-space: nowrap;
}

.message-card--media .message-meta {
  margin-top: 0.25rem;
  padding-inline: 0.35rem;
}

.message-card--captioned-media .message-meta {
  padding-inline: 0.45rem;
}

.message-delivery-ticks {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.message-delivery-ticks svg {
  display: block;
  stroke-width: 2.35;
}

.message-media-frame {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: clamp(13rem, 42vw, 22rem);
  max-width: 100%;
  min-height: clamp(10rem, 24vw, 16rem);
  max-height: min(52vh, 28rem);
  aspect-ratio: 4 / 3;
  border-radius: 0.82rem;
  background: #e5e7eb;
  box-shadow: none;
}

.message-media-frame--with-caption {
  width: 100%;
  min-height: clamp(10.5rem, 26vw, 17rem);
}

.message-media-frame--landscape {
  width: clamp(13rem, 42vw, 22rem);
  min-height: auto;
  aspect-ratio: 16 / 10;
}

.message-media-frame--portrait {
  width: clamp(9.5rem, 28vw, 14rem);
  min-height: auto;
  aspect-ratio: 3 / 4;
}

.message-media-frame--square {
  width: clamp(11rem, 34vw, 17rem);
  min-height: auto;
  aspect-ratio: 1 / 1;
}

.message-media-frame--image {
  background:
    linear-gradient(135deg, rgba(248, 250, 252, 0.95), rgba(226, 232, 240, 0.82));
}

.message-media-frame--video {
  width: clamp(14rem, 46vw, 24rem);
  min-height: clamp(8rem, 22vw, 14rem);
  aspect-ratio: 16 / 9;
  background: #000;
}

.message-media-frame--video.message-media-frame--portrait {
  width: clamp(9rem, 26vw, 13rem);
  aspect-ratio: 9 / 16;
}

.message-media-frame--video.message-media-frame--square {
  width: clamp(10.5rem, 32vw, 16rem);
  aspect-ratio: 1 / 1;
}

.message-media-content {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: inherit;
}

.message-media-frame--image .message-media-content {
  background: #f8fafc;
  object-fit: cover;
}

.message-media-frame--video .message-media-content {
  background: #000;
}

.message-media-expand {
  position: absolute;
  right: 0.65rem;
  top: 0.65rem;
  display: grid;
  height: 2rem;
  width: 2rem;
  place-items: center;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.58);
  color: #fff;
  opacity: 0.92;
  transition:
    opacity 0.18s ease,
    background 0.18s ease,
    transform 0.18s ease;
}

.message-media-expand:hover {
  opacity: 1;
  background: rgba(15, 23, 42, 0.78);
  transform: scale(1.04);
}

.media-preview-shell {
  position: relative;
  display: flex;
  max-height: calc(100dvh - 2rem);
  max-width: calc(100vw - 2rem);
  align-items: center;
  justify-content: center;
}

.media-preview-video {
  position: relative;
  display: flex;
  max-height: calc(100dvh - 2rem);
  max-width: calc(100vw - 2rem);
  align-items: center;
  justify-content: center;
}

.media-preview-content {
  display: block;
  width: auto;
  height: auto;
  max-height: calc(100dvh - 2rem);
  max-width: calc(100vw - 2rem);
  border-radius: 1rem;
  object-fit: contain;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.42);
}

.media-preview-video .media-preview-content {
  max-height: calc(100dvh - 6rem);
}

.media-preview-close {
  position: fixed;
  right: max(1rem, env(safe-area-inset-right));
  top: max(1rem, env(safe-area-inset-top));
  z-index: 110;
  display: grid;
  height: 2.75rem;
  width: 2.75rem;
  place-items: center;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.86);
  color: transparent;
  font-size: 0;
  box-shadow: 0 12px 34px rgba(0, 0, 0, 0.35);
  transition:
    background 0.18s ease,
    transform 0.18s ease;
}

.media-preview-close::before {
  content: '\00d7';
  color: rgba(255, 255, 255, 0.92);
  font-size: 1.75rem;
  line-height: 1;
}

.media-preview-close:hover {
  background: rgba(15, 23, 42, 0.92);
  transform: scale(1.04);
}

@media (max-width: 480px) {
  .message-bubble-shell {
    max-width: 100%;
  }

  .message-bubble-shell--media,
  .message-bubble-shell--captioned {
    width: min(100%, 22rem);
    max-width: 100%;
  }

  .message-bubble-shell--chat-media {
    width: fit-content;
    max-width: calc(100% - 0.25rem);
  }

  .message-card--media {
    padding: 0.25rem;
    border-radius: 1rem;
  }

  .message-text--caption {
    padding: 0.45rem 0.45rem 0.1rem;
    font-size: 0.875rem;
    line-height: 1.45;
  }

  .message-media-frame,
  .message-media-frame--video {
    width: 100%;
    min-height: clamp(9rem, 48vw, 13rem);
    max-height: 48vh;
    border-radius: 0.75rem;
  }

  .message-media-frame--video {
    min-height: clamp(8rem, 52vw, 12rem);
  }

  .message-media-frame--landscape {
    width: min(100%, 20rem);
    min-height: auto;
    aspect-ratio: 16 / 10;
  }

  .message-media-frame--portrait,
  .message-media-frame--video.message-media-frame--portrait {
    width: min(64vw, 12.5rem);
    min-height: auto;
  }

  .message-media-frame--portrait {
    aspect-ratio: 3 / 4;
  }

  .message-media-frame--video.message-media-frame--portrait {
    aspect-ratio: 9 / 16;
  }

  .message-media-frame--square,
  .message-media-frame--video.message-media-frame--square {
    width: min(72vw, 15rem);
    min-height: auto;
    aspect-ratio: 1 / 1;
  }

  .message-card--media-landscape .message-text--caption {
    max-width: min(100%, 20rem);
  }

  .message-card--media-portrait .message-text--caption {
    max-width: min(64vw, 12.5rem);
  }

  .message-card--media-square .message-text--caption {
    max-width: min(72vw, 15rem);
  }

  .media-preview-shell,
  .media-preview-video {
    max-height: calc(100dvh - 1rem);
    max-width: calc(100vw - 1rem);
  }

  .media-preview-content {
    max-height: calc(100dvh - 1rem);
    max-width: calc(100vw - 1rem);
    border-radius: 0.75rem;
  }

  .media-preview-video .media-preview-content {
    max-height: calc(100dvh - 5.5rem);
  }

  .media-preview-close {
    right: max(0.75rem, env(safe-area-inset-right));
    top: max(0.75rem, env(safe-area-inset-top));
  }

}

@media (min-width: 481px) and (max-width: 768px) {
  .message-bubble-shell {
    max-width: min(88%, 34rem);
  }

  .message-bubble-shell--media,
  .message-bubble-shell--captioned {
    max-width: min(88%, 28rem);
  }

  .message-media-frame {
    width: clamp(16rem, 58vw, 24rem);
    max-height: 52vh;
  }

  .message-media-frame--with-caption,
  .message-media-frame--video.message-media-frame--with-caption {
    width: 100%;
  }
}

@media (min-width: 769px) and (max-width: 1180px) {
  .message-bubble-shell {
    max-width: min(80%, 40rem);
  }

  .message-bubble-shell--media,
  .message-bubble-shell--captioned {
    max-width: min(84%, 30rem);
  }
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
