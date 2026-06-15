<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axiosInstance from '@/services/axiosInstance'

const authStore = useAuthStore()
const emit = defineEmits(['close'])

// Professional student/alumni interest tags for NxtTurn [1]
const availableInterests = [
  'Technology',
  'Coding',
  'Finance',
  'Consulting',
  'Research',
  'Exams',
  'Internships',
  'Jobs',
  'Apprenticeships',
  'Design',
]

const selectedInterests = ref<string[]>([])

// Toggles selected interests [1]
const toggleInterest = (interest: string) => {
  if (selectedInterests.value.includes(interest)) {
    selectedInterests.value = selectedInterests.value.filter((i) => i !== interest)
  } else {
    selectedInterests.value.push(interest)
  }
}

const completeOnboarding = async () => {
  const username = authStore.currentUser?.username || 'guest'

  // 1. Save locally first for instant frontend UI access [4]
  localStorage.setItem(
    `nxtturn_selected_interests_${username}`,
    JSON.stringify(selectedInterests.value),
  )
  localStorage.setItem(`nxtturn_onboarding_dismissed_${username}`, 'true')

  // 2. If logged in, save the selected interests directly to their database profile! [4]
  if (authStore.isAuthenticated && authStore.currentUser?.username) {
    try {
      await axiosInstance.patch(`/profile/${authStore.currentUser.username}/`, {
        interests: selectedInterests.value,
      })
    } catch (error) {
      console.error('Failed to sync onboarding interests to database:', error)
    }
  }

  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[99999] flex items-center justify-center p-4">
      <!-- Backdrop (clicking outside closes the modal) [4] -->
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-md transition-opacity duration-300"
        @click="completeOnboarding"
      ></div>

      <!-- Modal Card [4] -->
      <div
        class="relative bg-white rounded-3xl shadow-2xl p-6 md:p-8 max-w-lg w-full mx-auto z-10 transform scale-100 transition-all duration-300 border border-gray-100 animate-slide-up"
      >
        <!-- Top Right Close Button [4] -->
        <button
          @click="completeOnboarding"
          class="absolute top-5 right-5 p-2 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors duration-200 cursor-pointer"
          aria-label="Close onboarding"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>

        <div class="flex flex-col space-y-6 pt-2">
          <!-- Header Section -->
          <div class="text-center space-y-2">
            <!-- Decorative Icon -->
            <div class="inline-flex p-3 bg-indigo-50 rounded-full text-indigo-600 mb-2">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-8 w-8"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 class="text-2xl font-extrabold text-gray-900 tracking-tight">
              Personalize Your Experience
            </h3>
            <p class="text-sm text-gray-500 max-w-sm mx-auto leading-relaxed">
              Select your fields of interest to tailor your professional feed, directories, and
              recommendations [1].
            </p>
          </div>

          <!-- Interests Tags Grid [1] -->
          <div class="space-y-3">
            <div class="flex flex-wrap gap-2.5 justify-center py-2">
              <button
                v-for="interest in availableInterests"
                :key="interest"
                @click="toggleInterest(interest)"
                type="button"
                class="inline-flex items-center gap-1.5 px-4.5 py-2.5 rounded-full text-sm font-bold transition-all duration-200 border cursor-pointer active:scale-95 shadow-sm hover:-translate-y-0.5"
                :class="[
                  selectedInterests.includes(interest)
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white border-transparent'
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100 hover:border-gray-300',
                ]"
              >
                <!-- Checkmark Icon (rendered dynamically on select) [4] -->
                <svg
                  v-if="selectedInterests.includes(interest)"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4 text-white"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                {{ interest }}
              </button>
            </div>
          </div>

          <!-- Footer Action [4] -->
          <div class="flex items-center justify-center border-t border-gray-100 pt-5">
            <button
              @click="completeOnboarding"
              class="w-full sm:w-auto px-12 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-extrabold text-sm rounded-full shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95 text-center tracking-wide cursor-pointer"
            >
              Start Browsing My Feed
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Frosted glass effect for backdrop [4] */
.backdrop-blur-md {
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

/* Soft slide up animation [4] */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
