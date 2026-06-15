<template>
  <div
    class="grid h-[calc(100dvh-8.5rem)] min-h-0 overflow-hidden grid-cols-1 gap-3 lg:h-[calc(100dvh-96px)] lg:grid-cols-[300px_minmax(0,1fr)_300px] lg:items-stretch lg:gap-4"
  >
    <div class="min-h-0 h-full overflow-hidden " :class="selectedUser ? 'hidden lg:block' : 'block'">
      <ChatSidebar
        :selected-user-id="selectedUser?.id ?? null"
        :initial-username="$route.query.user?.toString() || ''"
        @selectUser="selectUser"
      />
    </div>

    <div class="min-h-0 h-full overflow-hidden" :class="selectedUser ? 'block' : 'hidden lg:block'">
      <ChatWindow
        :key="selectedUser?.id ?? 'empty'"
        :user="selectedUser"
        :show-mobile-back="Boolean(selectedUser)"
        @back="goBackToList"
      />
    </div>

    <aside class="hidden lg:block min-h-0 h-full overflow-hidden">
      <RightSidebar />
    </aside>
  </div>
</template>

<script>
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatWindow from '../components/chat/ChatWindow.vue'
import RightSidebar from '@/components/layout/RightSidebar.vue'

export default {
  components: { ChatSidebar, ChatWindow, RightSidebar },
  data() {
    return {
      selectedUser: null,
    }
  },
  methods: {
    selectUser(user) {
      this.selectedUser = user
      this.$router.replace({
        name: 'messages',
        query: user?.username ? { user: user.username } : {},
      })
    },
    goBackToList() {
      this.selectedUser = null
      this.$router.replace({
        name: 'messages',
      })
    },
  },
}
</script>
