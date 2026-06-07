<script setup lang="ts">
import { useProfileStore } from '@/stores/profile'
import { useNotificationStore } from '@/stores/notification'
import { useNetworkStore } from '@/stores/network'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import eventBus from '@/services/eventBus'

// Import filled icons from Heroicons
import { ClockIcon } from '@heroicons/vue/24/outline'
import {
  HeartIcon as HeartIconSolid,
  CheckBadgeIcon,
  UserGroupIcon as UserGroupIconSolid,
  ChatBubbleLeftRightIcon as ChatBubbleLeftRightIconSolid,
  LinkIcon as LinkIconSolid,
  HandThumbDownIcon as HandThumbDownIconSolid,
  ArrowPathIcon,
  XMarkIcon,
} from '@heroicons/vue/24/solid'

const profileStore = useProfileStore()
const notificationStore = useNotificationStore()
const networkStore = useNetworkStore()
const authStore = useAuthStore()
const { relationshipStatus, currentProfile, isLoadingFollow } = storeToRefs(profileStore)

const showDisconnectConfirm = ref(false)
const isHovering = ref({
  connect: false,
  follow: false,
  message: false,
  disconnect: false,
})

// --- NEW: DYNAMIC BUTTON LOGIC ---

// 1. Decides the text based on Hover and Relationship
const followButtonLabel = computed(() => {
  const status = relationshipStatus.value
  if (!status) return 'Follow'

  // CASE: You already follow them
  if (status.is_followed_by_request_user) {
    return isHovering.value.follow ? 'Unfollow' : 'Following'
  }

  // CASE: They follow you, but you don't follow back (The Follow-Back Invitation)
  if (status.is_following_viewer) {
    return isHovering.value.follow ? 'Follow Back' : 'Following'
  }

  // CASE: Standard (Stranger)
  return 'Follow'
})

// 2. Decides the colors based on the relationship
const followButtonClasses = computed(() => {
  const status = relationshipStatus.value
  if (!status)
    return {
      ring: 'bg-purple-50 border-purple-200',
      icon: 'text-purple-500',
      text: 'text-purple-600',
    }

  // IF YOU FOLLOW THEM: Use the Rose/Red "Unfollow" theme
  if (status.is_followed_by_request_user) {
    return {
      ring: isHovering.value.follow
        ? 'bg-red-100 border-red-300 shadow-sm shadow-red-100 scale-105'
        : 'bg-rose-50 border-rose-200',
      icon: isHovering.value.follow ? 'text-red-600' : 'text-rose-500',
      text: isHovering.value.follow ? 'text-red-600' : 'text-rose-600',
    }
  }

  // IF THEY FOLLOW YOU: Use the Emerald "Positive/Follow-Back" theme
  if (status.is_following_viewer) {
    return {
      ring: isHovering.value.follow
        ? 'bg-emerald-100 border-emerald-300 shadow-sm shadow-emerald-100 scale-105'
        : 'bg-emerald-50 border-emerald-200',
      icon: isHovering.value.follow ? 'text-emerald-600' : 'text-emerald-500',
      text: isHovering.value.follow ? 'text-emerald-600' : 'text-emerald-600',
    }
  }

  // STANDARD FOLLOW: Use the default Purple theme
  return {
    ring: isHovering.value.follow
      ? 'bg-purple-100 border-purple-300 shadow-sm shadow-purple-100 scale-105'
      : 'bg-purple-50 border-purple-200',
    icon: isHovering.value.follow ? 'text-purple-600' : 'text-purple-500',
    text: isHovering.value.follow ? 'text-purple-600' : 'text-purple-600',
  }
})

const followIcon = computed(() => {
  return relationshipStatus.value?.is_followed_by_request_user ? HeartIconSolid : HeartIconSolid
})

// Dynamically calculates if the viewer is authorized to send a message [4]
const canMessage = computed(() => {
  const status = relationshipStatus.value
  const visibility = (currentProfile.value as any)?.message_visibility || 'members'

  // 1. You cannot message yourself
  if (status?.connection_status === 'self') return false

  // 2. 'self' means fully private - nobody can message
  if (visibility === 'self') return false

  // 3. 'public' or 'members' means any logged-in user can message
  if (visibility === 'public' || visibility === 'members') return true

  // 4. 'followers' means the viewer must follow the owner
  if (visibility === 'followers') {
    return status?.is_followed_by_request_user || false
  }

  // 5. 'connections' means they must be mutual connections [4]
  if (visibility === 'connections') {
    return status?.connection_status === 'connected'
  }

  return false
})

const handleConnect = (event: MouseEvent) => {
  event.stopPropagation()
  if (!authStore.isAuthenticated) {
    ;(authStore as any).showAuthModal = true
    return
  }
  if (currentProfile.value) {
    profileStore.sendConnectRequest(currentProfile.value.user.username)
  }
}

const handleAccept = async (event: MouseEvent) => {
  event.stopPropagation()
  if (currentProfile.value) {
    try {
      await profileStore.acceptConnectRequest(currentProfile.value.user.username)
      const profileId = currentProfile.value.user.id

      // SYNC 1: Notifications Page (The Header/Bell List)
      notificationStore.forceSyncConnection(profileId)

      // SYNC 2: Suggestions List (The Discovery Tab/Sidebar)
      networkStore.forceSyncConnection(profileId)

      eventBus.emit('connection-established', profileId)
    } catch (error) {
      console.error('Failed to accept connection:', error)
    }
  }
}

const handleCancel = (event: MouseEvent) => {
  event.stopPropagation()
  if (currentProfile.value) {
    // Calls the store function to cancel the request in the DB
    profileStore.cancelConnectRequest(currentProfile.value.user.username)
  }
}

const handleFollowToggle = async (event: MouseEvent) => {
  event.stopPropagation()
  if (!authStore.isAuthenticated) {
    ;(authStore as any).showAuthModal = true
    return
  }
  if (currentProfile.value) {
    try {
      if (relationshipStatus.value?.is_followed_by_request_user) {
        // We don't need manual isLoading toggle here because
        // unfollowUser in your store likely handles it.
        await profileStore.unfollowUser(currentProfile.value.user.username)
      } else {
        await profileStore.followUser(currentProfile.value.user.username)

        // THE SYNC: Remove the "User X followed you" notification instantly
        const profileId = currentProfile.value.user.id
        notificationStore.forceSyncConnection(profileId)
      }
    } catch (error) {
      console.error('Follow toggle failed:', error)
    }
  }
}

const handleDisconnect = (event: MouseEvent) => {
  event.stopPropagation()
  if (currentProfile.value) {
    profileStore.unfollowUser(currentProfile.value.user.username)
    showDisconnectConfirm.value = false
  }
}

const handleMessage = (event: MouseEvent) => {
  event.stopPropagation()
  if (!authStore.isAuthenticated) {
    ;(authStore as any).showAuthModal = true
    return
  }
  console.log('Messaging functionality to be implemented.')
}

// Improved ripple effect handler without layout shifts
const createRipple = (event: MouseEvent) => {
  const button = event.currentTarget as HTMLElement

  // Create ripple container
  const rippleContainer = document.createElement('span')
  rippleContainer.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: inherit;
    overflow: hidden;
    pointer-events: none;
  `

  // Create ripple element
  const ripple = document.createElement('span')
  const rect = button.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2

  ripple.style.cssText = `
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.4);
    transform: scale(0);
    animation: ripple 600ms linear;
    width: ${size}px;
    height: ${size}px;
    left: ${x}px;
    top: ${y}px;
  `

  // Remove any existing ripple
  const existingRipple = button.querySelector('.ripple-container')
  if (existingRipple) {
    existingRipple.remove()
  }

  rippleContainer.classList.add('ripple-container')
  rippleContainer.appendChild(ripple)
  button.appendChild(rippleContainer)

  // Remove ripple after animation
  setTimeout(() => {
    if (rippleContainer.parentNode === button) {
      rippleContainer.remove()
    }
  }, 600)
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  if (showDisconnectConfirm.value) {
    showDisconnectConfirm.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div v-if="relationshipStatus" class="flex items-center space-x-3">
    <!-- CONNECT BUTTON -->
    <div class="relative overflow-visible">
      <!-- State: Not Connected -->
      <button
        v-if="relationshipStatus.connection_status === 'not_connected'"
        @click="handleConnect"
        @mouseenter="isHovering.connect = true"
        @mouseleave="isHovering.connect = false"
        @mousedown="createRipple"
        data-cy="connect-button"
        class="relative flex flex-col items-center p-2 transition-all duration-300 group w-[60px] h-[70px]"
      >
        <div
          :class="[
            'relative p-2 rounded-full mb-1 border-2 transition-all duration-300',
            isHovering.connect
              ? 'bg-gradient-to-br from-rose-100 to-red-100 border-rose-300/80 shadow-sm shadow-rose-200/50 scale-105'
              : 'bg-gradient-to-br from-red-50 to-rose-50 border-red-200/60 shadow-sm',
          ]"
        >
          <LinkIconSolid
            :class="[
              'w-5 h-5 transition-transform duration-300',
              isHovering.connect ? 'text-rose-600 scale-110' : 'text-red-500',
            ]"
          />
        </div>
        <span
          class="text-xs font-semibold bg-gradient-to-r from-rose-600 to-red-500 bg-clip-text text-transparent transition-all duration-300 mt-1"
        >
          Connect
        </span>
      </button>

      <!-- State: Request Sent (Now clickable to Cancel) -->
      <button
        v-else-if="relationshipStatus.connection_status === 'request_sent'"
        @click="handleCancel"
        @mouseenter="isHovering.connect = true"
        @mouseleave="isHovering.connect = false"
        @mousedown="createRipple"
        data-cy="pending-button"
        class="relative flex flex-col items-center p-2 transition-all duration-300 group w-[60px] h-[70px]"
        title="Click to cancel request"
      >
        <div
          :class="[
            'p-2 rounded-full mb-1 border-2 transition-all duration-300',
            isHovering.connect
              ? 'bg-red-50 border-red-200 shadow-sm'
              : 'border-amber-200/60 bg-gradient-to-br from-amber-50 to-yellow-50 shadow-sm',
          ]"
        >
          <!-- Show X icon on hover to signify 'Cancel', otherwise show Clock -->
          <XMarkIcon v-if="isHovering.connect" class="w-5 h-5 text-red-500" />
          <ClockIcon v-else class="w-5 h-5 text-amber-500" />
        </div>
        <span
          :class="[
            'text-xs font-semibold mt-1 transition-all duration-300',
            isHovering.connect
              ? 'text-red-600'
              : 'bg-gradient-to-r from-amber-500 to-yellow-500 bg-clip-text text-transparent',
          ]"
        >
          {{ isHovering.connect ? 'Cancel' : 'Pending' }}
        </span>
      </button>

      <!-- State: Request Received -->
      <button
        v-else-if="relationshipStatus.connection_status === 'request_received'"
        @click="handleAccept"
        @mouseenter="isHovering.connect = true"
        @mouseleave="isHovering.connect = false"
        @mousedown="createRipple"
        data-cy="accept-request-button"
        class="relative flex flex-col items-center p-2 transition-all duration-300 group w-[60px] h-[70px]"
      >
        <div
          :class="[
            'relative p-2 rounded-full mb-1 border-2 transition-all duration-300',
            isHovering.connect
              ? 'bg-gradient-to-br from-emerald-100 to-green-100 border-emerald-300/80 shadow-sm shadow-emerald-200/50 scale-105'
              : 'bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200/60 shadow-sm',
          ]"
        >
          <CheckBadgeIcon
            :class="[
              'w-5 h-5 transition-transform duration-300',
              isHovering.connect ? 'text-emerald-600 scale-110' : 'text-emerald-500',
            ]"
          />
        </div>
        <span
          class="text-xs font-semibold bg-gradient-to-r from-emerald-600 to-green-500 bg-clip-text text-transparent transition-all duration-300 mt-1"
        >
          Accept
        </span>
      </button>

      <!-- State: Connected -->
      <div
        v-else-if="relationshipStatus.connection_status === 'connected'"
        class="relative overflow-visible"
      >
        <button
          @click.stop="showDisconnectConfirm = !showDisconnectConfirm"
          @mouseenter="isHovering.connect = true"
          @mouseleave="isHovering.connect = false"
          data-cy="connected-button"
          :class="[
            'relative flex flex-col items-center p-2 transition-all duration-300 group w-[60px] h-[70px]',
            showDisconnectConfirm ? 'z-10' : '',
          ]"
        >
          <div
            :class="[
              'relative p-2 rounded-full mb-1 border-2 transition-all duration-300',
              showDisconnectConfirm
                ? 'bg-gradient-to-br from-emerald-100 to-green-100 border-emerald-300/80 shadow-sm scale-105'
                : isHovering.connect
                  ? 'bg-gradient-to-br from-emerald-100 to-green-100 border-emerald-300/80 shadow-sm shadow-emerald-200/50 scale-105'
                  : 'bg-gradient-to-br from-emerald-50 to-green-50 border-emerald-200/60 shadow-sm',
            ]"
          >
            <UserGroupIconSolid
              :class="[
                'w-5 h-5 transition-transform duration-300',
                showDisconnectConfirm || isHovering.connect
                  ? 'text-emerald-600 scale-110'
                  : 'text-emerald-500',
              ]"
            />
          </div>
          <span
            class="text-xs font-semibold bg-gradient-to-r from-emerald-600 to-green-500 bg-clip-text text-transparent transition-all duration-300 mt-1"
          >
            Connected
          </span>
        </button>

        <!-- Disconnect Dropdown -->
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          leave-active-class="transition-all duration-200 ease-in"
          enter-from-class="opacity-0 scale-95 -translate-y-2"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 -translate-y-2"
        >
          <div
            v-if="showDisconnectConfirm"
            class="absolute top-full left-1/2 transform -translate-x-1/2 mt-3 z-50"
          >
            <div class="relative">
              <!-- Arrow -->
              <div
                class="absolute -top-1 left-1/2 transform -translate-x-1/2 w-3 h-3 rotate-45 bg-red-50 border-l border-t border-red-200/60"
              ></div>

              <!-- Button -->
              <button
                @click.stop="handleDisconnect"
                @mouseenter="isHovering.disconnect = true"
                @mouseleave="isHovering.disconnect = false"
                data-cy="disconnect-button"
                class="relative overflow-hidden flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-red-50 to-rose-50 border border-red-200/60 rounded-xl shadow-md transition-all duration-300 group"
              >
                <HandThumbDownIconSolid
                  :class="[
                    'w-4 h-4 transition-transform duration-300',
                    isHovering.disconnect ? 'text-red-600 scale-110' : 'text-red-500',
                  ]"
                />
                <span
                  class="text-sm font-semibold bg-gradient-to-r from-red-600 to-rose-500 bg-clip-text text-transparent"
                >
                  Disconnect
                </span>
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- FOLLOW BUTTON -->
    <div v-if="relationshipStatus.connection_status !== 'connected'" class="overflow-visible">
      <button
        @click.stop="handleFollowToggle"
        @mouseenter="isHovering.follow = true"
        @mouseleave="isHovering.follow = false"
        @mousedown="createRipple"
        :disabled="isLoadingFollow"
        :class="[
          'relative flex flex-col items-center p-2 transition-all duration-300 group w-[60px] h-[70px]',
          isLoadingFollow ? 'cursor-wait' : '',
        ]"
        data-cy="follow-toggle-button"
      >
        <div
          :class="[
            'relative p-2 rounded-full mb-1 border-2 transition-all duration-300',
            followButtonClasses.ring,
          ]"
        >
          <component
            :is="isLoadingFollow ? ArrowPathIcon : followIcon"
            :class="[
              'w-5 h-5 transition-transform duration-300',
              isLoadingFollow ? 'animate-spin' : '',
              followButtonClasses.icon,
            ]"
          />
        </div>
        <span
          :class="[
            'text-[10px] font-bold uppercase tracking-tight transition-all duration-300 mt-1',
            followButtonClasses.text,
          ]"
        >
          {{ followButtonLabel }}
        </span>
      </button>
    </div>

    <!-- MESSAGE BUTTON -->
    <div v-if="canMessage" class="overflow-visible">
      <button
        @click.stop="handleMessage"
        @mouseenter="isHovering.message = true"
        @mouseleave="isHovering.message = false"
        @mousedown="createRipple"
        class="relative flex flex-col items-center p-2 transition-all duration-300 group w-[60px] h-[70px]"
        data-cy="message-button"
      >
        <div
          :class="[
            'relative p-2 rounded-full mb-1 border-2 transition-all duration-300',
            isHovering.message
              ? 'bg-gradient-to-br from-indigo-100 to-blue-100 border-indigo-300/80 shadow-sm shadow-indigo-200/50 scale-105'
              : 'bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-200/60 shadow-sm',
          ]"
        >
          <ChatBubbleLeftRightIconSolid
            :class="[
              'w-5 h-5 transition-transform duration-300',
              isHovering.message ? 'text-indigo-600 scale-110' : 'text-indigo-500',
            ]"
          />
        </div>
        <span
          class="text-xs font-semibold bg-gradient-to-r from-indigo-600 to-blue-500 bg-clip-text text-transparent transition-all duration-300 mt-1"
        >
          Message
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Ripple animation without layout shifts */
@keyframes ripple {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* Ensure the container maintains consistent sizing */
button {
  contain: layout style;
}
</style>
