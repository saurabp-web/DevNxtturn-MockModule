<template>
  <aside
    class="flex h-[calc(100vh-160px)] min-h-0 min-w-[300px] flex-col gap-4 overflow-hidden rounded-[2.5rem] border border-white/60 bg-gradient-to-b from-white/95 to-slate-50/95 p-4 shadow-[0_28px_90px_rgba(15,23,42,0.10)] backdrop-blur-2xl transition-all duration-300"
  >
    <!-- Header -->
    <div class="flex items-end justify-between px-2 pt-1">
      <div>
        <div class="flex items-center gap-2">
          <div
            class="h-2.5 w-2.5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 shadow-[0_0_0_4px_rgba(59,130,246,0.10)]"
          ></div>
          <h3 class="m-0 text-xl font-black tracking-tight text-slate-900">Messages</h3>
        </div>
        <p class="mt-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          Direct chat
        </p>
      </div>
      <span
        v-if="totalUnread > 0"
        class="flex h-7 min-w-[28px] items-center justify-center rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 px-2 text-[11px] font-black text-white shadow-[0_6px_18px_rgba(37,99,235,0.28)]"
      >
        {{ totalUnread }}
      </span>
    </div>

    <!-- Search -->
    <div class="group relative px-1">
      <div
        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white p-2 text-slate-400 shadow-sm transition-colors group-focus-within:text-blue-500"
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
        class="w-full rounded-[1.5rem] border border-slate-200/60 bg-white/90 py-3.5 pl-12 pr-10 text-sm font-medium text-slate-800 outline-none transition-all placeholder:text-slate-400 hover:bg-white hover:shadow-sm focus:border-blue-500/20 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
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
      <div class="h-6 w-6 rounded-full border-2 border-slate-300 border-t-blue-500"></div>
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
      class="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center"
    >
      <div class="relative">
        <div class="absolute -inset-4 rounded-full bg-blue-100/50 blur-xl"></div>
        <div
          class="relative grid h-16 w-16 place-items-center rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-xl shadow-blue-200"
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
        <p class="text-base font-bold text-slate-800">Your inbox is empty</p>
        <p class="mt-1 text-xs font-medium text-slate-400">
          Search for friends to start a conversation
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
        <span class="text-[10px] font-black uppercase tracking-[0.15em] text-blue-500"
          >Search Results</span
        >
      </div>

      <div
        v-for="user in displayedUsers"
        :key="user.id"
        class="group relative mx-1 flex cursor-pointer items-center gap-4 rounded-[1.75rem] border border-slate-200/60 bg-white/80 p-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-200/70 hover:bg-white hover:shadow-[0_16px_40px_rgba(59,130,246,0.08)]"
        :class="[
          user.unread_count > 0 && !search ? 'bg-blue-50/60' : '',
          selectedUserId === user.id
            ? '!border-blue-500/20 bg-blue-50/80 shadow-md ring-1 ring-blue-500/10'
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
          class="absolute left-1 top-1/2 h-8 w-1 -translate-y-1/2 rounded-full bg-blue-500"
        ></div>

        <!-- Avatar -->
        <div class="relative flex-shrink-0">
          <img
            :src="getConversationAvatarUrl(user)"
            :alt="`${user.username} avatar`"
            class="relative z-10 h-12 w-12 rounded-[1.25rem] object-cover shadow-lg transition-transform duration-300 group-hover:scale-105"
          />
          <!-- Online/Unread Dot -->
          <div
            v-if="user.unread_count > 0"
            class="absolute -right-1 -top-1 z-20 grid h-5 w-5 place-items-center rounded-full border-2 border-white bg-blue-500 text-[10px] font-black text-white shadow-sm"
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
              class="truncate text-sm font-bold tracking-tight text-slate-900 transition-colors hover:text-blue-600"
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
            <template v-if="user.last_message">
              <span v-if="user.last_message_is_mine" class="opacity-60">You: </span
              >{{ user.last_message }}
            </template>
            <template v-else>Start a conversation</template>
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

<script>
import axiosInstance from '@/services/axiosInstance'
import eventBus from '@/services/eventBus'
import {
  getMessagingConversations,
  getMessagingUsers,
} from '@/services/messagingCompat'
import { mapActions, mapState } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { getAvatarUrl } from '@/utils/avatars'

export default {
  emits: ['selectUser'],
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
      conversations: [],
      allUsers: [],
      search: '',
      loading: false,
      error: '',
      pollTimer: null,
      initialSelectionAttempted: false,
      avatarCache: {},
    }
  },
  computed: {
    ...mapState(useAuthStore, ['currentUser', 'authToken']),
    ...mapState(useProfileStore, ['profilesByUsername']),
    totalUnread() {
      return this.conversations.reduce((sum, u) => sum + (u.unread_count || 0), 0)
    },
    displayedUsers() {
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
    search(val) {
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
  },
  beforeUnmount() {
    this.stopPolling()
    eventBus.off('messaging-read-updated', this.handleMessagingReadUpdated)
  },
  methods: {
    ...mapActions(useProfileStore, ['fetchProfile']),
    handleMessagingReadUpdated() {
      if (this.authToken) {
        this.loadConversations({ silent: true })
      }
    },
    getConversationUsername(user) {
      return user?.username || user?.user?.username || ''
    },

    mergeProfileIntoConversation(user) {
      const username = this.getConversationUsername(user)
      const profile = this.profilesByUsername?.[username]
      const picture = this.getConversationAvatarUrl(user)
      const displayName =
        profile?.display_name ||
        profile?.user?.first_name ||
        user.display_name ||
        user.first_name ||
        user.username ||
        ''

      return {
        ...user,
        picture,
        avatar_url: picture,
        first_name: displayName,
        last_name: profile?.user?.last_name || profile?.last_name || user.last_name || '',
      }
    },

    async ensureProfileLoaded(username) {
      if (!username) return null
      const cached = this.profilesByUsername?.[username]
      if (cached) return cached
      try {
        await this.fetchProfile(username)
        return this.profilesByUsername?.[username] || null
      } catch {
        return null
      }
    },

    timeAgo(isoString) {
      if (!isoString) return ''
      const diff = (Date.now() - new Date(isoString).getTime()) / 1000
      if (diff < 60) return 'now'
      if (diff < 3600) return `${Math.floor(diff / 60)}m`
      if (diff < 86400) return `${Math.floor(diff / 3600)}h`
      if (diff < 604800) return `${Math.floor(diff / 86400)}d`
      return new Date(isoString).toLocaleDateString()
    },
    handleUserClick(user) {
      this.$emit('selectUser', this.mergeProfileIntoConversation(user))
    },
    async loadConversations(opts = {}) {
      if (!this.authToken) return
      if (!opts.silent) {
        this.loading = true
        this.error = ''
      }
      try {
        this.conversations = await getMessagingConversations()
        await this.hydrateConversationProfiles()
        await this.hydrateConversationAvatars()
        this.tryAutoSelectInitialUser()
      } catch (err) {
        if (!opts.silent) this.error = 'Sync failed'
      } finally {
        if (!opts.silent) this.loading = false
      }
    },
    async loadInitialUserByUsername() {
      if (!this.initialUsername || this.initialSelectionAttempted || this.selectedUserId) return
      this.initialSelectionAttempted = true
      try {
        const results = await getMessagingUsers(this.initialUsername)
        const match = (results || []).find((user) => user.username === this.initialUsername)
        if (match) {
          await this.ensureProfileLoaded(match.username)
          this.$emit('selectUser', this.mergeProfileIntoConversation(match))
        }
      } catch {
        // silent
      }
    },
    async searchUsers(query) {
      try {
        const res = await axiosInstance.get('/search/users/', {
          params: { q: query },
        })
        const results = res.data?.results || []
        this.allUsers = results.filter((u) => u.id !== this.currentUser?.id)
      } catch {
        // silent
      }
    },
    async hydrateConversationAvatars() {
      const rows = this.conversations || []
      this.conversations = rows.map((user) => {
        const username = this.getConversationUsername(user)
        const storeProfile = this.profilesByUsername?.[username]
        const profile = this.avatarCache[username]
        const activeProfile = storeProfile || profile
        if (!activeProfile) return user
        return {
          ...user,
          picture: activeProfile.picture || user.picture || '',
          first_name: activeProfile.first_name || user.first_name || '',
          last_name: activeProfile.last_name || user.last_name || '',
        }
      })
    },
    async hydrateConversationProfiles() {
      const rows = this.conversations || []
      await Promise.all(
        rows.map(async (user) => {
          const username = this.getConversationUsername(user)
          if (!username) return
          await this.ensureProfileLoaded(username)
        }),
      )
    },
    getConversationAvatarUrl(user) {
      const username = this.getConversationUsername(user)
      const profile = this.profilesByUsername?.[username] || this.avatarCache[username]
      const picture = profile?.picture || user.picture || ''
      const displayName =
        profile?.display_name ||
        profile?.user?.first_name ||
        user.display_name ||
        user.first_name ||
        user.username ||
        ''
      return getAvatarUrl(
        picture,
        displayName,
        profile?.user?.last_name || profile?.last_name || user.last_name || '',
      )
    },
    moveConversationToTop(userId, lastMessage, isMine = false) {
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
}
</script>

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
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}
</style>
