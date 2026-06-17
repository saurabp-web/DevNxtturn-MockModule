<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useNetworkStore } from '@/stores/network'
import { useProfileStore } from '@/stores/profile'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { Users, UserPlus, UserCheck, Search, MessageSquare, UserCircle } from 'lucide-vue-next'
import { getAvatarUrl } from '@/utils/avatars'
import eventBus from '@/services/eventBus'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { onMounted } from 'vue' // Ensure onMounted is imported from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { XMarkIcon } from '@heroicons/vue/24/solid' // Ensure this is also here for your Decline feedback

// 1. Setup the store we created yesterday
const networkStore = useNetworkStore()
const profileStore = useProfileStore()
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const { followers, following, connections, pending, isLoading, error } = storeToRefs(networkStore)
const { currentUser, isAuthenticated } = storeToRefs(authStore)
const route = useRoute()
const router = useRouter()

// 2. State for Tabs and Search (Added 'pending')
const activeTab = ref<'connections' | 'followers' | 'following' | 'pending' | 'discovery'>(
  'connections',
)
const searchQuery = ref('')
const successfulConnections = ref<Set<number>>(new Set())
const successfulDeclines = ref<Set<number>>(new Set())
const successfulCancels = ref<Set<number>>(new Set())

// --- INFINITE SCROLL LOGIC ---

// 1. The sensor element at the bottom of the page
const loadMoreTrigger = ref<HTMLElement | null>(null)

// 2. The "Compass": Tells the scroll utility which URL to fetch next based on the current tab
// --- REPLACE THIS BLOCK ---
const nextCursorUrl = computed(() => {
  // 1. Create a local reference
  const urls = networkStore.nextUrls

  // 2. SAFETY CHECK: If urls is undefined, stop here and return null (Prevents Crash)
  if (!urls) return null

  // 3. If urls exists, find the correct link
  if (activeTab.value === 'connections') return urls.connections
  if (activeTab.value === 'followers') return urls.followers
  if (activeTab.value === 'following') return urls.following
  if (activeTab.value === 'pending') return urls.pending

  return null
})

// 3. The "Engine": Runs the fetch function when the user reaches the bottom
useInfiniteScroll(
  loadMoreTrigger,
  async () => {
    if (activeTab.value === 'connections') await networkStore.fetchConnections(nextCursorUrl.value)
    else if (activeTab.value === 'followers') await networkStore.fetchFollowers(nextCursorUrl.value)
    else if (activeTab.value === 'following') await networkStore.fetchFollowing(nextCursorUrl.value)
    else if (activeTab.value === 'pending') await networkStore.fetchPending(nextCursorUrl.value)
  },
  nextCursorUrl,
)

const fetchData = async () => {
  // GUARD: If the store didn't load, stop here.
  if (!networkStore) return

  if (activeTab.value === 'connections') {
    const filter = route.query.filter as string
    const targetUser = route.query.username as string

    // THE MUTUAL FILTER HANDSHAKE:
    // If the URL has ?filter=mutual, fetch shared connections using our new backend view!
    if (filter === 'mutual' && targetUser) {
      await networkStore.fetchMutualConnections(targetUser)
    } else {
      await networkStore.fetchConnections()
    }
  } else if (activeTab.value === 'followers') {
    await networkStore.fetchFollowers()
  } else if (activeTab.value === 'following') {
    await networkStore.fetchFollowing()
  } else if (activeTab.value === 'pending') {
    await networkStore.fetchPending()
    // PRINT THE EXACT DATA COMING FROM THE SERVER:
    console.log('👥 LIVE SERVER PENDING DATA:', JSON.parse(JSON.stringify(networkStore.pending)))
  } else if (activeTab.value === 'discovery') {
    await networkStore.fetchDiscover()
  }
}

// 4. Filter the list based on the search bar
const filteredList = computed(() => {
  // If we are on the discovery tab, hide the old flat list
  if (activeTab.value === 'discovery') return []

  const list =
    activeTab.value === 'connections'
      ? connections.value
      : activeTab.value === 'followers'
        ? followers.value
        : activeTab.value === 'following'
          ? following.value
          : pending.value

  if (!searchQuery.value) return list

  return list.filter(
    (user) =>
      user.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      user.username.toLowerCase().includes(searchQuery.value.toLowerCase()),
  )
})

// --- GLOBAL SYNC HANDLERS ---

const handleAccept = async (user: any) => {
  if (successfulConnections.value.has(user.id)) return // Prevent double-clicks

  try {
    // 1. Update the Database
    await profileStore.acceptConnectRequest(user.username)

    // 2. SHOW FEEDBACK: Add to successful set
    successfulConnections.value.add(user.id)

    // 3. WAIT 1.5 SECONDS (UX satisfy delay)
    setTimeout(async () => {
      // 4. SYNC EVERYTHING ELSE
      notificationStore.forceSyncConnection(user.id)

      // Refresh the Network Hub lists (moves user between tabs)
      await networkStore.fetchPending()
      await networkStore.fetchConnections()

      await profileStore.fetchProfile(authStore.currentUser?.username || '')

      // Broadcast to Sidebar
      eventBus.emit('connection-established', user.id)

      // Cleanup the feedback state
      successfulConnections.value.delete(user.id)

      console.log('✅ NetworkHub: Delayed sync complete for', user.username)
    }, 1500)
  } catch (err) {
    console.error('NetworkHub: Failed to accept', err)
  }
}

const handleDecline = async (user: any) => {
  if (successfulDeclines.value.has(user.id)) return

  try {
    await profileStore.rejectConnectRequest(user.username)
    successfulDeclines.value.add(user.id)

    setTimeout(async () => {
      notificationStore.forceSyncConnection(user.id)
      await networkStore.fetchPending()

      // --- ADD THIS LINE: Sync sidebar stats ---
      await profileStore.fetchProfile(authStore.currentUser?.username || '')

      successfulDeclines.value.delete(user.id)
    }, 1500)
  } catch (err) {
    console.error('NetworkHub: Failed to decline', err)
    successfulDeclines.value.delete(user.id)
  }
}

const handleCancel = async (user: any) => {
  if (successfulCancels.value.has(user.id)) return

  try {
    // 1. Update Database
    await profileStore.cancelConnectRequest(user.username)

    // 2. Show local feedback immediately
    successfulCancels.value.add(user.id)

    // 3. Professional Delay (1.5s)
    setTimeout(async () => {
      // 4. Sync Notification Bar & Pending Tab
      notificationStore.forceSyncConnection(user.id)
      await networkStore.fetchPending()

      // 5. Refresh sidebar stats (Following count decreases)
      await profileStore.fetchProfile(authStore.currentUser?.username || '')

      // 6. Cleanup feedback state
      successfulCancels.value.delete(user.id)
      console.log('✅ NetworkHub: Cancel sync complete for', user.username)
    }, 1500)
  } catch (err) {
    console.error('NetworkHub: Failed to cancel', err)
    successfulCancels.value.delete(user.id)
  }
}

const handleMessage = (user: any) => {
  router.push({ name: 'messages', query: { user: user.username } })
}

// Watch for tab changes, authentication, and user load
watch(
  [activeTab, isAuthenticated, currentUser],
  async ([newTab, isAuth, user]) => {
    console.log(
      '🔍 [NetworkView Watcher] Tab:',
      newTab,
      '| Auth:',
      isAuth,
      '| User:',
      user ? user.username : 'null',
    )

    if (isAuth && user) {
      await fetchData()
    }
  },
  { immediate: true },
)

// --- THE DISCOVERY CATEGORIES GENERATOR ---
// This groups your 4 backend categories into a clean, loopable array
const discoveryCategories = computed(() => {
  if (!networkStore.discoverResults) return []
  return [
    {
      title: 'Mutual Connections',
      key: 'mutual_connections',
      list: networkStore.discoverResults.mutual_connections,
    },
    { title: 'Alumni from your school', key: 'alumni', list: networkStore.discoverResults.alumni },
    {
      title: 'People with Similar Skills',
      key: 'similar_skills',
      list: networkStore.discoverResults.similar_skills,
    },
    {
      title: 'Local Professionals near you',
      key: 'local_professionals',
      list: networkStore.discoverResults.local_professionals,
    },
  ].filter((category) => category.list && category.list.length > 0)
})

// --- THE DISCOVERY CONNECT HANDLER ---
const successfulConnects = ref<Set<number>>(new Set())

const handleConnect = async (user: any) => {
  if (successfulConnects.value.has(user.id)) return // Prevent double-clicks

  try {
    // 1. Send the connection request to the server
    await profileStore.sendConnectRequestById(user.id)

    // 2. SHOW FEEDBACK: Add to successful connects
    successfulConnects.value.add(user.id)

    // 3. WAIT 1.5 SECONDS (UX satisfy delay)
    setTimeout(async () => {
      // Sync notifications and refresh the pending tab list
      notificationStore.forceSyncConnection(user.id)
      await networkStore.fetchPending()

      // Smoothly erase this person from the suggestion cards in-place
      networkStore.forceSyncConnection(user.id)

      // Cleanup feedback state
      successfulConnects.value.delete(user.id)
      console.log('✅ NetworkHub: Discovery connect complete for', user.username)
    }, 1500)
  } catch (err) {
    console.error('NetworkHub: Failed to connect', err)
  }
}

const handleTabClick = (
  tab: 'connections' | 'followers' | 'following' | 'pending' | 'discovery',
) => {
  activeTab.value = tab

  // Keep the target username in the URL across all tabs so we don't lose the context!
  if (route.query.username) {
    router.replace({
      name: 'network',
      query: {
        tab,
        username: route.query.username,
      },
    })
  }
}

// --- DEEP LINKING LOGIC ---
onMounted(() => {
  // 1. Get the 'tab' from the URL: /network?tab=followers
  const requestedTab = route.query.tab as string

  // 2. Define our allowed tabs
  const validTabs = ['connections', 'followers', 'following', 'pending', 'discovery']

  // 3. If the URL says a specific tab, switch to it immediately
  if (requestedTab && validTabs.includes(requestedTab)) {
    activeTab.value = requestedTab as any
    console.log('🔗 Deep Link: Switching to tab:', requestedTab)
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Main Container Card -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      <!-- Header with Title and Search -->
      <div class="p-6 border-b border-gray-100">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h1 class="text-2xl font-bold text-gray-900">
            {{
              activeTab === 'connections'
                ? route.query.filter === 'mutual'
                  ? `Mutual Connections with @${route.query.username}`
                  : 'Your Connections'
                : activeTab === 'followers'
                  ? 'Your Followers'
                  : activeTab === 'following'
                    ? 'Following'
                    : activeTab === 'pending'
                      ? 'Pending Requests'
                      : 'Discovery'
            }}
          </h1>

          <!-- Search Bar -->
          <div class="relative group">
            <Search
              class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors"
            />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search people..."
              class="pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm w-full md:w-64 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
            />
          </div>
        </div>

        <!-- Tab Buttons -->
        <div class="flex gap-1 mt-6 p-1 bg-gray-100/50 rounded-xl w-full max-w-2xl">
          <button
            v-for="tab in [
              'connections',
              'followers',
              'following',
              'pending',
              'discovery',
            ] as const"
            :key="tab"
            @click="handleTabClick(tab)"
            :class="[
              'flex-1 text-center px-1.5 sm:px-4 py-2 text-[9.5px] sm:text-xs font-bold uppercase tracking-wider rounded-lg transition-all whitespace-nowrap',
              activeTab === tab
                ? 'bg-white text-blue-600 shadow-sm border border-gray-200'
                : 'text-gray-500 hover:text-gray-700',
            ]"
          >
            {{ tab }}
          </button>
        </div>

        <!-- The Sub-Pill Toggle (Only visible under Connections when a target username is present) -->
        <div
          v-if="activeTab === 'connections' && route.query.username"
          class="mt-4 flex gap-2 px-1 animate-fadeIn"
        >
          <!-- Button 1: All Connections -->
          <button
            @click="
              router.replace({
                name: 'network',
                query: { tab: 'connections', username: route.query.username },
              })
            "
            :class="[
              'px-4 py-1.5 text-xs font-bold rounded-lg border transition-all duration-200 shadow-sm',
              route.query.filter !== 'mutual'
                ? 'bg-blue-50 text-blue-600 border-blue-200'
                : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50',
            ]"
          >
            All Connections
          </button>

          <!-- Button 2: Mutual Connections -->
          <button
            @click="
              router.replace({
                name: 'network',
                query: { tab: 'connections', filter: 'mutual', username: route.query.username },
              })
            "
            :class="[
              'px-4 py-1.5 text-xs font-bold rounded-lg border transition-all duration-200 shadow-sm',
              route.query.filter === 'mutual'
                ? 'bg-blue-50 text-blue-600 border-blue-200'
                : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50',
            ]"
          >
            👥 Mutual with @{{ route.query.username }}
          </button>
        </div>
      </div>

      <!-- List of Users -->
      <div class="min-h-[500px] relative">
        <!-- Loading Spinner -->
        <div
          v-if="isLoading"
          class="absolute inset-0 flex justify-center items-center bg-white/60 z-10 backdrop-blur-[1px]"
        >
          <div
            class="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"
          ></div>
        </div>

        <!-- Empty State -->
        <div
          v-if="filteredList.length === 0 && activeTab !== 'discovery' && !isLoading"
          class="flex flex-col items-center justify-center py-24 text-gray-400 text-center"
        >
          <Users class="w-12 h-12 opacity-10 mb-4" />
          <p class="text-lg font-medium text-gray-900">No one found</p>
          <p class="text-sm">Try searching for someone else or check another tab.</p>
        </div>

        <!-- Discovery Empty State (If there are no suggestions at all) -->
        <div
          v-if="activeTab === 'discovery' && discoveryCategories.length === 0 && !isLoading"
          class="flex flex-col items-center justify-center py-24 text-gray-400 text-center"
        >
          <Users class="w-12 h-12 opacity-10 mb-4" />
          <p class="text-lg font-medium text-gray-900">You're all connected!</p>
          <p class="text-sm">
            You have connected with everyone in our recommendations. Check back later!
          </p>
        </div>

        <!-- User Rows -->
        <div
          v-if="activeTab !== 'discovery' && filteredList.length > 0"
          class="divide-y divide-gray-100 px-2"
        >
          <div
            v-for="user in filteredList"
            :key="user.id"
            class="group flex items-center justify-between p-4 hover:bg-blue-50/30 transition-colors rounded-xl"
          >
            <div class="flex items-center gap-4">
              <img
                :src="getAvatarUrl(user.picture, user.name, '')"
                class="w-14 h-14 rounded-2xl object-cover border border-gray-100 shadow-sm"
                alt=""
              />
              <div class="min-w-0">
                <RouterLink
                  :to="`/profile/${user.username}`"
                  class="text-base font-bold text-gray-900 hover:text-blue-600 transition-colors block"
                >
                  {{ user.name }}
                </RouterLink>
                <p class="text-xs text-gray-500 truncate max-w-[200px]">
                  {{ user.headline || 'Member at nxtturn' }}
                </p>
                <p class="text-[10px] font-mono text-gray-400">@{{ user.username }}</p>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <!-- 1. ALWAYS show the Message Button (Standard across all tabs) -->
              <button
                @click="handleMessage(user)"
                class="p-2.5 text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all"
                title="Message"
              >
                <MessageSquare class="w-5 h-5" />
              </button>

              <!-- 2. TAB-SPECIFIC ACTIONS (Accept/Decline/Pending) -->
              <template v-if="activeTab === 'pending'">
                <template
                  v-if="
                    user.connection_status === 'pending_received' ||
                    user.connection_status === 'none'
                  "
                >
                  <div class="flex gap-2">
                    <!-- Accept Button -->
                    <button
                      @click="handleAccept(user)"
                      :disabled="successfulConnections.has(user.id)"
                      class="px-4 py-1.5 text-xs font-bold rounded-lg transition-all shadow-sm border min-w-[100px]"
                      :class="[
                        successfulConnections.has(user.id)
                          ? 'bg-green-600 text-white border-green-700'
                          : 'bg-green-50 text-green-600 border-green-200 hover:bg-green-100',
                      ]"
                    >
                      <span v-if="successfulConnections.has(user.id)">Connected ✓</span>
                      <span v-else>Accept</span>
                    </button>

                    <!-- Decline Button -->
                    <button
                      v-if="!successfulConnections.has(user.id) && !successfulDeclines.has(user.id)"
                      @click="handleDecline(user)"
                      class="px-3 py-1.5 bg-gray-50 text-gray-500 text-xs font-bold rounded-lg hover:bg-gray-100 border border-gray-200 transition"
                    >
                      Decline
                    </button>

                    <!-- Declined Feedback -->
                    <div
                      v-if="successfulDeclines.has(user.id)"
                      class="px-4 py-1.5 bg-gray-100 text-gray-500 text-xs font-bold rounded-lg border border-gray-200 shadow-sm flex items-center gap-1"
                    >
                      <XMarkIcon class="w-3 h-3" />
                      <span>Declined</span>
                    </div>
                  </div>
                </template>

                <!-- Outgoing Case: Hover to Cancel -->
                <!-- CASE: Sent Request (Cancel) -->
                <template v-else-if="user.connection_status === 'pending_sent'">
                  <!-- 1. Feedback Badge: Shown for 1.5s after clicking -->
                  <div
                    v-if="successfulCancels.has(user.id)"
                    class="px-4 py-1.5 bg-gray-100 text-gray-500 text-xs font-bold rounded-lg border border-gray-200 shadow-sm flex items-center gap-1"
                  >
                    <XMarkIcon class="w-3 h-3" />
                    <span>Cancelled</span>
                  </div>

                  <!-- 2. Interactive Button: Shown by default -->
                  <button
                    v-else
                    @click="handleCancel(user)"
                    class="px-4 py-1.5 bg-gray-100 text-gray-500 text-xs font-bold rounded-lg hover:bg-red-50 hover:text-red-600 border border-gray-200 transition group/cancel"
                  >
                    <span class="group-hover/cancel:hidden">Pending</span>
                    <span class="hidden group-hover/cancel:inline">Cancel</span>
                  </button>
                </template>
              </template>

              <!-- 3. ALWAYS show the Profile Link -->
              <RouterLink
                :to="`/profile/${user.username}`"
                class="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all"
              >
                <UserCircle class="w-5 h-5" />
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- NEW: DISCOVERY CATEGORIES (Only shown on 'discovery' tab) -->
        <div v-if="activeTab === 'discovery' && !isLoading" class="divide-y divide-gray-100 px-2">
          <!-- Loop through each of our 4 categories -->
          <div v-for="category in discoveryCategories" :key="category.key" class="py-6 first:pt-3">
            <h2 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 px-2">
              {{ category.title }}
            </h2>

            <div class="space-y-2">
              <div
                v-for="user in category.list"
                :key="user.id"
                class="group flex items-center justify-between p-4 hover:bg-blue-50/30 transition-colors rounded-xl"
              >
                <!-- Avatar & Details -->
                <div class="flex items-center gap-4">
                  <img
                    :src="getAvatarUrl(user.picture, user.name, '')"
                    class="w-14 h-14 rounded-2xl object-cover border border-gray-100 shadow-sm"
                    alt=""
                  />
                  <div class="min-w-0">
                    <RouterLink
                      :to="`/profile/${user.username}`"
                      class="text-base font-bold text-gray-900 hover:text-blue-600 transition-colors block"
                    >
                      {{ user.name }}
                    </RouterLink>
                    <p class="text-xs text-gray-500 truncate max-w-[200px]">
                      {{ user.headline || 'Member at nxtturn' }}
                    </p>
                    <p class="text-[10px] font-mono text-gray-400">@{{ user.username }}</p>
                  </div>
                </div>

                <!-- Actions (Standard Message, Custom Connect, Profile Link) -->
                <div class="flex items-center gap-2">
                  <button
                    @click="handleMessage(user)"
                    class="p-2.5 text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-all"
                    title="Message"
                  >
                    <MessageSquare class="w-5 h-5" />
                  </button>

                  <!-- Connect / Sent Button -->
                  <div class="flex gap-2">
                    <button
                      @click="handleConnect(user)"
                      :disabled="successfulConnects.has(user.id)"
                      class="px-4 py-1.5 text-xs font-bold rounded-lg transition-all shadow-sm border min-w-[100px]"
                      :class="[
                        successfulConnects.has(user.id)
                          ? 'bg-blue-600 text-white border-blue-700'
                          : 'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100',
                      ]"
                    >
                      <span v-if="successfulConnects.has(user.id)">Sent ✓</span>
                      <span v-else>Connect</span>
                    </button>
                  </div>

                  <RouterLink
                    :to="`/profile/${user.username}`"
                    class="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all"
                  >
                    <UserCircle class="w-5 h-5" />
                  </RouterLink>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="nextCursorUrl && activeTab !== 'discovery'"
          ref="loadMoreTrigger"
          class="py-10 flex justify-center"
        >
          <div
            class="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
