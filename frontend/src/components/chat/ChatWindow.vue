<template>
  <section class="relative flex-1 overflow-hidden">
    <!-- Dynamic Ambient Background -->
    <div
      class="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-gradient-to-br from-slate-50 via-white to-indigo-50/30"
    >
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(99,102,241,0.08),transparent_24%),radial-gradient(circle_at_top_right,rgba(168,85,247,0.06),transparent_26%),radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.04),transparent_22%)]"
      ></div>
      <div
        class="absolute -left-24 top-24 h-96 w-96 rounded-full bg-blue-400/10 blur-[120px]"
      ></div>
      <div
        class="absolute right-10 top-40 h-80 w-80 rounded-full bg-violet-400/10 blur-[120px]"
      ></div>
      <div
        class="absolute bottom-20 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-indigo-400/5 blur-[100px]"
      ></div>
    </div>

    <!-- Empty/No Selection State -->
    <div
      v-if="!user"
      class="flex min-h-[calc(100vh-160px)] flex-col items-center justify-center gap-6 rounded-[2.5rem] border border-white/80 bg-white/90 p-10 text-center shadow-[0_30px_100px_rgba(79,70,229,0.08)] backdrop-blur-2xl"
    >
      <div class="relative">
        <div
          class="absolute -inset-8 rounded-full bg-gradient-to-r from-blue-100 via-indigo-100 to-cyan-100 blur-2xl"
        ></div>
        <div
          class="relative grid h-24 w-24 place-items-center rounded-[2rem] bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-600 shadow-2xl shadow-blue-200 transition-all duration-300 hover:scale-105 hover:shadow-blue-300"
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
        <h3 class="text-2xl font-black tracking-tight text-slate-900">Your conversations</h3>
        <p class="mx-auto max-w-xs text-sm font-medium text-slate-500">
          Select a friend from the sidebar or search to start messaging
        </p>
        <div class="flex justify-center gap-2 pt-4">
          <div class="h-1.5 w-8 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500"></div>
          <div class="h-1.5 w-3 rounded-full bg-slate-200"></div>
          <div class="h-1.5 w-2 rounded-full bg-slate-200"></div>
        </div>
      </div>
    </div>

    <!-- Active Chat Window -->
    <div
      v-else
      class="relative flex h-[calc(100vh-160px)] flex-col overflow-hidden rounded-[2.5rem] border border-white/80 bg-white/90 shadow-[0_28px_90px_rgba(79,70,229,0.08)] backdrop-blur-2xl"
    >
      <!-- Chat Header -->
      <div
        class="relative z-10 flex items-center justify-between border-b border-slate-200/50 bg-white/70 px-6 py-4 backdrop-blur-xl"
      >
        <div class="flex items-center gap-4">
          <div class="relative group">
            <img
              v-if="chatAvatarUrl"
              :src="chatAvatarUrl"
              :alt="`${user.username} avatar`"
              class="h-12 w-12 rounded-[1.25rem] object-cover shadow-md shadow-blue-200 transition-all duration-300 group-hover:shadow-lg group-hover:shadow-blue-300"
            />
            <div
              v-else
              class="grid h-12 w-12 place-items-center rounded-[1.25rem] bg-gradient-to-br from-blue-600 to-indigo-700 font-bold text-white shadow-md shadow-blue-200 transition-all duration-300 group-hover:shadow-lg group-hover:shadow-blue-300"
            >
              {{ user.username?.[0]?.toUpperCase() || 'U' }}
            </div>
            <!-- <div
              class="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-white bg-blue-500 shadow-sm ring-2 ring-blue-400/20"
            ></div> -->
          </div>
          <div>
            <div class="text-lg font-black tracking-tight text-slate-900">{{ user.username }}</div>
            <!-- <div
              class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500"
            >
              <span class="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
              <span class="h-1.5 w-1.5 rounded-full bg-indigo-300"></span>
              <span class="h-1.5 w-1.5 rounded-full bg-cyan-200"></span>
              <span class="ml-1">Active now</span>
            </div> -->
          </div>
        </div>

        <!-- Header Actions -->
        <div class="flex gap-1">
          <button
            class="group grid h-10 w-10 place-items-center rounded-[1.1rem] bg-slate-100/60 text-slate-500 transition-all duration-200 hover:bg-white hover:text-blue-600 hover:shadow-md active:scale-95"
          >
            <svg
              class="h-5 w-5 transition-transform duration-200 group-hover:scale-110"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
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
      <div ref="messageList" class="message-area relative flex-1 overflow-y-auto px-5 py-5 lg:px-6">
        <div
          class="pointer-events-none absolute inset-0 opacity-[0.03]"
          style="
            background-image: radial-gradient(#4f46e5 1px, transparent 1px);
            background-size: 24px 24px;
          "
        ></div>
        <div class="relative z-10 flex flex-col gap-3">
          <div class="flex flex-col gap-2">
            <template v-for="item in groupedMessages" :key="item.key">
              <div v-if="item.type === 'date'" class="flex justify-center py-2">
                <span
                  class="rounded-full border border-slate-200/70 bg-white/80 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500 shadow-sm backdrop-blur-sm"
                >
                  {{ item.label }}
                </span>
              </div>
              <MessageBubble
                v-else
                :message="item.message"
                :isMe="String(item.message.sender) === String(currentUserId)"
                @react="sendReaction"
                @reply="beginReplyMessage"
                @edit="beginEditMessage"
                @delete="deleteMessage"
              />
            </template>
          </div>

          <div
            v-if="!messages.length"
            class="flex flex-col items-center justify-center gap-4 py-20 opacity-70"
          >
            <div class="text-5xl animate-bounce">👋</div>
            <div class="text-center space-y-1">
              <p class="text-sm font-black uppercase tracking-[0.18em] text-slate-500">
                Start the conversation here
              </p>
              <p class="text-xs font-medium text-slate-400">Say hello to {{ user.username }}</p>
            </div>
          </div>
        </div>
      </div>

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
          class="absolute bottom-28 right-6 z-30 grid h-11 w-11 place-items-center rounded-xl bg-white text-indigo-600 shadow-lg ring-1 ring-slate-200 transition-all duration-200 hover:-translate-y-0.5 hover:bg-indigo-600 hover:text-white hover:shadow-indigo-200 active:scale-95"
          type="button"
          @click="scrollToBottom(true)"
        >
          <svg
            class="h-5 w-5 transition-transform duration-200 group-hover:translate-y-0.5"
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
          class="absolute bottom-28 left-6 right-6 z-40 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500 p-4 text-sm font-semibold text-white shadow-xl shadow-rose-200/50 backdrop-blur-sm"
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
              class="rounded-lg p-1 hover:bg-white/20 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      </transition>

      <!-- Input Area -->
      <div
        class="relative z-10 border-t border-slate-200/60 bg-white/55 px-6 py-4 backdrop-blur-md"
      >
        <MessageInput
          v-if="user"
          ref="messageInput"
          :disabled="!user"
          :editing-message="editingMessage"
          :replying-message="replyingMessage"
          @send="sendMessage"
          @cancel-edit="cancelEditMessage"
          @cancel-reply="cancelReplyMessage"
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
  scrollbar-color: rgba(99, 102, 241, 0.3) transparent;
}

.message-area::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.message-area::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 10px;
}

.message-area::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 10px;
  transition: background 0.2s;
}

.message-area::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}
</style>

<script>
import chatApi from '@/services/messageApi'
import MessageInput from './MessageInput.vue'
import MessageBubble from './MessageBubble.vue'
import { mapState } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { mapActions } from 'pinia'
import { useProfileStore } from '@/stores/profile'
import { getAvatarUrl } from '@/utils/avatars'
import eventBus from '@/services/eventBus'

export default {
  props: ['user'],
  components: {
    MessageBubble,
    MessageInput,
  },
  data() {
    return {
      messages: [],
      loading: false,
      sendError: '',
      pollTimer: null,
      ws: null,
      wsConnected: false,
      showScrollDown: false,
      totalCount: 0,
      hasMore: false,
      loadingMore: false,
      loadOffset: 0,
      editingMessage: null,
      replyingMessage: null,
    }
  },
  computed: {
    ...mapState(useAuthStore, ['currentUser', 'authToken']),
    ...mapState(useProfileStore, ['currentProfile', 'profilesByUsername']),
    currentUserId() {
      return this.currentUser?.id
    },
    selectedUserProfile() {
      const username = this.user?.username
      if (!username) return null
      return (
        this.profilesByUsername?.[username] ||
        (this.currentProfile?.user?.username === username ? this.currentProfile : null)
      )
    },
    chatAvatarUrl() {
      const profile = this.selectedUserProfile
      const avatar =
        this.user?.avatar_url ||
        this.user?.picture ||
        profile?.picture ||
        this.user?.picture_url ||
        this.user?.avatar ||
        this.user?.user?.picture ||
        this.user?.user?.picture_url ||
        ''
      if (!avatar) return ''

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

      return getAvatarUrl(avatar, firstName, lastName, this.user?.username || profile?.user?.username || '')
    },
    groupedMessages() {
      const groups = []
      let lastDateKey = null

      this.messages.forEach((message) => {
        const timestamp = message?.timestamp
        const dateKey = timestamp ? this.getLocalDateKey(timestamp) : 'unknown'

        if (dateKey !== lastDateKey) {
          groups.push({
            type: 'date',
            key: `date-${dateKey}-${groups.length}`,
            label: this.getDateLabel(timestamp),
          })
          lastDateKey = dateKey
        }

        groups.push({
          type: 'message',
          key: `message-${message.id}`,
          message,
        })
      })

      return groups
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
        this.stopPolling()
        this.closeWebSocket()
        this.detachScroll()
        return
      }
      this.editingMessage = null
      this.$nextTick(this.attachScroll)
      this.refreshThread()
      this.loadSelectedUserProfile()
    },
  },
  mounted() {
    this.refreshThread()
    this.$nextTick(this.attachScroll)
    this.loadSelectedUserProfile()
  },
  beforeUnmount() {
    this.stopPolling()
    this.closeWebSocket()
    this.detachScroll()
  },
  methods: {
    ...mapActions(useProfileStore, ['fetchProfile']),
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
    refreshThread() {
      if (!this.user) {
        this.messages = []
        this.editingMessage = null
        this.replyingMessage = null
        this.stopPolling()
        this.closeWebSocket()
        return
      }
      this.getMessages()
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
            this.addMessageUnique(data.message, true)
          } else if (data?.reaction) {
            this.applyReactionUpdate(data.reaction)
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
    },
    attachScroll() {
      this.detachScroll()
      const el = this.$refs.messageList
      if (el) {
        el.addEventListener('scroll', this.onScroll, { passive: true })
      }
    },
    detachScroll() {
      const el = this.$refs.messageList
      if (el) {
        el.removeEventListener('scroll', this.onScroll)
      }
    },
    onScroll() {
      const el = this.$refs.messageList
      if (!el) return

      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
      this.showScrollDown = !nearBottom

      if (el.scrollTop < 50 && this.hasMore && !this.loadingMore && !this.loading) {
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
    async getMessages() {
      if (!this.user || !this.authToken) return
      this.loading = true
      const el = this.$refs.messageList
      const wasNearBottom = el ? el.scrollHeight - el.scrollTop - el.clientHeight < 80 : true
      const previousScrollTop = el ? el.scrollTop : 0
      const previousScrollHeight = el ? el.scrollHeight : 0
      try {
        const res = await chatApi.get(`messaging/conversations/${this.user.id}/messages/?limit=50&offset=0`)
        const data = res.data
        this.messages = data.messages || []
        this.totalCount = data.total_count || 0
        this.hasMore = data.has_more || false
        this.loadOffset = this.messages.length
        eventBus.emit('messaging-read-updated')

        this.$nextTick(() => {
          const list = this.$refs.messageList
          if (!list) return

          if (wasNearBottom) {
            this.scrollToBottom(true)
            this.showScrollDown = false
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
        const res = await chatApi.get(
          `messaging/conversations/${this.user.id}/messages/?limit=50&offset=${this.loadOffset}`,
        )
        const data = res.data
        const newMessages = data.messages || []

        if (newMessages.length > 0) {
          this.messages = [...newMessages, ...this.messages]
          this.loadOffset += newMessages.length
          this.hasMore = data.has_more || false

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
      const editingMessageId =
        typeof payload === 'string' ? null : payload?.editingMessageId || null
      const replyToMessageId =
        typeof payload === 'string' ? null : payload?.replyToMessageId || null

      if (!text.trim() && !files.length) return
      try {
        this.sendError = ''
        if (editingMessageId) {
          await this.updateMessage(editingMessageId, text.trim())
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
            const res = await chatApi.post(`messaging/conversations/${this.user.id}/media/`, form)
            this.addMessageUnique(res.data)
          }
          this.replyingMessage = null
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
            const res = await chatApi.post(`messaging/conversations/${this.user.id}/send/`, {
              content: text.trim(),
              reply_to_message_id: replyToMessageId,
            })
            this.addMessageUnique(res.data)
          }
          this.replyingMessage = null
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
    beginEditMessage(message) {
      if (
        !message ||
        String(message.sender) !== String(this.currentUserId) ||
        message.is_deleted ||
        message.can_edit === false
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
      if (String(message.sender) !== String(this.currentUserId)) return
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
      this.messages[idx] = { ...existing, reactions: update.reactions || [] }
    },
    applyMessagePatch(message) {
      if (!message?.id) return
      const idx = this.messages.findIndex((msg) => String(msg.id) === String(message.id))
      if (idx === -1) {
        this.messages.push(message)
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
    addMessageUnique(message) {
      if (!message) return
      const exists = this.messages.some((msg) => String(msg.id) === String(message.id))
      if (!exists) {
        this.messages.push(message)
        this.totalCount += 1
        if (this.shouldAutoScroll()) {
          this.$nextTick(() => this.scrollToBottom(true))
        } else {
          this.showScrollDown = true
        }
      }
    },
    scrollToBottom(force = false) {
      const el = this.$refs.messageList
      if (!el) return
      if (!force && !this.shouldAutoScroll()) {
        this.showScrollDown = true
        return
      }
      el.scrollTop = el.scrollHeight
      this.showScrollDown = false
    },
  },
}
</script>
<!--
<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(203, 213, 225, 0.5);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.message-list-enter-active,
.message-list-leave-active {
  transition: all 0.4s ease;
}
.message-list-enter-from,
.message-list-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style> -->
