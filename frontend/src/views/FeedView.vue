<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useFeedStore } from '@/stores/feed'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import OnboardingModal from '@/components/common/OnboardingModal.vue'
import axiosInstance from '@/services/axiosInstance'
import { getAvatarUrl } from '@/utils/avatars'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import CreatePostForm from '@/components/CreatePostForm.vue'
import PostItem from '@/components/PostItem.vue'
import eventBus from '@/services/eventBus'
import {
  ArrowUpIcon,
  ExclamationTriangleIcon,
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  SparklesIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/solid'
import PostItemSkeleton from '@/components/PostItemSkeleton.vue'

const feedStore = useFeedStore()
const postsStore = usePostsStore()
const authStore = useAuthStore()

const createPostFormKey = ref(0)

// --- MOBILE DISCOVERY CAROUSEL STATE --- [20]
const recommendedUsers = ref<any[]>([])
const isLoadingDiscovery = ref(false)

// Fetches 6 recommended colleagues from your discover API [20]
const fetchMobileRecommendations = async () => {
  if (!authStore.isAuthenticated) return
  isLoadingDiscovery.value = true
  try {
    const response = await axiosInstance.get('/network/discover/')
    const mutuals = response.data.mutual_connections || []
    const alumni = response.data.alumni || []
    const locals = response.data.local_professionals || []

    // Take the top 6 suggestions to keep the horizontal list fast and clean [20]
    recommendedUsers.value = [...mutuals, ...alumni, ...locals].slice(0, 6)
  } catch (error) {
    console.error('Failed to fetch mobile suggestions:', error)
  } finally {
    isLoadingDiscovery.value = false
  }
}

// Handles connection request from the mobile carousel [20]
const handleCarouselConnect = async (user: any) => {
  try {
    await axiosInstance.post('/connection-requests/', { receiver: user.id })
    // Change the button state locally to "Pending" [20]
    user.connection_status = 'pending_sent'
  } catch (error) {
    console.error('Failed to connect:', error)
  }
}

const loadMoreTrigger = ref<HTMLElement | null>(null)

const mainFeedPosts = computed(() => {
  return postsStore.getPostsByIds(feedStore.mainFeedPostIds)
})

const nextFeedPageUrl = computed(() => feedStore.mainFeedNextCursor)
useInfiniteScroll(loadMoreTrigger, feedStore.fetchNextPageOfMainFeed, nextFeedPageUrl)

function forceFormReset() {
  createPostFormKey.value++
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

function handleShowNewPosts() {
  feedStore.showNewPosts()
  scrollToTop()
}

// --- ONBOARDING MODAL STATE --- [1]
const showOnboardingModal = ref(false)

onMounted(() => {
  eventBus.on('reset-feed-form', forceFormReset)
  eventBus.on('scroll-to-top', scrollToTop)

  feedStore.refreshMainFeed()

  // --- Check if they need onboarding (User-Specific) --- [4]
  const username = authStore.currentUser?.username || 'guest'
  const isDismissed = localStorage.getItem(`nxtturn_onboarding_dismissed_${username}`) === 'true'
  if (authStore.isAuthenticated && !isDismissed) {
    showOnboardingModal.value = true
  }

  // Fetch mobile suggestions on load if authenticated [20]
  if (authStore.isAuthenticated) {
    fetchMobileRecommendations()
  }
})

onUnmounted(() => {
  eventBus.off('reset-feed-form', forceFormReset)
  eventBus.off('scroll-to-top', scrollToTop)
})
</script>

<template>
  <div class="max-w-4xl mx-auto min-h-[calc(100vh-12rem)]">
    <div class="space-y-3">
      <CreatePostForm :key="createPostFormKey" />

      <!-- --- NEW: MOBILE DISCOVERY CAROUSEL --- [20] -->
      <!-- Only shown on mobile (md:hidden) for logged-in users with suggestions [20] -->
      <div
        v-if="authStore.isAuthenticated && recommendedUsers.length > 0"
        class="block md:hidden bg-white p-4 rounded-2xl shadow-sm border border-gray-100"
      >
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-sm font-bold text-gray-800 flex items-center gap-1.5">
            <!-- Custom Inline User-Plus SVG to prevent any import errors -->
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4.5 w-4.5 text-orange-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
              />
            </svg>
            People You May Know [20]
          </h4>
          <router-link to="/network" class="text-xs text-blue-500 font-semibold hover:underline">
            See all
          </router-link>
        </div>

        <!-- Horizontal Swipeable Card Deck [20] -->
        <div
          class="flex gap-3 overflow-x-auto pb-2 no-scrollbar scroll-smooth snap-x snap-mandatory"
        >
          <div
            v-for="user in recommendedUsers"
            :key="user.id"
            class="flex-shrink-0 w-36 bg-gray-50 rounded-xl p-3 border border-gray-100/50 flex flex-col items-center text-center snap-start"
          >
            <img
              :src="getAvatarUrl(user.picture, user.name, user.username)"
              class="w-12 h-12 rounded-full object-cover border-2 border-white shadow-sm mb-1.5"
              alt="avatar"
            />
            <p class="text-xs font-bold text-gray-900 truncate w-full px-1">{{ user.name }}</p>
            <p class="text-[10px] text-gray-500 truncate w-full px-1 mb-3">@{{ user.username }}</p>

            <!-- Connect / Pending CTA Button [20] -->
            <button
              type="button"
              @click="handleCarouselConnect(user)"
              :disabled="user.connection_status === 'pending_sent'"
              class="w-full py-1.5 rounded-full text-[10px] font-bold transition active:scale-95 disabled:opacity-50 cursor-pointer"
              :class="[
                user.connection_status === 'pending_sent'
                  ? 'bg-amber-100 text-amber-700 border border-amber-200'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm',
              ]"
            >
              {{ user.connection_status === 'pending_sent' ? 'Pending' : 'Connect' }}
            </button>
          </div>
        </div>
      </div>

      <!-- New Posts Notification - Floating Overlap with lower stop point -->
      <div
        v-if="feedStore.newPostIdsFromRefresh.length > 0"
        class="sticky top-24 z-30 pointer-events-none"
        :class="feedStore.newPostIdsFromRefresh.length === 0 ? 'hidden' : ''"
        style="height: 0"
      >
        <div class="absolute left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <button
            @click="handleShowNewPosts"
            class="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold px-3 py-1 rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 transform pointer-events-auto"
          >
            <SparklesIcon class="w-5 h-5" />
            Show {{ feedStore.newPostIdsFromRefresh.length }} new post(s)
            <ArrowUpIcon class="w-5 h-5 ml-1" />
          </button>
        </div>
      </div>

      <div v-if="feedStore.isLoadingMainFeed && mainFeedPosts.length === 0" class="space-y-6">
        <PostItemSkeleton v-for="n in 3" :key="n" />
      </div>

      <!-- Error Message -->
      <div
        v-if="feedStore.mainFeedError"
        class="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 rounded-r-lg p-6 shadow-md"
        role="alert"
      >
        <div class="flex items-center gap-3">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <ExclamationTriangleIcon class="w-6 h-6 text-red-600" />
            </div>
          </div>
          <div>
            <p class="text-lg font-semibold text-red-800">
              Error loading feed: {{ feedStore.mainFeedError }}
            </p>
            <button
              @click="feedStore.refreshMainFeed"
              class="mt-2 inline-flex items-center gap-2 text-sm font-medium text-red-700 hover:text-red-800 transition"
            >
              <ArrowPathIcon class="w-4 h-4" />
              Try again
            </button>
          </div>
        </div>
      </div>

      <div v-if="mainFeedPosts.length > 0" class="space-y-4">
        <PostItem v-for="post in mainFeedPosts" :key="post.id" :post="post" />
      </div>

      <!-- Empty Feed Message -->
      <div
        v-if="
          !feedStore.isLoadingMainFeed && mainFeedPosts.length === 0 && !feedStore.mainFeedError
        "
        class="text-center py-12 px-4"
        data-cy="empty-feed-message"
      >
        <div class="max-w-md mx-auto">
          <div
            class="w-24 h-24 mx-auto bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6"
          >
            <ChatBubbleLeftRightIcon class="w-12 h-12 text-gray-400" />
          </div>
          <h3 class="text-2xl font-bold text-gray-800 mb-2">Your feed is empty</h3>
          <p class="text-gray-600 mb-6">Follow some users or create a post!</p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              @click="eventBus.emit('scroll-to-top')"
              class="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 transition shadow-md hover:shadow-lg"
            >
              Create a post
            </button>
            <button
              class="px-6 py-3 bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 font-medium rounded-lg hover:from-gray-200 hover:to-gray-300 transition shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              <UserGroupIcon class="w-5 h-5" />
              Explore users
            </button>
          </div>
        </div>
      </div>

      <div v-if="feedStore.mainFeedNextCursor" ref="loadMoreTrigger" class="h-10"></div>

      <!-- Loading More Posts -->
      <div v-if="feedStore.isLoadingMainFeed && mainFeedPosts.length > 0" class="text-center py-8">
        <div class="inline-flex flex-col items-center gap-3">
          <div class="relative">
            <div class="w-12 h-12 border-4 border-blue-100 rounded-full"></div>
            <div
              class="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full absolute top-0 left-0 animate-spin"
            ></div>
          </div>
          <div>
            <p class="text-gray-700 font-medium">Loading more posts...</p>
          </div>
        </div>
      </div>

      <!-- Add extra spacing at the bottom for mobile -->
      <div class="h-4 md:h-0"></div>
    </div>
  </div>

  <!-- --- NEW: THE ONBOARDING MODAL OVERLAY --- -->
  <OnboardingModal v-if="showOnboardingModal" @close="showOnboardingModal = false" />
</template>
