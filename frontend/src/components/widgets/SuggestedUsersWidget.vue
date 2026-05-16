<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useNetworkStore } from '@/stores/network'
import { useProfileStore } from '@/stores/profile'
import { useNotificationStore } from '@/stores/notification'
import { storeToRefs } from 'pinia'
import type { NetworkUser } from '@/types'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'
import eventBus from '@/services/eventBus'
import { getAvatarUrl } from '@/utils/avatars'
// Import the site-wide SVG illustration
import defaultAvatar from '@/assets/images/default-avatar.svg'

// 1. Setup Stores
const networkStore = useNetworkStore()
const profileStore = useProfileStore()
const notificationStore = useNotificationStore()
const { discoverResults, isLoading } = storeToRefs(networkStore)

// 2. Local State for "Pending" status (Optimistic UI)
const pendingRequests = ref<Set<number>>(new Set())
const successfulConnections = ref<Set<number>>(new Set())

// 3. Fetch discovery data
const handleRefresh = () => {
  networkStore.fetchDiscover()
}

onMounted(() => {
  networkStore.fetchDiscover()

  // SMART SYNC: Listen for connections made anywhere else in the app
  eventBus.on('connection-established', (userId: number) => {
    // 1. Instantly clean this user out of the Store's memory (All buckets)
    networkStore.forceSyncConnection(userId)

    // 2. Instantly clean this user out of the Notification Bar (if active)
    notificationStore.forceSyncConnection(userId)

    console.log('🔄 Widget: Local memory scrubbed for User ID:', userId)
  })
})

onUnmounted(() => {
  eventBus.off('connection-established')
})

// 4. Algorithm to pick the first "best" category to show
const suggestionCategory = computed(() => {
  if (!discoverResults.value) return null

  const categories = [
    { key: 'mutual_connections', title: 'People You May Know' },
    { key: 'alumni', title: 'Fellow Alumni' },
    { key: 'similar_skills', title: 'Based On Your Skills' },
    { key: 'local_professionals', title: 'In Your Area' },
  ] as const

  for (const cat of categories) {
    const users = discoverResults.value[cat.key as keyof typeof discoverResults.value]
    if (users && users.length > 0) {
      return {
        title: cat.title,
        users: users.slice(0, 3),
      }
    }
  }
  return null
})

function getCategoryTitle(key: string): string {
  switch (key) {
    case 'mutual_connections':
      return 'People You May Know'
    case 'alumni':
      return 'Fellow Alumni'
    case 'similar_skills':
      return 'Based On Your Skills'
    case 'local_professionals':
      return 'In Your Area'
    default:
      return 'Suggestions'
  }
}

async function handleConnect(user: NetworkUser) {
  if (pendingRequests.value.has(user.id) || successfulConnections.value.has(user.id)) return

  pendingRequests.value.add(user.id)

  try {
    const response = await profileStore.sendConnectRequestById(user.id)

    // IF SUCCESSFUL CONNECTION (Follow-back or Smart Resolve)
    if (response && response.status === 'connected') {
      // 1. Switch from 'Pending' to 'Success' state
      pendingRequests.value.delete(user.id)
      successfulConnections.value.add(user.id)

      // 2. DELAYED CLEANUP: Wait 1.5 seconds so user sees "Connected"
      setTimeout(() => {
        // Sync Notification Bar instantly
        notificationStore.forceSyncConnection(user.id)

        // Remove from Sidebar list
        networkStore.forceSyncConnection(user.id)

        // Remove from local feedback tracker
        successfulConnections.value.delete(user.id)

        eventBus.emit('connection-established', user.id)
      }, 1500)
    } else {
      // If it was just a standard request sent (not a mutual connection yet)
      // Keep it in pendingRequests so the button stays "Pending"
    }
  } catch (error) {
    pendingRequests.value.delete(user.id)
    console.error('Connection failed:', error)
  }
}
</script>

<template>
  <div
    class="bg-gradient-to-br from-white to-gray-50 p-5 rounded-2xl border border-gray-200 shadow-sm min-h-[100px]"
  >
    <!-- Header Area -->
    <div class="flex items-start justify-between mb-4">
      <div class="flex items-start gap-2">
        <!-- Decorative Bar -->
        <div
          class="w-1 self-stretch bg-gradient-to-b from-blue-500 to-purple-500 rounded-full my-0.5"
        ></div>

        <div class="flex flex-col justify-center">
          <h3 class="font-bold text-gray-800 text-lg leading-tight">People You May Know</h3>
          <p
            v-if="suggestionCategory && suggestionCategory.title !== 'People You May Know'"
            class="text-[10px] font-bold text-blue-600 uppercase tracking-wider mt-0.5"
          >
            {{ suggestionCategory.title }}
          </p>
        </div>
      </div>

      <!-- Manual Refresh Button -->
      <button
        @click="handleRefresh"
        :disabled="isLoading"
        class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-all"
        title="Refresh suggestions"
      >
        <ArrowPathIcon :class="['w-5 h-5', isLoading ? 'animate-spin text-blue-600' : '']" />
      </button>
    </div>

    <!-- 1. Loading State (Skeleton) -->
    <div v-if="isLoading && !suggestionCategory" class="space-y-4">
      <div v-for="i in 3" :key="i" class="flex items-center gap-3 py-2">
        <div class="w-10 h-10 rounded-full bg-gray-200 animate-pulse"></div>
        <div class="flex-1 space-y-2">
          <div class="h-3 w-24 bg-gray-200 rounded animate-pulse"></div>
          <div class="h-2 w-16 bg-gray-100 rounded animate-pulse"></div>
        </div>
      </div>
    </div>

    <!-- 2. Real Content -->
    <div v-else-if="suggestionCategory && suggestionCategory.users.length > 0">
      <ul class="space-y-4">
        <li
          v-for="user in suggestionCategory.users"
          :key="user.id"
          class="flex items-center p-2 hover:bg-gray-50 rounded-xl transition-colors duration-200 group"
        >
          <!-- Clickable Avatar and Info -->
          <RouterLink :to="`/profile/${user.username}`" class="flex items-center flex-1 min-w-0">
            <img
              :src="getAvatarUrl(user.picture, user.name || user.username, '')"
              class="h-10 w-10 rounded-full ring-2 ring-white shadow-sm flex-shrink-0 mr-3 object-cover bg-white group-hover:ring-blue-100 transition-all"
              alt=""
            />

            <div class="flex-1 min-w-0 mr-3">
              <p
                class="font-semibold text-gray-800 text-sm truncate group-hover:text-blue-600 transition-colors"
              >
                {{ user.name }}
              </p>
              <p class="text-xs text-gray-500 truncate">{{ user.headline || 'NxtTurn Member' }}</p>
            </div>
          </RouterLink>

          <!-- Dynamic Connect/Follow Back Button -->
          <button
            @click="handleConnect(user)"
            :disabled="pendingRequests.has(user.id) || successfulConnections.has(user.id)"
            class="flex-shrink-0 text-xs font-bold px-3 py-1.5 rounded-lg transition-all shadow-sm border"
            :class="[
              // 1. Success State (Green)
              successfulConnections.has(user.id)
                ? 'bg-green-600 text-white border-green-700'
                : // 2. Loading/Pending State (Gray)
                  pendingRequests.has(user.id)
                  ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                  : // 3. Follow Back State (Emerald)
                    user.connection_status === 'follows_you'
                    ? 'bg-emerald-50 text-emerald-600 border-emerald-200 hover:bg-emerald-100'
                    : // 4. Accept State (Green)
                      user.connection_status === 'pending_received'
                      ? 'bg-green-600 text-white border-green-700 hover:bg-green-700'
                      : // 5. Default Connect State (Blue)
                        'bg-blue-50 text-blue-600 border-blue-200 hover:bg-blue-100',
            ]"
          >
            <!-- Label Logic -->
            <span v-if="successfulConnections.has(user.id)">Connected ✓</span>
            <span v-else-if="pendingRequests.has(user.id)">
              {{ user.connection_status === 'pending_received' ? 'Accepting...' : 'Pending' }}
            </span>
            <span v-else-if="user.connection_status === 'pending_received'">Accept</span>
            <span v-else-if="user.connection_status === 'follows_you'">Follow Back</span>
            <span v-else>Connect</span>
          </button>
        </li>
      </ul>

      <div class="mt-3 pt-3 border-t border-gray-100">
        <RouterLink
          to="/network"
          class="block w-full text-center text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 py-2 rounded-xl transition-colors duration-200"
        >
          Show more suggestions
        </RouterLink>
      </div>
    </div>

    <!-- 3. Fallback -->
    <div v-else class="py-6 text-center">
      <p class="text-xs text-gray-400 leading-relaxed">
        Complete your profile to get personalized recommendations!
      </p>
    </div>
  </div>
</template>
