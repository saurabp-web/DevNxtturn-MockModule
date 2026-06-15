<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { useRouter } from 'vue-router'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'

const authStore = useAuthStore()
const profileStore = useProfileStore()
const router = useRouter()
const toast = useToast()

const activeTab = ref<'settings' | 'privacy'>('privacy') // Default to privacy first

// Dynamic state variables for the 4 database fields
const profileVisibility = ref('public')
const emailVisibility = ref('connections')
const phoneVisibility = ref('connections')
const messageVisibility = ref('members')

const isSaving = ref(false)
const isLoadingSettings = ref(false)

// Redirect them back to the feed page on cancel or success
const goBackToFeed = () => {
  router.push('/')
}

// Fetch the user's actual database settings on load
const fetchCurrentPrivacySettings = async () => {
  if (!authStore.currentUser?.username) return
  isLoadingSettings.value = true
  try {
    const response = await axiosInstance.get(`/profiles/${authStore.currentUser.username}/`)
    profileVisibility.value = response.data.profile_visibility || 'public'
    emailVisibility.value = response.data.email_visibility || 'connections'
    phoneVisibility.value = response.data.phone_visibility || 'connections'
    messageVisibility.value = response.data.message_visibility || 'members'
  } catch (error) {
    console.error('Failed to fetch current privacy settings:', error)
  } finally {
    isLoadingSettings.value = false
  }
}

// Save all 4 privacy settings at once with a single API PATCH request!
const handleSavePrivacy = async () => {
  if (!authStore.currentUser?.username) return
  isSaving.value = true
  try {
    const response = await axiosInstance.patch(`/profiles/${authStore.currentUser.username}/`, {
      profile_visibility: profileVisibility.value,
      email_visibility: emailVisibility.value,
      phone_visibility: phoneVisibility.value,
      message_visibility: messageVisibility.value,
    })

    // Instant UI Sync: If they are looking at their own profile card right now,
    // update the local profile store state so the visual lock badges update instantly!
    if (
      profileStore.currentProfile &&
      profileStore.currentProfile.user.username === authStore.currentUser.username
    ) {
      const profile = profileStore.currentProfile as any
      profile.profile_visibility = response.data.profile_visibility
      profile.email_visibility = response.data.email_visibility
      profile.phone_visibility = response.data.phone_visibility
      profile.message_visibility = response.data.message_visibility
    }

    toast.success('Privacy settings saved successfully!')
    goBackToFeed()
  } catch (error) {
    console.error('Failed to save privacy settings:', error)
    toast.error('Could not save privacy settings. Please try again.')
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  fetchCurrentPrivacySettings()
})
</script>

<template>
  <div class="max-w-7xl mx-auto pt-24 pb-6 px-4 sm:px-5 lg:px-6">
    <!-- Main Dashboard Box -->
    <div
      class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row h-[600px] max-h-[80vh] w-full"
    >
      <!-- LEFT SIDEBAR: Tab Selectors -->
      <aside
        class="w-full md:w-60 bg-gray-50 border-r border-gray-100 flex flex-row md:flex-col p-4 space-x-2 md:space-x-0 md:space-y-1.5 flex-shrink-0"
      >
        <div class="hidden md:block px-3 py-3 mb-2">
          <h3 class="text-lg font-extrabold text-gray-800">Account Portal</h3>
          <p class="text-xs text-gray-400">Configure preferences & security</p>
        </div>

        <!-- General Settings Tab Button -->
        <button
          @click="activeTab = 'settings'"
          type="button"
          class="flex-1 md:flex-none flex items-center justify-center md:justify-start gap-2.5 px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 cursor-pointer"
          :class="[
            activeTab === 'settings'
              ? 'bg-blue-500 text-white shadow-md'
              : 'text-gray-600 hover:bg-gray-150 hover:text-gray-900',
          ]"
        >
          <!-- Gear Icon -->
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span>Settings</span>
        </button>

        <!-- Privacy Settings Tab Button -->
        <button
          @click="activeTab = 'privacy'"
          type="button"
          class="flex-1 md:flex-none flex items-center justify-center md:justify-start gap-2.5 px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 cursor-pointer"
          :class="[
            activeTab === 'privacy'
              ? 'bg-blue-500 text-white shadow-md'
              : 'text-gray-600 hover:bg-gray-150 hover:text-gray-900',
          ]"
        >
          <!-- Lock Icon -->
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
          <span>Privacy & Safety</span>
        </button>
      </aside>

      <!-- RIGHT PANEL: Content Pane -->
      <main class="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col h-full relative">
        <!-- TAB 1: General Settings -->
        <div v-if="activeTab === 'settings'" class="space-y-6">
          <div>
            <h2 class="text-xl font-extrabold text-gray-900">General Settings</h2>
            <p class="text-xs text-gray-400">View your basic account profile credentials.</p>
          </div>

          <!-- Read Only Credentials -->
          <div
            class="space-y-4 bg-gray-50 border border-gray-100 rounded-2xl p-5"
            v-if="authStore.currentUser"
          >
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider"
                >Username</label
              >
              <p class="text-sm font-semibold text-gray-800 mt-1">
                @{{ authStore.currentUser.username }}
              </p>
            </div>
            <hr class="border-gray-200/60" />
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider"
                >Email Address</label
              >
              <p class="text-sm font-semibold text-gray-800 mt-1">
                {{ authStore.currentUser.email }}
              </p>
            </div>
            <hr class="border-gray-200/60" />
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider"
                >Date Joined</label
              >
              <p class="text-sm font-semibold text-gray-800 mt-1">
                {{
                  new Date(authStore.currentUser.date_joined).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })
                }}
              </p>
            </div>
          </div>
        </div>

        <!-- TAB 2: Privacy & Safety Settings -->
        <div v-if="activeTab === 'privacy'" class="flex-grow flex flex-col justify-between h-full">
          <div class="space-y-6">
            <div>
              <h2 class="text-xl font-extrabold text-gray-900">Privacy & Safety</h2>
              <p class="text-xs text-gray-400">
                Configure who is authorized to view your contents and files.
              </p>
            </div>

            <!-- Loading spinner -->
            <div v-if="isLoadingSettings" class="text-center py-10 text-sm text-gray-500">
              Fetching current preferences...
            </div>

            <!-- Privacy Dropdowns Form -->
            <div v-else class="space-y-4 max-h-[350px] overflow-y-auto pr-1 no-scrollbar">
              <!-- 1. Profile Visibility -->
              <div class="space-y-1.5">
                <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider"
                  >Profile Page Visibility</label
                >
                <select
                  v-model="profileVisibility"
                  class="w-full p-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl text-sm font-semibold focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition outline-none cursor-pointer"
                >
                  <option value="public">Everyone (Public index)</option>
                  <option value="members">Registered Members Only</option>
                  <option value="followers">My Followers Only</option>
                  <option value="connections">Mutual Connections Only</option>
                  <option value="self">Only Me (Fully Private)</option>
                </select>
                <p class="text-[10px] text-gray-400 leading-tight">
                  Controls who can read your bio, resume, skills, and histories.
                </p>
              </div>

              <!-- 2. Messaging Privacy -->
              <div class="space-y-1.5 pt-2">
                <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider"
                  >Inbox Privacy (Direct Messages)</label
                >
                <select
                  v-model="messageVisibility"
                  class="w-full p-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl text-sm font-semibold focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition outline-none cursor-pointer"
                >
                  <option value="public">Everyone (Accept all DMs)</option>
                  <option value="members">Registered Members</option>
                  <option value="followers">My Followers</option>
                  <option value="connections">Mutual Connections Only</option>
                  <option value="self">No One (Lock inbox)</option>
                </select>
                <p class="text-[10px] text-gray-400 leading-tight">
                  Controls who is authorized to open direct chats with you.
                </p>
              </div>

              <!-- 3. Email Visibility -->
              <div class="space-y-1.5 pt-2">
                <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider"
                  >Email Address Visibility</label
                >
                <select
                  v-model="emailVisibility"
                  class="w-full p-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl text-sm font-semibold focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition outline-none cursor-pointer"
                >
                  <option value="public">Everyone</option>
                  <option value="members">Registered Members</option>
                  <option value="followers">My Followers</option>
                  <option value="connections">Mutual Connections Only</option>
                  <option value="self">Only Me</option>
                </select>
              </div>

              <!-- 4. Phone Visibility -->
              <div class="space-y-1.5 pt-2">
                <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider"
                  >Phone Number Visibility</label
                >
                <select
                  v-model="phoneVisibility"
                  class="w-full p-2.5 bg-gray-50 border-2 border-gray-200 rounded-xl text-sm font-semibold focus:border-blue-400 focus:ring-2 focus:ring-blue-50 transition outline-none cursor-pointer"
                >
                  <option value="public">Everyone</option>
                  <option value="members">Registered Members</option>
                  <option value="followers">My Followers</option>
                  <option value="connections">Mutual Connections Only</option>
                  <option value="self">Only Me</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Save/Cancel Actions -->
          <div
            class="flex items-center justify-end gap-3 border-t border-gray-100 pt-5 mt-auto flex-shrink-0"
          >
            <button
              @click="goBackToFeed"
              type="button"
              class="px-6 py-2.5 border border-gray-300 text-gray-700 font-bold text-sm rounded-full hover:bg-gray-50 transition active:scale-95 text-center cursor-pointer"
            >
              Cancel
            </button>
            <button
              @click="handleSavePrivacy"
              :disabled="isSaving || isLoadingSettings"
              class="w-full sm:w-auto px-8 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-extrabold text-sm rounded-full shadow hover:shadow-md transition active:scale-95 text-center cursor-pointer disabled:opacity-50"
            >
              {{ isSaving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Hide scrollbar on dropdown container for clean layout */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
