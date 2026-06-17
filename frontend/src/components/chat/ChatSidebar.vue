<script lang="ts">
import { defineComponent } from 'vue'
import axiosInstance from '@/services/axiosInstance'
import eventBus from '@/services/eventBus'
import { getMessagingConversations, getMessagingUsers } from '@/services/messagingCompat'
import { mapActions, mapState } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { buildMediaUrl, getAvatarUrl } from '@/utils/avatars'
import StableAvatar from './StableAvatar.vue'

export default defineComponent({
  emits: ['selectUser'],
  components: {
    StableAvatar,
  },
  props: {
    selectedUserId: {
      type: Number,
      default: null,
    },
    initialUsername: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      conversations: [] as any[],
      allUsers: [] as any[],
      search: '',
      loading: false,
      error: '',
      pollTimer: null as any,
      initialSelectionAttempted: false,
      profileFetchesInFlight: {} as Record<string, boolean>,
      profileFetchesAttempted: {} as Record<string, boolean>,
    }
  },
  computed: {
    ...mapState(useAuthStore, ['currentUser', 'authToken']),
    ...mapState(useProfileStore, ['currentProfile', 'profilesByUsername']),
    totalUnread(): number {
      return this.conversations.reduce((sum, u) => sum + (u.unread_count || 0), 0)
    },
    displayedUsers(): any[] {
      if (!this.search) {
        return this.conversations
      }
      const term = this.search.toLowerCase()
      return this.allUsers.filter((u) => {
        if (u.id === this.currentUser?.id) return false
        return (u.username || '').toLowerCase().includes(term)
      })
    },
  },
  watch: {
    search(val: string) {
      if (val && val.trim()) {
        this.searchUsers(val.trim())
      } else {
        this.allUsers = []
      }
    },
  },
  mounted() {
    if (this.authToken) {
      this.loadConversations()
      this.startPolling()
      this.tryAutoSelectInitialUser()
    }
    eventBus.on('messaging-read-updated', this.handleMessagingReadUpdated)
    eventBus.on('messaging-presence-updated', this.handlePresenceUpdated)
    eventBus.on('messaging-thread-read', this.handleThreadRead)
    eventBus.on('messaging-last-message-updated', this.handleLastMessageUpdated)
  },
  beforeUnmount() {
    this.stopPolling()
    eventBus.off('messaging-read-updated', this.handleMessagingReadUpdated)
    eventBus.off('messaging-presence-updated', this.handlePresenceUpdated)
    eventBus.off('messaging-thread-read', this.handleThreadRead)
    eventBus.off('messaging-last-message-updated', this.handleLastMessageUpdated)
  },
  methods: {
    getAvatarUrl,
    ...mapActions(useProfileStore, ['fetchProfile']),
    handleMessagingReadUpdated() {
      if (this.authToken) {
        this.loadConversations({ silent: true })
      }
    },
    handlePresenceUpdated(presence: any) {
      const userId = String(presence?.user_id ?? '')
      if (!userId) return
      const applyPresence = (rows: any[]) =>
        (rows || []).map((row) =>
          String(row?.id) === userId
            ? {
                ...row,
                is_online: Boolean(presence?.is_online),
              }
            : row,
        )
      this.conversations = applyPresence(this.conversations)
      this.allUsers = applyPresence(this.allUsers)
    },
    handleThreadRead(read: any) {
      const readerId = String(read?.reader_id ?? '')
      if (!readerId || readerId !== String(this.currentUser?.id)) return
      const senderId = String(read?.sender_id ?? '')
      if (!senderId) return
      this.conversations = this.conversations.map((row) =>
        String(row?.id) === senderId
          ? {
              ...row,
              unread_count: 0,
            }
          : row,
      )
      this.allUsers = this.allUsers.map((row) =>
        String(row?.id) === senderId
          ? {
              ...row,
              unread_count: 0,
            }
          : row,
      )
    },
    getConversationUsername(user: any): string {
      return user?.username || user?.user?.username || ''
    },
    getConversationProfile(user: any): any {
      const username = this.getConversationUsername(user)
      if (!username) return null
      return (
        this.profilesByUsername?.[username] ||
        (this.currentProfile?.user?.username === username ? this.currentProfile : null)
      )
    },
    getConversationPicture(user: any): string {
      const profile = this.getConversationProfile(user)
      return (
        user?.picture ||
        user?.avatar_url ||
        user?.picture_url ||
        user?.avatar ||
        user?.user?.picture ||
        user?.user?.picture_url ||
        user?.user?.avatar_url ||
        profile?.picture ||
        ''
      )
    },
    getConversationFirstName(user: any): string {
      const profile = this.getConversationProfile(user)
      return (
        profile?.display_name ||
        profile?.user?.first_name ||
        user?.first_name ||
        user?.display_name ||
        user?.user?.first_name ||
        ''
      )
    },
    getConversationLastName(user: any): string {
      const profile = this.getConversationProfile(user)
      return profile?.user?.last_name || user?.last_name || user?.user?.last_name || ''
    },
    getConversationAvatarUrl(user: any): string {
      const username = this.getConversationUsername(user)
      return getAvatarUrl(
        this.getConversationPicture(user),
        this.getConversationFirstName(user) || username,
        this.getConversationLastName(user),
        username,
      )
    },
    getConversationKey(user: any): string {
      return String(
        user?.id ??
          user?.conversation_id ??
          user?.conversationId ??
          this.getConversationUsername(user),
      )
    },
    lastMessagePreview(user: any): any {
      const preview = user?.last_message_preview || null
      const url = buildMediaUrl(preview?.url || '')
      if (!preview || !url) return null
      return {
        ...preview,
        url,
      }
    },
    lastMessagePreviewLabel(user: any): string {
      const kind = this.lastMessagePreview(user)?.kind
      if (kind === 'video') return 'Video'
      if (kind === 'gif') return 'GIF'
      if (kind === 'sticker') return 'Sticker'
      if (kind === 'image') return 'Photo'
      return 'Media'
    },
    getExistingAvatarRow(user: any, rows: any[] = []): any {
      const username = this.getConversationUsername(user)
      const key = this.getConversationKey(user)
      return (rows || []).find((row) => {
        return (
          this.getConversationKey(row) === key ||
          (username && this.getConversationUsername(row) === username)
        )
      })
    },
    hydrateUserAvatar(user: any, existingUser: any = null): any {
      const username = this.getConversationUsername(user)
      const picture = this.getConversationPicture(user)
      const firstName = this.getConversationFirstName(user) || username
      const lastName = this.getConversationLastName(user)
      const avatarUrl = getAvatarUrl(picture, firstName, lastName, username)

      return {
        ...user,
        picture,
        avatar_url: picture,
        picture_url: user?.picture_url || '',
        avatar: user?.avatar || '',
        first_name: firstName,
        last_name: lastName,
        avatar_display_url: picture
          ? avatarUrl
          : existingUser?.avatar_display_url || user?.avatar_display_url || avatarUrl,
      }
    },
    mergeProfileIntoConversation(user: any): any {
      return this.hydrateUserAvatar(user, this.getExistingAvatarRow(user, this.conversations))
    },
    timeAgo(isoString: any): string {
      if (!isoString) return ''
      const diff = (Date.now() - new Date(isoString).getTime()) / 1000
      if (diff < 60) return 'just now'
      return new Date(isoString).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    },
    handleUserClick(user: any) {
      const unreadCount = Number(user?.unread_count || 0)
      this.$emit(
        'selectUser',
        this.mergeProfileIntoConversation({
          ...user,
          initial_unread_count: unreadCount,
        }),
      )
    },
    async loadConversations(options: any = {}) {
      try {
        const rows = await getMessagingConversations()
        this.hydrateConversationAvatars(rows)
        this.prefetchProfilesForUsers(this.conversations)
      } catch (err) {
        console.error(err)
      }
    },
    async loadInitialUserByUsername() {
      if (!this.initialUsername || this.initialSelectionAttempted || this.selectedUserId) return
      this.initialSelectionAttempted = true
      try {
        const results = await getMessagingUsers(this.initialUsername)
        const match = (results || []).find((user) => user.username === this.initialUsername)
        if (match) {
          this.$emit('selectUser', this.mergeProfileIntoConversation(match))
        }
      } catch {
        // silent
      }
    },
    async searchUsers(query: any) {
      try {
        const res = await axiosInstance.get('/search/users/', {
          params: { q: query },
        })
        const results = res.data?.results || []
        this.allUsers = results
          .filter((u: any) => u.id !== this.currentUser?.id)
          .map((user: any) =>
            this.hydrateUserAvatar(user, this.getExistingAvatarRow(user, this.allUsers)),
          )
        this.prefetchProfilesForUsers(this.allUsers)
      } catch {
        // silent
      }
    },
    hydrateConversationAvatars(rows?: any[]) {
      const targetRows = rows || this.conversations || []
      const previousRows = this.conversations || []
      this.conversations = targetRows.map((user) =>
        this.hydrateUserAvatar(user, this.getExistingAvatarRow(user, previousRows)),
      )
    },
    prefetchProfilesForUsers(users: any[] = []) {
      ;(users || []).forEach((user) => {
        const username = this.getConversationUsername(user)
        if (
          !username ||
          this.profilesByUsername?.[username] ||
          this.profileFetchesInFlight[username] ||
          this.profileFetchesAttempted[username]
        ) {
          return
        }
        this.profileFetchesInFlight = {
          ...this.profileFetchesInFlight,
          [username]: true,
        }
        this.profileFetchesAttempted = {
          ...this.profileFetchesAttempted,
          [username]: true,
        }
        this.fetchProfile(username)
          .then(() => {
            this.hydrateConversationAvatars()
            this.allUsers = this.allUsers.map((row) =>
              this.getConversationUsername(row) === username
                ? this.hydrateUserAvatar(row, row)
                : row,
            )
          })
          .catch(() => {
            // Keep the generated initials avatar if the profile request fails.
          })
          .finally(() => {
            const { [username]: _done, ...rest } = this.profileFetchesInFlight
            this.profileFetchesInFlight = rest
          })
      })
    },
    moveConversationToTop(userId: any, lastMessage: any, isMine: boolean = false) {
      const idx = this.conversations.findIndex((c) => c.id === userId)
      if (idx !== -1) {
        const conv = this.conversations[idx]
        conv.last_message = lastMessage
        conv.last_message_time = new Date().toISOString()
        conv.last_message_is_mine = isMine
        if (!isMine) conv.unread_count = (conv.unread_count || 0) + 1

        // Move to top
        this.conversations.splice(idx, 1)
        this.conversations.unshift(conv)
      } else {
        // If not in list, reload to get new conversation
        this.loadConversations({ silent: true })
      }
    },
    handleLastMessageUpdated(update: any) {
      const userId = update?.user_id
      if (!userId) return
      const idx = this.conversations.findIndex((c) => String(c.id) === String(userId))
      if (idx === -1) {
        this.loadConversations({ silent: true })
        return
      }

      const conv = {
        ...this.conversations[idx],
        last_message: update.last_message || '',
        last_message_time: update.timestamp || new Date().toISOString(),
        last_message_is_mine: Boolean(update.is_mine),
        last_message_preview: update.preview || null,
      }
      this.conversations.splice(idx, 1)
      this.conversations.unshift(conv)
    },
    tryAutoSelectInitialUser() {
      if (!this.initialUsername || this.selectedUserId) return
      const match = this.conversations.find((user) => user.username === this.initialUsername)
      if (match) {
        this.$emit('selectUser', this.mergeProfileIntoConversation(match))
      } else {
        this.loadInitialUserByUsername()
      }
    },
    startPolling() {
      this.stopPolling()
      if (!this.authToken) return
      this.pollTimer = setInterval(() => {
        this.loadConversations({ silent: true })
      }, 5000)
    },
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
  },
})
</script>

<template>
  <aside
    class="flex h-full min-h-0 w-full min-w-0 flex-col gap-4 overflow-hidden rounded-[1.75rem] border border-violet-100/80 bg-gradient-to-b from-white/95 via-violet-50/70 to-fuchsia-50/50 p-4 shadow-[0_28px_90px_rgba(139,92,246,0.12)] backdrop-blur-2xl transition-all duration-300 sm:rounded-[2.5rem] sm:p-5 lg:min-w-[300px]"
  >
    <!-- Header -->
    <div class="flex items-end justify-between px-1 pt-1">
      <div>
        <div class="flex items-center gap-2">
          <div
            class="h-2.5 w-2.5 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 shadow-[0_0_0_4px_rgba(139,92,246,0.12)]"
          ></div>
          <h3 class="m-0 text-xl font-black tracking-tight text-slate-900">Messages</h3>
        </div>
        <!-- <p class="mt-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          Direct chat
        </p> -->
      </div>
      <!-- <span
        v-if="totalUnread > 0"
        class="flex h-7 min-w-[28px] items-center justify-center rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 px-2 text-[11px] font-black text-white shadow-[0_6px_18px_rgba(139,92,246,0.28)]"
      >
        {{ totalUnread }}
      </span> -->
    </div>

    <!-- Search -->
    <div class="group relative px-1">
      <div
        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white p-2 text-violet-300 shadow-sm transition-colors group-focus-within:text-violet-500"
      >
        <svg
          class="h-4.5 w-4.5"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          viewBox="0 0 24 24"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
      </div>
      <input
        v-model.trim="search"
        class="w-full rounded-[1.35rem] border border-violet-100/80 bg-white/90 py-3.5 pl-12 pr-10 text-sm font-medium text-slate-800 outline-none transition-all placeholder:text-slate-400 hover:bg-white hover:shadow-sm focus:border-violet-300/70 focus:bg-white focus:ring-4 focus:ring-violet-500/10 sm:rounded-[1.5rem]"
        placeholder="Find someone..."
        aria-label="Search users"
      />
      <button
        v-if="search"
        class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1.5 text-slate-400 transition hover:bg-slate-200 hover:text-slate-600"
        type="button"
        @click="search = ''"
      >
        <svg
          class="h-3.5 w-3.5"
          fill="none"
          stroke="currentColor"
          stroke-width="3"
          viewBox="0 0 24 24"
        >
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Loading / Error States -->
    <div v-if="loading" class="flex flex-col items-center justify-center gap-3 py-10 opacity-60">
      <div
        class="h-6 w-6 rounded-full border-2 border-violet-100 border-t-violet-500 animate-spin"
      ></div>
      <span class="text-xs font-semibold text-slate-400 uppercase tracking-widest"
        >Updating...</span
      >
    </div>

    <div v-if="error" class="mx-1 rounded-2xl bg-rose-50 p-4 text-center">
      <p class="text-xs font-bold text-rose-500 uppercase tracking-tight">{{ error }}</p>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && !search && conversations.length === 0"
      class="flex min-h-0 flex-1 flex-col items-center justify-center gap-4 px-4 text-center"
    >
      <div class="relative">
        <div class="absolute -inset-4 rounded-full bg-violet-100/60 blur-xl"></div>
        <div
          class="relative grid h-16 w-16 place-items-center rounded-3xl bg-gradient-to-br from-violet-500 to-fuchsia-600 shadow-xl shadow-violet-200"
        >
          <svg
            class="h-8 w-8 text-white"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
      </div>
      <div>
        <p class="text-base font-bold text-slate-800">Your inbox is Waiting</p>
        <p class="mt-1 text-xs font-medium text-slate-400">
          Find your pepole and start a conversation!
        </p>
      </div>
    </div>

    <!-- User List -->
    <div class="custom-scrollbar flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto pr-1">
      <div
        v-if="!search && conversations.length > 0"
        class="mb-2 flex items-center justify-between px-3"
      >
        <span class="text-[10px] font-black uppercase tracking-[0.15em] text-slate-400"
          >Recent Chats</span
        >
      </div>
      <div v-if="search" class="mb-2 px-3">
        <span class="text-[10px] font-black uppercase tracking-[0.15em] text-violet-500"
          >Search Results</span
        >
      </div>

      <div
        v-for="user in displayedUsers"
        :key="getConversationKey(user)"
        class="group relative mx-0.5 flex cursor-pointer items-center gap-3 rounded-[1.45rem] border border-violet-100/70 bg-white/82 p-3 shadow-sm shadow-violet-100/40 transition-all duration-200 hover:-translate-y-0.5 hover:border-violet-200 hover:bg-white hover:shadow-md hover:shadow-violet-100 sm:gap-4 sm:rounded-[1.75rem] sm:p-3.5"
        :class="[
          user.unread_count > 0 && !search ? 'bg-violet-50/80' : '',
          selectedUserId === user.id
            ? '!border-violet-300/70 bg-violet-50/90 shadow-md shadow-violet-100 ring-1 ring-violet-500/10'
            : '',
        ]"
        role="button"
        tabindex="0"
        @click="handleUserClick(user)"
        @keyup.enter="handleUserClick(user)"
      >
        <!-- Selection Indicator -->
        <div
          v-if="selectedUserId === user.id"
          class="absolute left-1 top-1/2 h-8 w-1 -translate-y-1/2 rounded-full bg-gradient-to-b from-violet-500 to-fuchsia-500"
        ></div>

        <!-- Avatar Container -->
        <div class="relative flex-shrink-0">
          <StableAvatar
            :src="user.avatar_display_url || getConversationAvatarUrl(user)"
            :alt="`${getConversationUsername(user) || 'user'} avatar`"
            class="relative z-10 h-12 w-12 rounded-[3.25rem] object-cover"
          />
          <!-- Unread Badge -->
          <div
            v-if="user.unread_count > 0"
            class="absolute -right-1 -top-1 z-20 grid h-5 w-5 place-items-center rounded-full border-2 border-white bg-gradient-to-r from-fuchsia-600 to-fuchsia-600 text-[10px] font-black text-white shadow-sm"
          >
            {{ user.unread_count > 9 ? '9+' : user.unread_count }}
          </div>
        </div>

        <!-- Info -->
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-1">
            <RouterLink
              v-if="user.username"
              :to="{ name: 'profile', params: { username: user.username } }"
              class="truncate text-sm font-bold tracking-tight text-slate-900 transition-colors hover:text-violet-600"
              @click.stop
            >
              {{ user.username }}
            </RouterLink>
            <span v-else class="truncate text-sm font-bold tracking-tight text-slate-900">
              Unknown user
            </span>
            <span
              v-if="user.last_message_time && !search"
              class="flex-shrink-0 text-[10px] font-bold text-slate-400 uppercase"
            >
              {{ timeAgo(user.last_message_time) }}
            </span>
          </div>

          <!-- Last Message -->
          <div
            v-if="!search"
            class="mt-0.5 truncate text-xs"
            :class="
              user.unread_count > 0 ? 'font-bold text-slate-700' : 'font-medium text-slate-400'
            "
          >
            <!-- <template v-if="lastMessagePreview(user)">
              <span v-if="user.last_message_is_mine" class="opacity-60">You: </span>
              {{ lastMessagePreviewLabel(user) }}
            </template>
            <template v-else-if="user.last_message">
              <span v-if="user.last_message_is_mine" class="opacity-60">You: </span>
              {{ user.last_message }}
            </template>
            <template v-else>Start a conversation</template> -->
          </div>
        </div>
      </div>

      <!-- No search results -->
      <div
        v-if="search && displayedUsers.length === 0 && !loading"
        class="flex flex-col items-center justify-center gap-2 py-10 opacity-60"
      >
        <div class="text-3xl">🔍</div>
        <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">No users found</p>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
  transition: background 0.2s;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 0.8s linear infinite;
}
</style>
