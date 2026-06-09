<template>
  <section class="relative h-full min-h-0 flex-1 overflow-hidden">
    <!-- Dynamic Ambient Background -->
    <div
      class="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-gradient-to-br from-slate-50 via-white to-purple-50/30"
    >
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(139,92,246,0.08),transparent_24%),radial-gradient(circle_at_top_right,rgba(20,184,166,0.06),transparent_26%),radial-gradient(circle_at_bottom_left,rgba(139,92,246,0.04),transparent_22%)]"
      ></div>
      <div
        class="absolute -left-24 top-24 h-96 w-96 rounded-full bg-purple-400/10 blur-[120px]"
      ></div>
      <div
        class="absolute right-10 top-40 h-80 w-80 rounded-full bg-teal-400/10 blur-[120px]"
      ></div>
      <div
        class="absolute bottom-20 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-purple-400/5 blur-[100px]"
      ></div>
    </div>

    <!-- Empty/No Selection State -->
    <div
      v-if="!user"
      class="flex h-full min-h-0 w-full min-w-0 flex-col items-center justify-center gap-6 rounded-[1.75rem] border border-white/70 bg-white/90 p-6 text-center shadow-[0_20px_60px_rgba(139,92,246,0.08)] backdrop-blur-2xl sm:rounded-[2.5rem] sm:p-8 lg:p-10"
    >
      <div class="relative">
        <div
          class="absolute -inset-8 rounded-full bg-gradient-to-r from-purple-100 via-purple-100 to-teal-100 blur-2xl"
        ></div>
        <div
          class="relative grid h-24 w-24 place-items-center rounded-[1.75rem] bg-purple-500 shadow-xl shadow-purple-200 transition-all duration-300 hover:scale-105 hover:shadow-purple-300"
        >
          <svg
            class="h-10 w-10 text-white"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
      </div>
      <div class="space-y-2">
        <h3 class="text-2xl font-bold tracking-tight text-slate-800">Your conversations</h3>
        <p class="mx-auto max-w-xs text-sm text-slate-500">
          Select a connection to get started ...
        </p>
        <div class="flex justify-center gap-2 pt-4">
          <div class="h-1.5 w-8 rounded-full bg-purple-500"></div>
          <div class="h-1.5 w-3 rounded-full bg-purple-200"></div>
          <div class="h-1.5 w-2 rounded-full bg-purple-100"></div>
        </div>
      </div>
    </div>

    <!-- Active Chat Window -->
    <div
      v-else
      data-chat-pane
      class="relative flex h-full min-h-0 w-full min-w-0 flex-col overflow-hidden rounded-[1.75rem] border border-white/70 bg-white/90 shadow-[0_20px_60px_rgba(139,92,246,0.08)] backdrop-blur-2xl sm:rounded-[2.5rem]"
    >
      <!-- Chat Header -->
      <div
        class="relative z-10 flex items-center justify-between gap-3 border-b border-slate-200/50 bg-white/70 px-4 py-4 backdrop-blur-xl sm:px-5 lg:px-6"
      >
        <div class="flex min-w-0 items-center gap-3 sm:gap-4">
          <button
            v-if="showMobileBack"
            type="button"
            class="grid h-10 w-10 flex-shrink-0 place-items-center rounded-xl bg-slate-100/70 text-slate-600 transition-all duration-200 hover:bg-white hover:text-purple-600 hover:shadow-md active:scale-95 lg:hidden"
            @click="handleBackToList"
            aria-label="Back to conversations"
          >
            <svg
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              viewBox="0 0 24 24"
            >
              <path d="M15 19l-7-7 7-7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <div class="relative group">
            <StableAvatar
              :src="chatAvatarUrl"
              :alt="`${user.username || 'user'} avatar`"
              class="h-12 w-12 rounded-xl object-cover shadow-md shadow-purple-200 transition-all duration-300 group-hover:shadow-lg group-hover:shadow-purple-300"
            />
            <div
              v-if="isSelectedUserOnline"
              class="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-white bg-emerald-500 shadow-sm"
            ></div>
          </div>
          <div>
            <div class="text-lg font-bold tracking-tight text-slate-800">{{ user.username }}</div>
            <div class="flex items-center gap-1.5 text-xs font-medium" :class="userPresenceClass">
              <!-- <span class="h-1.5 w-1.5 rounded-full" :class="userPresenceDotClass"></span> -->
              <span>{{ userPresenceLabel }}</span>
              <span
                v-if="unreadInThreadCount > 0"
                class="ml-1 rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-bold leading-none text-white shadow-sm"
              >
                {{ unreadInThreadCount > 99 ? '99+' : unreadInThreadCount }} unread
              </span>
            </div>
          </div>
        </div>

        <!-- Header Actions -->
        <div class="flex gap-1">
          <button
            class="group grid h-10 w-10 place-items-center rounded-xl bg-slate-100/60 text-slate-500 transition-all duration-200 hover:bg-white hover:text-purple-600 hover:shadow-md active:scale-95"
          >
            <svg
              class="h-5 w-5 transition-transform duration-200 group-hover:scale-110"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Messages Area -->
      <div
        ref="messageList"
        class="message-area relative flex-1 overflow-y-auto px-5 py-5 lg:px-6"
        style="overflow-anchor: none"
        @scroll="onScroll"
        @wheel="markManualHistoryScroll"
        @touchstart="markManualHistoryScroll"
        @pointerdown="markManualHistoryScroll"
      >
        <div
          class="pointer-events-none absolute inset-0 opacity-[0.02]"
          style="
            background-image: radial-gradient(#8b5cf6 1px, transparent 1px);
            background-size: 24px 24px;
          "
        ></div>
        <div class="relative z-10 flex flex-col gap-3">
          <div class="flex flex-col gap-2">
            <template v-for="item in groupedMessages" :key="item.key">
              <div v-if="item.type === 'date'" class="flex justify-center py-2">
                <span
                  class="rounded-full border border-slate-200/70 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500 shadow-sm backdrop-blur-sm"
                >
                  {{ item.label }}
                </span>
              </div>
              <div
                v-else-if="item.type === 'unread-divider'"
                data-unread-divider
                class="relative z-20 flex items-center gap-4 py-5"
              >
                <div
                  class="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300/70 to-transparent"
                ></div>
                <span
                  class="rounded-full bg-slate-900 px-4 py-2 text-[12px] font-semibold leading-none text-white shadow-[0_10px_24px_rgba(15,23,42,0.28)] ring-1 ring-black/10 backdrop-blur-md"
                >
                  {{ item.label }}
                </span>
                <div
                  class="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300/70 to-transparent"
                ></div>
              </div>
              <MessageBubble
                v-else
                v-memo="[
                  item.message.id,
                  item.message.timestamp,
                  item.message.is_read,
                  item.message.is_deleted,
                  item.message.edited_at,
                  item.message.reactions?.length,
                ]"
                :message="item.message"
                :isMe="String(getMessageSenderId(item.message)) === String(currentUserId)"
                @react="sendReaction"
                @reply="beginReplyMessage"
                @edit="beginEditMessage"
                @delete="deleteMessage"
                @media-load="handleMessageMediaLoad"
                @media-error="handleMessageMediaError"
                @open-reaction-picker="openReactionPicker"
              />
            </template>
          </div>

          <div
            v-if="!messages.length"
            class="flex flex-col items-center justify-center gap-4 py-20 opacity-70"
          >
            <div class="text-5xl">💬</div>
            <div class="space-y-1 text-center">
              <p class="text-sm font-bold uppercase tracking-wide text-slate-500">
                Start the conversation here
              </p>
              <p class="text-xs text-slate-400">Say hello to {{ user.username }}</p>
            </div>
          </div>
        </div>
      </div>

      <FloatingEmojiLayer ref="emojiLayer" />

      <!-- Floating Scroll Button -->
      <transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="translate-y-10 opacity-0 scale-90"
        enter-to-class="translate-y-0 opacity-100 scale-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="translate-y-0 opacity-100 scale-100"
        leave-to-class="translate-y-10 opacity-0 scale-90"
      >
        <button
          v-if="showScrollDown"
          class="absolute bottom-24 right-4 z-30 grid h-11 w-11 place-items-center rounded-xl bg-white text-purple-600 shadow-lg ring-1 ring-slate-200 transition-all duration-200 hover:-translate-y-0.5 hover:bg-purple-600 hover:text-white hover:shadow-purple-200 active:scale-95 sm:bottom-28 sm:right-6"
          type="button"
          @click="scrollToBottom(true)"
        >
          <svg
            class="h-5 w-5 transition-transform duration-200"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            viewBox="0 0 24 24"
          >
            <path d="M19 14l-7 7m0 0l-7-7m7 7V3" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </transition>

      <!-- Error Toast -->
      <transition name="toast">
        <div
          v-if="sendError"
          class="absolute bottom-24 left-4 right-4 z-40 rounded-xl bg-rose-500 p-4 text-sm font-semibold text-white shadow-xl shadow-rose-200/50 backdrop-blur-sm sm:bottom-28 sm:left-6 sm:right-6"
        >
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <svg
                class="h-5 w-5"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                viewBox="0 0 24 24"
              >
                <path
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <span>{{ sendError }}</span>
            </div>
            <button
              @click="sendError = ''"
              class="rounded-lg p-1 transition-colors hover:bg-white/20"
            >
              ✕
            </button>
          </div>
        </div>
      </transition>

      <!-- Input Area -->
      <div
        class="relative z-10 border-t border-slate-200/60 bg-white/55 px-4 py-4 backdrop-blur-md sm:px-5 lg:px-6"
      >
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="translate-y-1 opacity-0"
          enter-to-class="translate-y-0 opacity-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="translate-y-0 opacity-100"
          leave-to-class="translate-y-1 opacity-0"
        >
          <div
            v-if="isPartnerTyping"
            class="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200/80 bg-white/90 px-3 py-2 text-xs font-semibold text-slate-500 shadow-sm backdrop-blur-md"
          >
            <span class="flex items-center gap-1">
              <span class="typing-dot"></span>
              <span class="typing-dot typing-dot-delay-1"></span>
              <span class="typing-dot typing-dot-delay-2"></span>
            </span>
            <span>{{ user.username }} is typing</span>
          </div>
        </transition>
        <MessageInput
          v-if="user"
          ref="messageInput"
          :disabled="!user"
          :draft-text="draftText"
          :editing-message="editingMessage"
          :replying-message="replyingMessage"
          @send="sendMessage"
          @cancel-edit="cancelEditMessage"
          @cancel-reply="cancelReplyMessage"
          @draft-change="updateDraftText"
          @typing="handleTyping"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Toast animations */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.toast-enter-from {
  transform: translateY(20px) scale(0.9);
  opacity: 0;
}

.toast-enter-to {
  transform: translateY(0) scale(1);
  opacity: 1;
}

.toast-leave-from {
  transform: translateY(0) scale(1);
  opacity: 1;
}

.toast-leave-to {
  transform: translateY(20px) scale(0.9);
  opacity: 0;
}

/* Custom scrollbar styles */
.message-area {
  scrollbar-width: thin;
  scrollbar-color: rgba(139, 92, 246, 0.3) transparent;
}

.message-area::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}

.message-area::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 10px;
}

.message-area::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 10px;
  transition: background 0.2s;
}

.message-area::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}

/* Smooth scrolling */
.message-area {
  scroll-behavior: smooth;
}

.typing-dot {
  display: inline-block;
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 9999px;
  background: rgb(148 163 184);
  animation: typingPulse 1.2s infinite ease-in-out;
}

.typing-dot-delay-1 {
  animation-delay: 0.15s;
}

.typing-dot-delay-2 {
  animation-delay: 0.3s;
}

@keyframes typingPulse {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.45;
  }

  40% {
    transform: translateY(-2px);
    opacity: 1;
  }
}
</style>

<script>
import chatApi from '@/services/messageApi'
import MessageInput from './MessageInput.vue'
import MessageBubble from './MessageBubble.vue'
import FloatingEmojiLayer from './FloatingEmojiLayer.vue'
import StableAvatar from './StableAvatar.vue'
import { mapState } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { mapActions } from 'pinia'
import { useProfileStore } from '@/stores/profile'
import { getAvatarUrl } from '@/utils/avatars'
import eventBus from '@/services/eventBus'
import {
  getConversationMessages,
  markConversationAsRead,
  sendConversationMessage,
} from '@/services/messagingCompat'
import { isCelebrationEmoji } from './emoji-catalog'
import { getEmojiCount, isEmojiOnlyMessage, tokenizeMessageText } from './emoji-parser'

export default {
  props: {
    user: {
      type: Object,
      default: null,
    },
    showMobileBack: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['back'],
  components: {
    MessageBubble,
    MessageInput,
    FloatingEmojiLayer,
    StableAvatar,
  },
  data() {
    return {
      messages: [],
      loading: false,
      sendError: '',
      pollTimer: null,
      readSyncTimer: null,
      readSyncInFlight: false,
      ws: null,
      wsConnected: false,
      showScrollDown: false,
      totalCount: 0,
      hasMore: false,
      loadingMore: false,
      loadOffset: 0,
      editingMessage: null,
      replyingMessage: null,
      revealUnreadOnLoad: false,
      unreadDividerSnapshot: null,
      isPartnerTyping: false,
      typingIndicatorTimer: null,
      isLocallyTyping: false,
      typingSendTimer: null,
      draftsByConversation: {},
      stickToBottom: true,
      suppressLoadMoreUntil: 0,
      initialScrollDone: false,
      canLoadOlderFromUserScroll: false,
      userPresenceOverride: null,
      keepUnreadDividerVisible: false,
    }
  },
  computed: {
    ...mapState(useAuthStore, ['currentUser', 'authToken']),
    ...mapState(useProfileStore, ['currentProfile', 'profilesByUsername']),
    currentUserId() {
      return this.currentUser?.id
    },
    conversationKey() {
      return this.user ? String(this.user.id ?? this.user.username ?? '') : ''
    },
    draftText() {
      if (!this.conversationKey) return ''
      return this.draftsByConversation[this.conversationKey] || ''
    },
    selectedUserProfile() {
      const username = this.user?.username
      if (!username) return null
      return (
        this.profilesByUsername?.[username] ||
        (this.currentProfile?.user?.username === username ? this.currentProfile : null)
      )
    },
    userPresenceLabel() {
      if (!this.user) return ''
      return this.isSelectedUserOnline ? 'Online' : 'Offline'
    },
    userPresenceClass() {
      return this.isSelectedUserOnline ? 'text-emerald-600' : 'text-slate-500'
    },
    userPresenceDotClass() {
      return this.isSelectedUserOnline ? 'bg-emerald-500' : 'bg-slate-400'
    },
    isSelectedUserOnline() {
      if (!this.user) return false
      if (this.userPresenceOverride !== null) return Boolean(this.userPresenceOverride)
      return Boolean(this.user?.is_online)
    },
    chatAvatarUrl() {
      const profile = this.selectedUserProfile
      const avatar =
        this.user?.avatar_url ||
        this.user?.picture ||
        this.user?.picture_url ||
        this.user?.avatar ||
        this.user?.user?.picture ||
        this.user?.user?.picture_url ||
        profile?.picture ||
        ''
      const firstName =
        profile?.display_name ||
        profile?.user?.first_name ||
        this.user?.display_name ||
        this.user?.first_name ||
        this.user?.user?.first_name ||
        this.user?.username ||
        ''
      const lastName =
        profile?.user?.last_name || this.user?.last_name || this.user?.user?.last_name || ''

      return getAvatarUrl(
        avatar,
        firstName,
        lastName,
        this.user?.username || profile?.user?.username || '',
      )
    },
    groupedMessages() {
      const groups = []
      let lastDateKey = null
      let unreadDividerAdded = false
      const unreadInfo = this.getUnreadDividerInfo()
      const unreadDividerLabel =
        unreadInfo.count > 0
          ? `${unreadInfo.count} unread message${unreadInfo.count === 1 ? '' : 's'}`
          : 'Unread messages'

      this.messages.forEach((message, index) => {
        const isUnreadIncoming =
          !unreadDividerAdded && !message?.is_deleted && index === unreadInfo.index

        const timestamp = message?.timestamp
        if (timestamp) {
          const dateKey = this.getLocalDateKey(timestamp)

          if (dateKey !== lastDateKey) {
            groups.push({
              type: 'date',
              key: `date-${dateKey}-${groups.length}`,
              label: this.getDateLabel(timestamp),
            })
            lastDateKey = dateKey
          }
        }

        if (isUnreadIncoming) {
          groups.push({
            type: 'unread-divider',
            key: `unread-divider-${message.id ?? groups.length}`,
            label: unreadDividerLabel,
          })
          unreadDividerAdded = true
        }

        groups.push({
          type: 'message',
          key: `message-${message.id}`,
          message,
        })
      })

      return groups
    },
    unreadInThreadCount() {
      return this.getUnreadDividerInfo().count
    },
  },
  async created() {
    await this.loadSelectedUserProfile()
  },
  watch: {
    user() {
      if (!this.user) {
        this.messages = []
        this.editingMessage = null
        this.replyingMessage = null
        this.revealUnreadOnLoad = false
        this.unreadDividerSnapshot = null
        this.initialScrollDone = false
        this.canLoadOlderFromUserScroll = false
        this.userPresenceOverride = null
        this.keepUnreadDividerVisible = false
        this.stopReadSyncTimer()
        this.clearTypingIndicator()
        this.stopPolling()
        this.closeWebSocket()
        return
      }
      this.editingMessage = null
      this.replyingMessage = null
      this.revealUnreadOnLoad = false
      this.unreadDividerSnapshot = null
      this.initialScrollDone = false
      this.canLoadOlderFromUserScroll = false
      this.suppressLoadMoreUntil = Date.now() + 1000
      this.userPresenceOverride = null
      this.keepUnreadDividerVisible = false
      this.stopReadSyncTimer()
      this.clearTypingIndicator()
      this.refreshThread(true)
      this.loadSelectedUserProfile()
    },
  },
  mounted() {
    this.revealUnreadOnLoad = false
    this.refreshThread(true)
    this.loadSelectedUserProfile()
    document.addEventListener('visibilitychange', this.handleVisibilityChange)
    eventBus.on('messaging-presence-updated', this.handlePresenceBusEvent)
  },
  beforeUnmount() {
    void this.syncConversationReadState({ requireVisible: false })
    this.stopPolling()
    this.stopReadSyncTimer()
    this.clearTypingIndicator()
    this.closeWebSocket()
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
    eventBus.off('messaging-presence-updated', this.handlePresenceBusEvent)
  },
  methods: {
    ...mapActions(useProfileStore, ['fetchProfile']),
    stopReadSyncTimer() {
      if (this.readSyncTimer) {
        clearTimeout(this.readSyncTimer)
        this.readSyncTimer = null
      }
    },
    clearTypingIndicator() {
      this.isPartnerTyping = false
      if (this.typingIndicatorTimer) {
        clearTimeout(this.typingIndicatorTimer)
        this.typingIndicatorTimer = null
      }
    },
    clearTypingSenderTimer() {
      if (this.typingSendTimer) {
        clearTimeout(this.typingSendTimer)
        this.typingSendTimer = null
      }
    },
    scheduleTypingIndicatorReset() {
      if (this.typingIndicatorTimer) {
        clearTimeout(this.typingIndicatorTimer)
      }
      this.typingIndicatorTimer = window.setTimeout(() => {
        this.isPartnerTyping = false
        this.typingIndicatorTimer = null
      }, 2500)
    },
    sendTypingState(isTyping) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false
      this.ws.send(
        JSON.stringify({
          event: 'typing',
          is_typing: Boolean(isTyping),
        }),
      )
      return true
    },
    scheduleReadSync(delay = 250, options = {}) {
      if (!this.user || !this.authToken || document.hidden) return
      this.stopReadSyncTimer()
      this.readSyncTimer = window.setTimeout(() => {
        this.readSyncTimer = null
        void this.syncConversationReadState(options)
      }, delay)
    },
    sendReadStateOverSocket() {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false
      this.ws.send(
        JSON.stringify({
          event: 'read',
        }),
      )
      return true
    },
    async syncConversationReadState(options = {}) {
      const requireVisible = options?.requireVisible !== false
      const activeUser = this.user
      if (
        !activeUser ||
        !this.authToken ||
        this.readSyncInFlight ||
        (requireVisible && !this.isChatPaneVisible())
      )
        return
      this.readSyncInFlight = true
      try {
        let readState = null
        const sentOverSocket = this.sendReadStateOverSocket()
        if (!sentOverSocket) {
          readState = await markConversationAsRead(activeUser)
        }
        this.markThreadAsReadLocally()
        eventBus.emit('messaging-thread-read', {
          reader_id: this.currentUserId,
          sender_id: activeUser.id,
          updated_count:
            readState?.updated_count === undefined ? undefined : Number(readState.updated_count),
          unread_count:
            readState?.unread_count === undefined ? undefined : Number(readState.unread_count),
        })
      } catch {
        // keep the UI responsive even if the backend read call fails
      } finally {
        this.readSyncInFlight = false
      }
    },
    handleVisibilityChange() {
      if (document.hidden) this.stopReadSyncTimer()
      else this.scheduleReadSync(150)
    },
    async handleBackToList() {
      await this.syncConversationReadState({ requireVisible: false })
      this.$emit('back')
    },
    isChatPaneVisible() {
      if (document.hidden || !this.user) return false
      const el = this.$refs.messageList
      if (!el || !el.isConnected) return false
      const rect = el.getBoundingClientRect()
      return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.top < window.innerHeight
    },
    getMessageUserId(value) {
      if (value && typeof value === 'object') {
        return value.id ?? value.user_id ?? value.pk ?? value.user?.id ?? ''
      }
      return value ?? ''
    },
    getMessageSenderId(message) {
      return this.getMessageUserId(message?.sender ?? message?.sender_id ?? message?.sender_user)
    },
    getMessageReceiverId(message) {
      return this.getMessageUserId(
        message?.receiver ?? message?.receiver_id ?? message?.recipient ?? message?.recipient_id,
      )
    },
    isIncomingMessage(message) {
      if (!message) return false
      const currentUserId = String(this.currentUserId ?? '')
      const senderId = String(this.getMessageSenderId(message) ?? '')
      if (!currentUserId || !senderId) return false
      return senderId !== currentUserId
    },
    isUnreadIncomingMessage(message) {
      return !message?.is_deleted && !message?.is_read && this.isIncomingMessage(message)
    },
    captureUnreadDividerSnapshot() {
      const messages = Array.isArray(this.messages) ? this.messages : []
      const unreadMessages = messages.filter((message) => this.isUnreadIncomingMessage(message))

      this.unreadDividerSnapshot = unreadMessages.length
        ? {
            count: unreadMessages.length,
            firstMessageId: unreadMessages[0]?.id ?? null,
          }
        : this.getUnreadSnapshotFromInitialCount(messages)
    },
    clearUnreadDividerSnapshot() {
      this.keepUnreadDividerVisible = false
      this.unreadDividerSnapshot = null
    },
    rememberUnreadIncomingMessage(message) {
      if (!message?.id || !this.isIncomingMessage(message)) return

      if (!this.unreadDividerSnapshot?.count) {
        this.unreadDividerSnapshot = {
          count: 1,
          firstMessageId: message.id,
        }
        this.keepUnreadDividerVisible = true
        return
      }

      this.unreadDividerSnapshot = {
        ...this.unreadDividerSnapshot,
        count: this.unreadDividerSnapshot.count + 1,
      }
      this.keepUnreadDividerVisible = true
    },
    getInitialUnreadCount() {
      return Number(this.user?.initial_unread_count || this.user?.unread_count || 0)
    },
    getUnreadSnapshotFromInitialCount(messages) {
      const initialUnreadCount = this.getInitialUnreadCount()
      if (initialUnreadCount <= 0) return null

      const incomingMessages = messages.filter(
        (message) => !message?.is_deleted && this.isIncomingMessage(message),
      )
      if (!incomingMessages.length) return null

      const firstUnread =
        incomingMessages[Math.max(0, incomingMessages.length - initialUnreadCount)] || null
      return firstUnread
        ? {
            count: Math.min(initialUnreadCount, incomingMessages.length),
            firstMessageId: firstUnread.id ?? null,
          }
        : null
    },
    getUnreadDividerInfo() {
      if (this.unreadDividerSnapshot?.count > 0) {
        const firstMessageId = this.unreadDividerSnapshot.firstMessageId
        const index = this.messages.findIndex(
          (message) => String(message?.id) === String(firstMessageId),
        )
        if (index >= 0) {
          return { count: this.unreadDividerSnapshot.count, index }
        }
      }

      const messages = Array.isArray(this.messages) ? this.messages : []
      const flaggedUnread = messages.filter((message) => this.isUnreadIncomingMessage(message))

      if (flaggedUnread.length > 0) {
        const index = messages.findIndex((message) => this.isUnreadIncomingMessage(message))
        return { count: flaggedUnread.length, index }
      }
      return { count: 0, index: -1 }
    },
    getCelebrationEmojiFromMessage(message) {
      const raw = String(message?.content || '').trim()
      if (!raw) return ''

      const tokens = tokenizeMessageText(raw)
      if (!isEmojiOnlyMessage(tokens) || getEmojiCount(tokens) !== 1) return ''

      const celebrationEmoji = [...tokens]
        .reverse()
        .find((token) => token?.type === 'emoji' && isCelebrationEmoji(token.value))

      return celebrationEmoji?.value || ''
    },
    async loadSelectedUserProfile() {
      const username = this.user?.username
      if (!username) return
      if (this.profilesByUsername?.[username]) return
      try {
        await this.fetchProfile(username)
      } catch {
        // Keep the existing fallback avatar if profile loading fails.
      }
    },
    refreshThread(forceScroll = false) {
      if (!this.user) {
        this.messages = []
        this.editingMessage = null
        this.replyingMessage = null
        this.revealUnreadOnLoad = false
        this.unreadDividerSnapshot = null
        this.keepUnreadDividerVisible = false
        this.stickToBottom = true
        this.stopPolling()
        this.closeWebSocket()
        return
      }
      this.stickToBottom = true
      this.initialScrollDone = false
      this.canLoadOlderFromUserScroll = false
      this.suppressLoadMoreUntil = Date.now() + 1000
      this.getMessages({ forceScroll })
      this.connectWebSocket()
    },
    startPolling() {
      this.stopPolling()
      if (this.wsConnected) return
      this.pollTimer = setInterval(() => {
        this.getMessages()
      }, 5000)
    },
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
    connectWebSocket() {
      this.closeWebSocket()
      if (!this.user || !this.authToken) {
        this.startPolling()
        return
      }
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const wsBase = import.meta.env.VITE_WS_BASE_URL || '/ws/'
      const wsUrl = `${protocol}//${host}${wsBase}chat/${this.user.id}/?token=${this.authToken}`

      try {
        this.ws = new WebSocket(wsUrl)
      } catch {
        this.startPolling()
        return
      }

      this.ws.onopen = () => {
        this.wsConnected = true
        this.stopPolling()
        if (this.isLocallyTyping) {
          this.sendTypingState(true)
        }
      }
      this.ws.onclose = () => {
        this.wsConnected = false
        this.startPolling()
      }
      this.ws.onerror = () => {
        this.wsConnected = false
        this.startPolling()
      }
      this.ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data?.event === 'deleted' && data?.message?.id) {
            this.applyMessagePatch(data.message)
          } else if (data?.event === 'edited' && data?.message?.id) {
            this.applyMessagePatch(data.message)
          } else if (data?.message) {
            this.addMessageUnique(
              data.message,
              String(this.getMessageSenderId(data?.message)) === String(this.currentUserId),
            )
          } else if (data?.reaction) {
            this.applyReactionUpdate(data.reaction)
          } else if (data?.typing) {
            this.handleTypingEvent(data.typing)
          } else if (data?.read) {
            this.handleReadEvent(data.read)
          } else if (data?.presence) {
            this.handlePresenceEvent(data.presence)
          }
        } catch {
          // ignore
        }
      }
    },
    closeWebSocket() {
      if (this.ws) {
        this.ws.close()
        this.ws = null
      }
      this.wsConnected = false
      this.clearTypingIndicator()
      this.clearTypingSenderTimer()
    },
    markManualHistoryScroll() {
      this.canLoadOlderFromUserScroll = true
    },
    onScroll() {
      const el = this.$refs.messageList
      if (!el) return

      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
      this.showScrollDown = !nearBottom
      this.stickToBottom = nearBottom
      if (nearBottom) {
        if (Date.now() > this.suppressLoadMoreUntil) {
          this.clearUnreadDividerSnapshot()
        }
      }

      if (
        el.scrollTop < 50 &&
        this.hasMore &&
        !this.loadingMore &&
        !this.loading &&
        this.canLoadOlderFromUserScroll &&
        Date.now() > this.suppressLoadMoreUntil
      ) {
        this.canLoadOlderFromUserScroll = false
        this.loadMoreMessages()
      }
    },
    shouldAutoScroll() {
      const el = this.$refs.messageList
      if (!el) return true
      return el.scrollHeight - el.scrollTop - el.clientHeight < 80
    },
    getLocalDateKey(timestamp) {
      const date = new Date(timestamp)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
        date.getDate(),
      ).padStart(2, '0')}`
    },
    getDateLabel(timestamp) {
      if (!timestamp) return 'Unknown date'

      const messageDate = new Date(timestamp)
      const today = new Date()
      const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
      const startOfMessage = new Date(
        messageDate.getFullYear(),
        messageDate.getMonth(),
        messageDate.getDate(),
      )
      const dayDiff = Math.round((startOfToday - startOfMessage) / 86400000)

      if (dayDiff === 0) return 'Today'
      if (dayDiff === 1) return 'Yesterday'

      return messageDate.toLocaleDateString([], {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    },
    async getMessages(options = {}) {
      const forceScroll = Boolean(options.forceScroll)
      if (!this.user || !this.authToken) return
      this.loading = true
      const el = this.$refs.messageList
      const wasNearBottom = el ? el.scrollHeight - el.scrollTop - el.clientHeight < 80 : true
      const previousScrollTop = el ? el.scrollTop : 0
      const previousScrollHeight = el ? el.scrollHeight : 0
      try {
        const data = await getConversationMessages(this.user, { limit: 50, offset: 0 })
        this.messages = data.messages || []
        this.totalCount = data.total_count || 0
        this.hasMore = data.has_more || false
        this.loadOffset = this.messages.length
        this.captureUnreadDividerSnapshot()
        const shouldRevealUnread =
          forceScroll && !this.initialScrollDone && this.unreadInThreadCount > 0
        this.keepUnreadDividerVisible = shouldRevealUnread
        this.stickToBottom = !shouldRevealUnread

        this.$nextTick(() => {
          const list = this.$refs.messageList
          if (!list) return

          if (shouldRevealUnread) {
            this.$nextTick(() => {
              window.requestAnimationFrame(() => {
                this.revealUnreadThreadPosition()
                this.initialScrollDone = true
                this.canLoadOlderFromUserScroll = false
                this.scheduleReadSync(2500)
              })
            })
            return
          }

          if (forceScroll || wasNearBottom) {
            this.scrollToBottom(true)
            this.initialScrollDone = true
            this.canLoadOlderFromUserScroll = false
            this.showScrollDown = false
            this.scheduleReadSync(150)
            return
          }

          const nextScrollHeight = list.scrollHeight
          const heightDelta = nextScrollHeight - previousScrollHeight
          list.scrollTop = Math.max(0, previousScrollTop + heightDelta)
          this.showScrollDown = true
        })
      } catch {
        this.totalCount = 0
        this.hasMore = false
      } finally {
        this.loading = false
      }
    },
    async loadMoreMessages() {
      if (!this.user || !this.authToken || !this.hasMore || this.loadingMore) return

      this.loadingMore = true
      const el = this.$refs.messageList
      if (!el) {
        this.loadingMore = false
        return
      }

      const prevScrollHeight = el.scrollHeight
      const prevScrollTop = el.scrollTop

      try {
        const data = await getConversationMessages(this.user, {
          limit: 50,
          offset: this.loadOffset,
        })
        const newMessages = data.messages || []

        if (newMessages.length > 0) {
          this.messages = [...newMessages, ...this.messages]
          this.loadOffset += newMessages.length
          this.hasMore = data.has_more || false
          this.canLoadOlderFromUserScroll = false

          this.$nextTick(() => {
            const newScrollHeight = el.scrollHeight
            el.scrollTop = newScrollHeight - prevScrollHeight + prevScrollTop
          })
        } else {
          this.hasMore = false
        }
      } catch {
        this.hasMore = false
      } finally {
        this.loadingMore = false
      }
    },
    async sendMessage(payload) {
      const text = typeof payload === 'string' ? payload : payload?.text || ''
      const files = typeof payload === 'string' ? [] : payload?.files || []
      const media = typeof payload === 'string' ? null : payload?.media || null
      const editingMessageId =
        typeof payload === 'string' ? null : payload?.editingMessageId || null
      const replyToMessageId =
        typeof payload === 'string' ? null : payload?.replyToMessageId || null

      if (!text.trim() && !files.length && !media) return
      try {
        this.sendError = ''
        if (editingMessageId) {
          await this.updateMessage(editingMessageId, text.trim())
          return
        }
        if (media) {
          const mediaPayload = {
            content: text.trim(),
            reply_to_message_id: replyToMessageId,
            message_type: media.kind,
            gif_url: media.kind === 'gif' ? media.sendUrl : '',
            sticker_url: media.kind === 'sticker' ? media.sendUrl : '',
            provider: media.provider || 'giphy',
            provider_id: media.providerId,
            animated: Boolean(media.animated),
            media_title: media.title || '',
          }

          if (this.wsConnected && this.ws) {
            this.ws.send(JSON.stringify(mediaPayload))
          } else {
            const message = await sendConversationMessage(this.user, {
              ...mediaPayload,
              recipientUsername: this.user.username,
            })
            this.addMessageUnique(message, true)
          }
          this.replyingMessage = null
          this.markThreadAsReadLocally()
          this.$nextTick(() => this.scrollToBottom(true))
          void this.syncConversationReadState()
          return
        }
        if (files.length) {
          for (let index = 0; index < files.length; index += 1) {
            const file = files[index]
            const form = new FormData()
            form.append('media', file)
            if (index === 0 && text.trim()) {
              form.append('content', text.trim())
            }
            if (replyToMessageId) {
              form.append('reply_to_message_id', replyToMessageId)
            }
            const res = await fetch(
              `${window.location.origin}/api/messaging/conversations/${this.user.id}/media/`,
              {
                method: 'POST',
                headers: {
                  Authorization: this.authToken ? `Token ${this.authToken}` : '',
                },
                body: form,
              },
            ).catch(() => null)
            if (!res || !res.ok) {
              throw new Error('Media messages are not supported on this backend.')
            }
            const json = await res.json()
            this.addMessageUnique(json)
          }
          this.replyingMessage = null
          this.markThreadAsReadLocally()
          this.$nextTick(() => this.scrollToBottom(true))
          void this.syncConversationReadState()
          return
        }

        if (text.trim()) {
          if (this.wsConnected && this.ws) {
            this.ws.send(
              JSON.stringify({
                content: text.trim(),
                reply_to_message_id: replyToMessageId,
              }),
            )
          } else {
            const message = await sendConversationMessage(this.user, {
              content: text.trim(),
              reply_to_message_id: replyToMessageId,
              recipientUsername: this.user.username,
            })
            this.addMessageUnique(message, true)
          }
          this.replyingMessage = null
          this.markThreadAsReadLocally()
          this.$nextTick(() => this.scrollToBottom(true))
          void this.syncConversationReadState()
        }
      } catch (err) {
        this.sendError = err?.response?.data?.error || err?.message || 'Message failed to send.'
      }
    },
    async sendReaction(payload) {
      const messageId = payload?.messageId
      const emoji = payload?.emoji
      if (!messageId || !emoji) return
      try {
        const res = await chatApi.post('messaging/messages/react/', {
          message_id: messageId,
          emoji,
        })
        this.applyReactionUpdate(res.data)
      } catch {
        // ignore
      }
    },
    handleTyping(isTyping) {
      this.isLocallyTyping = Boolean(isTyping)
      this.clearTypingSenderTimer()
      if (!this.wsConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) return
      this.sendTypingState(isTyping)
      if (isTyping) {
        this.typingSendTimer = window.setTimeout(() => {
          this.typingSendTimer = null
          if (this.isLocallyTyping) {
            this.sendTypingState(true)
          }
        }, 1200)
      }
    },
    handleTypingEvent(typing) {
      const senderId = String(typing?.user_id ?? typing?.sender_id ?? '')
      if (senderId && senderId === String(this.currentUserId)) {
        return
      }

      if (typing?.is_typing) {
        this.isPartnerTyping = true
        this.scheduleTypingIndicatorReset()
        return
      }

      this.clearTypingIndicator()
    },
    handleReadEvent(read) {
      const readerId = String(read?.reader_id ?? read?.user_id ?? '')
      if (!readerId) return

      if (readerId === String(this.currentUserId)) {
        this.markThreadAsReadLocally()
        eventBus.emit('messaging-thread-read', read)
        return
      }

      this.messages = this.messages.map((message) => {
        const senderId = String(this.getMessageSenderId(message) ?? '')
        const receiverId = String(this.getMessageReceiverId(message) ?? '')
        if (
          !message ||
          senderId !== String(this.currentUserId) ||
          (receiverId && receiverId !== readerId)
        ) {
          return message
        }
        return {
          ...message,
          is_read: true,
        }
      })
      eventBus.emit('messaging-thread-read', read)
    },
    handlePresenceEvent(presence) {
      const userId = String(presence?.user_id ?? '')
      if (!userId) return
      eventBus.emit('messaging-presence-updated', presence)
      this.applyPresenceOverride(presence)
    },
    handlePresenceBusEvent(presence) {
      this.applyPresenceOverride(presence)
    },
    applyPresenceOverride(presence) {
      const userId = String(presence?.user_id ?? '')
      if (this.user && userId === String(this.user.id)) {
        this.userPresenceOverride = Boolean(presence?.is_online)
      }
    },
    openReactionPicker() {
      this.$refs.messageInput?.openEmojiPicker?.()
    },
    beginEditMessage(message) {
      if (
        !message ||
        String(this.getMessageSenderId(message)) !== String(this.currentUserId) ||
        message.is_deleted ||
        message.can_edit === false ||
        ['gif', 'sticker', 'file'].includes(String(message?.message_type || '').toLowerCase())
      )
        return
      this.replyingMessage = null
      this.editingMessage = { ...message }
      this.sendError = ''
      this.$nextTick(() => this.scrollToBottom(true))
    },
    beginReplyMessage(message) {
      if (!message || message.is_deleted) return
      this.editingMessage = null
      this.replyingMessage = { ...message }
      this.sendError = ''
      this.$nextTick(() => {
        const input = this.$refs.messageInput?.$refs?.inputArea
        if (input) {
          input.focus()
        }
      })
    },
    cancelEditMessage() {
      this.editingMessage = null
    },
    cancelReplyMessage() {
      this.replyingMessage = null
    },
    async updateMessage(messageId, content) {
      if (!messageId || !content.trim()) return
      try {
        const res = await chatApi.patch(`messaging/messages/${messageId}/`, {
          content: content.trim(),
        })
        this.applyMessagePatch(res.data)
        this.editingMessage = null
        eventBus.emit('messaging-read-updated')
      } catch (err) {
        this.sendError = err?.response?.data?.error || err?.message || 'Message failed to update.'
      }
    },
    async deleteMessage(message) {
      if (!message?.id) return
      if (String(this.getMessageSenderId(message)) !== String(this.currentUserId)) return
      const confirmed = window.confirm('Delete this message?')
      if (!confirmed) return
      try {
        const res = await chatApi.delete(`messaging/messages/${message.id}/`)
        this.applyMessagePatch(res.data)
        eventBus.emit('messaging-read-updated')
        if (this.editingMessage?.id === message.id) {
          this.editingMessage = null
        }
      } catch (err) {
        this.sendError = err?.response?.data?.error || err?.message || 'Message failed to delete.'
      }
    },
    applyReactionUpdate(update) {
      const messageId = update?.message_id
      if (!messageId) return
      const idx = this.messages.findIndex((msg) => String(msg.id) === String(messageId))
      if (idx === -1) return
      const existing = this.messages[idx]
      const reactorId = String(update?.reactor_id ?? '')
      const isCurrentUserReaction = reactorId && reactorId === String(this.currentUserId)
      this.messages[idx] = {
        ...existing,
        reactions: update.reactions || [],
        my_reaction: isCurrentUserReaction
          ? update.selected_emoji || ''
          : existing.my_reaction || '',
      }
    },
    applyMessagePatch(message) {
      if (!message?.id) return
      const idx = this.messages.findIndex((msg) => String(msg.id) === String(message.id))
      if (idx === -1) {
        this.messages.push(message)
        this.triggerEmojiEffectForMessage(message)
        return
      }
      this.messages[idx] = {
        ...this.messages[idx],
        ...message,
      }
      if (this.editingMessage?.id === message.id && message.is_deleted) {
        this.editingMessage = null
      }
    },
    addMessageUnique(message, forceScroll = false) {
      if (!message) return
      const exists = this.messages.some((msg) => String(msg.id) === String(message.id))
      if (!exists) {
        const wasNearBottom = this.shouldAutoScroll()
        const isMine = String(this.getMessageSenderId(message)) === String(this.currentUserId)
        const isIncoming = this.isIncomingMessage(message)
        this.messages.push(message)
        this.totalCount += 1
        this.triggerEmojiEffectForMessage(message)

        if (isIncoming) {
          this.clearTypingIndicator()
          if (this.isChatPaneVisible()) {
            this.clearUnreadDividerSnapshot()
            this.markThreadAsReadLocally()
            this.scheduleReadSync(150, { requireVisible: false })
          } else if (wasNearBottom) {
            this.clearUnreadDividerSnapshot()
            this.scheduleReadSync(200, { requireVisible: false })
          } else {
            this.rememberUnreadIncomingMessage(message)
          }
        }

        if (forceScroll || wasNearBottom || isMine) {
          this.stickToBottom = true
          this.$nextTick(() => this.scrollToBottom(true))
        } else {
          this.stickToBottom = false
          this.showScrollDown = true
        }
      }
    },
    markThreadAsReadLocally() {
      if (!this.keepUnreadDividerVisible) {
        this.clearUnreadDividerSnapshot()
      }
      const currentUserId = String(this.currentUserId ?? '')
      this.messages = this.messages.map((message) => {
        if (!message || String(this.getMessageSenderId(message)) === currentUserId) {
          return message
        }
        return {
          ...message,
          is_read: true,
        }
      })
    },
    updateDraftText(text) {
      if (!this.conversationKey) return
      this.draftsByConversation = {
        ...this.draftsByConversation,
        [this.conversationKey]: text || '',
      }
    },
    handleMessageMediaLoad() {
      if (!this.stickToBottom) return
      this.$nextTick(() => this.scrollToBottom(true))
    },
    handleMessageMediaError() {
      if (!this.stickToBottom) return
      this.$nextTick(() => this.scrollToBottom(true))
    },
    scrollToBottom(force = false) {
      const el = this.$refs.messageList
      if (!el) return
      if (!force && !this.shouldAutoScroll()) {
        this.showScrollDown = true
        return
      }
      this.suppressLoadMoreUntil = Date.now() + 400
      el.scrollTop = el.scrollHeight
      this.showScrollDown = false
      this.stickToBottom = true
      this.clearUnreadDividerSnapshot()
    },
    revealUnreadThreadPosition() {
      const el = this.$refs.messageList
      if (!el) return

      const unreadInfo = this.getUnreadDividerInfo()
      const targetMessage = unreadInfo.index >= 0 ? this.messages[unreadInfo.index] || null : null
      let didScroll = false

      const dividerEl = el.querySelector('[data-unread-divider]')
      if (dividerEl?.scrollIntoView) {
        const listRect = el.getBoundingClientRect()
        const dividerRect = dividerEl.getBoundingClientRect()
        const offsetTop = dividerRect.top - listRect.top
        const nextTop = el.scrollTop + offsetTop - 72
        this.suppressLoadMoreUntil = Date.now() + 400
        el.scrollTop = Math.max(0, nextTop)
        didScroll = true
      } else if (targetMessage?.id != null) {
        const targetEl = el.querySelector(`[data-message-id="${String(targetMessage.id)}"]`)
        if (targetEl?.scrollIntoView) {
          const listRect = el.getBoundingClientRect()
          const targetRect = targetEl.getBoundingClientRect()
          const offsetTop = targetRect.top - listRect.top
          const nextTop = el.scrollTop + offsetTop - 96
          this.suppressLoadMoreUntil = Date.now() + 400
          el.scrollTop = Math.max(0, nextTop)
          didScroll = true
        }
      }

      if (!didScroll) {
        this.scrollToBottom(true)
      } else {
        const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
        this.showScrollDown = !nearBottom
        this.stickToBottom = nearBottom
      }

      const latestMessage =
        [...this.messages].reverse().find((message) => !message?.is_deleted) || null
      const latestEmoji = this.getCelebrationEmojiFromMessage(latestMessage)
      if (latestEmoji) {
        this.$nextTick(() => {
          this.triggerEmojiEffect(latestEmoji)
        })
      }
    },
    triggerEmojiEffect(emoji, origin) {
      this.$refs.emojiLayer?.play?.(emoji, origin)
    },
    triggerEmojiEffectForMessage(message) {
      const emoji = this.getCelebrationEmojiFromMessage(message)
      if (!emoji) return
      this.$nextTick(() => {
        this.triggerEmojiEffect(emoji)
      })
    },
  },
}
</script>
