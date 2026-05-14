<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, nextTick } from 'vue'
import { useNotificationStore } from '@/stores/notification'

import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { formatDistanceToNowStrict } from 'date-fns'
import { getAvatarUrl } from '@/utils/avatars'
import type { Notification } from '@/stores/notification'
import {
  HeartIcon,
  ChatBubbleOvalLeftEllipsisIcon,
  ArrowUturnLeftIcon,
  UserPlusIcon,
  AtSymbolIcon,
  UserGroupIcon,
  CheckBadgeIcon,
  BellIcon,
  CheckCircleIcon,
  LinkIcon,
} from '@heroicons/vue/24/solid'
import eventBus from '@/services/eventBus'

import { useProfileStore } from '@/stores/profile'
const profileStore = useProfileStore()

const notificationStore = useNotificationStore()
const isMarkingAllRead = ref(false)
const loadMoreTrigger = ref<HTMLElement | null>(null)

const nextNotificationPageUrl = computed(() => notificationStore.pagination.next)
useInfiniteScroll(
  loadMoreTrigger,
  () => notificationStore.fetchNotifications(notificationStore.pagination.currentPage + 1),
  nextNotificationPageUrl,
)

const getNotificationLink = (notification: Notification) => {
  if (notification.notification_type === 'group_join_request' && notification.target?.slug) {
    return { name: 'group-requests', params: { slug: notification.target.slug } }
  }
  if (notification.notification_type === 'group_join_approved' && notification.target?.slug) {
    return { name: 'group-detail', params: { slug: notification.target.slug } }
  }
  if (['like', 'comment', 'reply', 'mention'].includes(notification.notification_type)) {
    if (notification.target && notification.target.type.toLowerCase() === 'statuspost') {
      return { name: 'single-post', params: { postId: notification.target.object_id } }
    }
  }
  return { name: 'profile', params: { username: notification.actor.username } }
}

const markOneAsRead = async (notificationId: number) => {
  const notification = notificationStore.notifications.find((n) => n.id === notificationId)
  if (notification && notification.is_read) return
  await notificationStore.markNotificationsAsRead([notificationId])
}

const toast = useToast()

const handleConnectionAction = async (notification: Notification, action: 'accept' | 'reject') => {
  // 1. We need the ID of the connection request.
  // Based on your backend, this is stored in action_object.id
  const requestId = notification.action_object?.id
  if (!requestId) {
    toast.error('Could not find request ID.')
    return
  }

  try {
    // 2. Call your Django API
    await axiosInstance.post(`/connections/requests/${requestId}/${action}/`)

    if (action === 'accept') {
      notification.is_following_back = true
      eventBus.emit('connection-established', notification.actor.id)
    } else {
      // THIS IS NEW: If we decline, set this flag to true
      notification.is_declined = true
    }

    // 3. Mark the notification as read in DB and update local state
    await markOneAsRead(notification.id)
    notification.is_read = true

    // 4. [NEW] Decrease the unread count in the store immediately
    // This ensures the red bubble on the Bell Icon updates instantly
    if (notificationStore.unreadCount > 0) {
      notificationStore.unreadCount--
    }

    // 5. Show success message
    const msg = action === 'accept' ? 'Connection established!' : 'Request declined.'
    // toast.success(msg)
  } catch (error) {
    console.error(`Failed to ${action} connection:`, error)
    toast.error(`Error processing ${action}.`)
  }
}

const handleFollowBack = async (notification: Notification) => {
  try {
    // 1. Send the follow command to the backend
    await profileStore.followUser(notification.actor.username)

    // 2. SMART UI: Update the local state instantly.
    // This triggers the template to hide the button and show the "Connected" badge.
    notification.is_following_back = true
    eventBus.emit('connection-established', notification.actor.id)

    // 3. Mark as read
    await markOneAsRead(notification.id)

    // toast.success(`You are now following ${notification.actor.username}`)
  } catch (error) {
    console.error('Follow back failed:', error)
    toast.error('Could not follow back.')
  }
}

async function handleMarkAllAsRead() {
  if (isMarkingAllRead.value) return
  isMarkingAllRead.value = true
  await notificationStore.markAllAsRead()
  isMarkingAllRead.value = false
}

// Function to get background color based on notification type and read status
const getNotificationBgColor = (notificationType: string, isRead: boolean) => {
  if (isRead) return 'bg-gray-50'

  switch (notificationType) {
    case 'like':
      return 'bg-pink-50'
    case 'comment':
      return 'bg-blue-50'
    case 'connection_request':
      return 'bg-blue-50' // Added
    case 'connection_accepted':
      return 'bg-emerald-50' // Added
    case 'follow':
      return 'bg-green-50'
    case 'mention':
      return 'bg-indigo-50'
    case 'group_join_request':
      return 'bg-purple-50'
    case 'group_join_approved':
      return 'bg-emerald-50'
    default:
      return 'bg-gray-50'
  }
}

const getHoverBgColor = (notificationType: string, isRead: boolean) => {
  if (isRead) return 'hover:bg-gray-100'

  switch (notificationType) {
    case 'like':
      return 'hover:bg-pink-100'
    case 'comment':
      return 'hover:bg-blue-100'
    case 'connection_request':
      return 'hover:bg-blue-100' // Added
    case 'connection_accepted':
      return 'hover:bg-emerald-100' // Added
    case 'follow':
      return 'hover:bg-green-100'
    case 'mention':
      return 'hover:bg-indigo-100'
    case 'group_join_request':
      return 'hover:bg-purple-100'
    case 'group_join_approved':
      return 'hover:bg-emerald-100'
    default:
      return 'hover:bg-gray-100'
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Scroll to top when component is mounted/activated
const scrollToTopOnOpen = () => {
  nextTick(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  })
}

onMounted(() => {
  scrollToTopOnOpen()

  if (!notificationStore.hasLoadedInitialList) {
    notificationStore.fetchNotifications(1)
  }

  eventBus.on('scroll-notifications-to-top', scrollToTop)
})

onUnmounted(() => {
  eventBus.off('scroll-notifications-to-top', scrollToTop)
})
</script>

<template>
  <div class="container mx-auto max-w-3xl">
    <!-- Changed rounded-lg to rounded-2xl here -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-6">
      <!-- Header with Bell Icon -->
      <div class="flex justify-between items-center border-b border-gray-100 pb-4 mb-4">
        <div class="flex items-center gap-3">
          <div class="relative">
            <BellIcon class="w-7 h-7 text-blue-500" />
            <div
              v-if="notificationStore.unreadCount > 0"
              class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center"
            >
              {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
            </div>
          </div>
          <h1 class="text-2xl font-bold text-gray-800">Your Notifications</h1>
        </div>
        <button
          v-if="notificationStore.unreadCount > 0"
          @click="handleMarkAllAsRead"
          :disabled="isMarkingAllRead"
          class="text-sm font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 px-4 py-2 rounded-lg transition disabled:opacity-50 border border-blue-100"
        >
          {{ isMarkingAllRead ? 'Processing...' : 'Mark all as read' }}
        </button>
      </div>

      <div
        v-if="notificationStore.isLoadingList && notificationStore.notifications.length === 0"
        class="text-center py-10"
      >
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"
        ></div>
        <p class="text-gray-500">Loading notifications...</p>
      </div>
      <div
        v-else-if="notificationStore.error"
        class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 rounded"
      >
        <p>{{ notificationStore.error }}</p>
      </div>
      <div
        v-else-if="notificationStore.notifications.length === 0 && !notificationStore.isLoadingList"
        class="text-center py-10 text-gray-500"
      >
        <BellIcon class="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p class="text-lg">You're all caught up!</p>
        <p class="text-sm">No new notifications</p>
      </div>

      <div v-else>
        <ul class="space-y-2">
          <li
            v-for="notification in notificationStore.notifications"
            :key="notification.id"
            class="block"
          >
            <router-link
              :to="getNotificationLink(notification)"
              @click="markOneAsRead(notification.id)"
              class="flex items-start gap-4 p-4 rounded-lg transition-all duration-200 w-full text-left"
              :class="[
                getNotificationBgColor(notification.notification_type, notification.is_read),
                getHoverBgColor(notification.notification_type, notification.is_read),
              ]"
            >
              <!-- Avatar with Icon Badge -->
              <div class="flex-shrink-0 relative">
                <img
                  v-if="notification.actor"
                  :src="
                    getAvatarUrl(
                      notification.actor.picture,
                      notification.actor.first_name,
                      notification.actor.last_name,
                    )
                  "
                  class="w-12 h-12 rounded-full object-cover border-2 border-white shadow-sm"
                  alt=""
                />
                <div
                  class="absolute -bottom-1 -right-1 w-6 h-6 rounded-full border-2 border-white shadow-sm flex items-center justify-center"
                  :class="{
                    'bg-pink-500': notification.notification_type === 'like',
                    'bg-blue-500': ['comment', 'connection_request'].includes(
                      notification.notification_type,
                    ),
                    'bg-gray-500': notification.notification_type === 'reply',
                    'bg-green-500': notification.notification_type === 'follow',
                    'bg-indigo-500': notification.notification_type === 'mention',
                    'bg-purple-500': notification.notification_type === 'group_join_request',
                    'bg-emerald-500': ['group_join_approved', 'connection_accepted'].includes(
                      notification.notification_type,
                    ),
                  }"
                >
                  <!-- 1. Like -->
                  <HeartIcon
                    v-if="notification.notification_type === 'like'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 2. Comment -->
                  <ChatBubbleOvalLeftEllipsisIcon
                    v-else-if="notification.notification_type === 'comment'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 3. Reply -->
                  <ArrowUturnLeftIcon
                    v-else-if="notification.notification_type === 'reply'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 4. Follow (Standard) -->
                  <UserPlusIcon
                    v-else-if="notification.notification_type === 'follow'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 5. Connection Request (New - Link) -->
                  <LinkIcon
                    v-else-if="notification.notification_type === 'connection_request'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 6. Connection Accepted (New - Verified Circle) -->
                  <CheckCircleIcon
                    v-else-if="notification.notification_type === 'connection_accepted'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 7. Mention -->
                  <AtSymbolIcon
                    v-else-if="notification.notification_type === 'mention'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 8. Group Request -->
                  <UserGroupIcon
                    v-else-if="notification.notification_type === 'group_join_request'"
                    class="w-3 h-3 text-white"
                  />

                  <!-- 9. Group Approved -->
                  <CheckBadgeIcon
                    v-else-if="notification.notification_type === 'group_join_approved'"
                    class="w-3 h-3 text-white"
                  />
                </div>
              </div>

              <!-- Content -->
              <div class="flex-grow min-w-0 break-words">
                <div class="flex justify-between items-start mb-1">
                  <strong
                    class="font-semibold text-sm"
                    :class="notification.is_read ? 'text-gray-700' : 'text-gray-900'"
                  >
                    <span v-if="notification.notification_type === 'group_join_approved'"
                      >Group Membership Approved</span
                    >
                    <span v-else>{{ notification.actor.username }}</span>
                  </strong>
                  <!-- Time moved to right corner -->
                  <p class="text-xs text-gray-500 flex-shrink-0">
                    {{
                      formatDistanceToNowStrict(new Date(notification.timestamp), {
                        addSuffix: true,
                      })
                    }}
                  </p>
                </div>

                <div class="mt-1 text-sm text-gray-600">
                  <!-- Case 1: Join Request (for owners) -->
                  <div
                    v-if="
                      notification.notification_type === 'group_join_request' && notification.target
                    "
                  >
                    <span>
                      <strong class="font-semibold text-gray-700">{{
                        notification.actor.username
                      }}</strong>
                      {{ notification.verb }}
                      <strong class="font-semibold text-gray-800">{{
                        notification.target.display_text
                      }}</strong>
                    </span>
                  </div>

                  <!-- Case 2: Join Request APPROVED (for requesters) -->
                  <div
                    v-else-if="
                      notification.notification_type === 'group_join_approved' &&
                      notification.target
                    "
                  >
                    <span>
                      You have been accepted into
                      <strong class="font-semibold text-gray-800">{{
                        notification.target.display_text
                      }}</strong
                      >. Welcome!
                    </span>
                  </div>

                  <!-- Case 3: Connection Request -->
                  <div v-else-if="notification.notification_type === 'connection_request'">
                    <span>
                      <strong class="font-semibold text-gray-800">{{
                        notification.actor.username
                      }}</strong>
                      sent you a connection request.
                    </span>
                  </div>

                  <!-- Case 4: Connection Accepted -->
                  <div v-else-if="notification.notification_type === 'connection_accepted'">
                    <!-- Condition 1: Manual Follow Back -->
                    <span v-if="notification.verb.includes('followed you back')">
                      <strong class="font-semibold text-gray-800">{{
                        notification.actor.username
                      }}</strong>
                      {{ notification.verb }}
                    </span>

                    <!-- Condition 2: Formal Request Accepted -->
                    <span v-else-if="notification.verb.includes('accepted')">
                      <strong class="font-semibold text-gray-800">{{
                        notification.actor.username
                      }}</strong>
                      accepted your connection request.
                    </span>

                    <!-- Condition 3: The person who clicked Accept (Receiver history) -->
                    <span v-else>
                      You are now connected with
                      <strong class="font-semibold text-gray-800">{{
                        notification.actor.username
                      }}</strong
                      >.
                    </span>
                  </div>

                  <!-- Fallback for simple Follows and others -->
                  <div v-else>
                    <span>{{ notification.verb }}</span>
                  </div>
                </div>

                <p
                  v-if="notification.context_snippet"
                  class="mt-2 text-sm text-gray-500 italic break-words bg-white bg-opacity-50 px-2 py-1 rounded border border-gray-100"
                >
                  {{ notification.context_snippet }}
                </p>

                <!-- COMMAND CENTER: Action Buttons -->
                <div class="mt-3">
                  <!-- 1. THE STATUS BADGE: Shown if already connected -->
                  <div
                    v-if="
                      notification.is_following_back &&
                      (notification.notification_type === 'follow' ||
                        notification.notification_type === 'connection_request')
                    "
                    class="flex items-center gap-1.5 text-emerald-600 font-bold text-xs bg-emerald-50 w-fit px-2.5 py-1.5 rounded-lg border border-emerald-100 shadow-sm"
                  >
                    <CheckCircleIcon class="w-4 h-4" />
                    <span>Connected</span>
                  </div>

                  <!-- 2. THE ACTION BUTTONS: Shown if NOT connected yet -->
                  <div v-else-if="!notification.is_declined" class="flex gap-2">
                    <!-- Connection Request Actions -->
                    <template v-if="notification.notification_type === 'connection_request'">
                      <button
                        @click.stop.prevent="handleConnectionAction(notification, 'accept')"
                        class="px-4 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 transition shadow-sm"
                      >
                        Accept
                      </button>
                      <button
                        @click.stop.prevent="handleConnectionAction(notification, 'reject')"
                        class="px-4 py-1.5 bg-gray-200 text-gray-700 text-xs font-bold rounded-lg hover:bg-gray-300 transition"
                      >
                        Decline
                      </button>
                    </template>

                    <!-- Follow Back Actions -->
                    <template v-if="notification.notification_type === 'follow'">
                      <button
                        @click.stop.prevent="handleFollowBack(notification)"
                        class="px-4 py-1.5 bg-purple-600 text-white text-xs font-bold rounded-lg hover:bg-purple-700 transition shadow-sm"
                      >
                        Follow Back
                      </button>
                      <router-link
                        :to="{ name: 'profile', params: { username: notification.actor.username } }"
                        @click.stop
                        class="px-4 py-1.5 border border-gray-300 text-gray-600 text-xs font-bold rounded-lg hover:bg-gray-50 transition"
                      >
                        View Profile
                      </router-link>
                    </template>
                  </div>
                </div>
              </div>

              <!-- Unread indicator - more subtle -->
              <div
                v-if="!notification.is_read"
                class="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 self-center mt-1 animate-pulse"
                title="Unread"
              ></div>
            </router-link>
          </li>
        </ul>

        <div v-if="notificationStore.pagination.next" ref="loadMoreTrigger" class="h-10"></div>
        <div
          v-if="notificationStore.isLoadingList && notificationStore.notifications.length > 0"
          class="text-center py-4 text-gray-500"
        >
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    </div>
  </div>
</template>
