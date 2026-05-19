<template>
  <header class="sticky top-0 z-20 border-b border-slate-200/80 bg-white/80 backdrop-blur-xl">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
      <button
        class="flex flex-col items-start gap-0.5 text-left"
        type="button"
        @click="$router.push(store.token ? '/messages' : '/')"
      >
        <span class="bg-gradient-to-r from-blue-500 to-violet-500 bg-clip-text text-xl font-bold tracking-tight text-transparent">
          ChatFlow
        </span>
        <span class="text-xs text-slate-500">Connect instantly</span>
      </button>

      <div class="flex items-center gap-3">
        <template v-if="!store.token">
          <router-link
            class="rounded-full border border-transparent px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50"
            to="/"
          >
            Login
          </router-link>
          <router-link
            class="rounded-full border border-transparent px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50"
            to="/register"
          >
            Register
          </router-link>
        </template>
        <template v-else>
          <span class="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 text-sm font-medium text-slate-700 ring-1 ring-inset ring-blue-100">
            Hi, {{ store.user?.username || "User" }}
            <span
              v-if="unreadCount"
              class="rounded-full border border-emerald-300 bg-emerald-100 px-2 py-0.5 text-[11px] font-bold text-emerald-700"
            >
              {{ unreadCount }}
            </span>
          </span>
          <button
            class="rounded-full border border-blue-200 bg-gradient-to-r from-blue-100 to-violet-100 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:from-blue-200 hover:to-violet-200"
            type="button"
            @click="logout"
          >
            Logout
          </button>
        </template>
      </div>
    </div>
  </header>
</template>

<script>
import api from "../services/api"
import { store, clearSession } from "../store"

export default {
  data() {
    return {
      store,
      unreadCount: 0,
      pollTimer: null
    }
  },
  mounted() {
    if (this.store.token) {
      this.refreshUnread()
      this.startPolling()
    }
  },
  beforeUnmount() {
    this.stopPolling()
  },
  watch: {
    "store.token"(value) {
      if (value) {
        this.refreshUnread()
        this.startPolling()
      } else {
        this.unreadCount = 0
        this.stopPolling()
      }
    }
  },
  methods: {
    startPolling() {
      this.stopPolling()
      if (!this.store.token) return
      this.pollTimer = setInterval(() => {
        this.refreshUnread()
      }, 5000)
    },
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
    async refreshUnread() {
      if (!this.store.token) return
      try {
        const res = await api.get("messaging/messages/unread-count/")
        this.unreadCount = Number(res.data?.count || 0)
      } catch {
        this.unreadCount = 0
      }
    },
    logout() {
      clearSession()
      this.$router.push("/")
    }
  }
}
</script>
