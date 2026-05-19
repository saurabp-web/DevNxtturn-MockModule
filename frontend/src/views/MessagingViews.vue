<template>
  <div
    class="grid min-h-0 grid-cols-1 gap-4 lg:h-[calc(100vh-160px)] lg:grid-cols-[300px_minmax(0,1fr)_300px] lg:gap-4"
  >
    <ChatSidebar
      :selected-user-id="selectedUser?.id ?? null"
      :initial-username="$route.query.user?.toString() || ''"
      @selectUser="selectUser"
    />
    <ChatWindow :user="selectedUser" />
    <aside class="hidden lg:block">
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
  },
}
</script>
