<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const closeModal = () => {
  authStore.showAuthModal = false
}

const navigateTo = (routeName: string) => {
  closeModal()
  router.push({ name: routeName })
}

// Close on Escape key [4]
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    closeModal()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-[99999] flex items-center justify-center p-4">
      <!-- Backdrop (Clicking outside closes the modal) [4] -->
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
        @click="closeModal"
      ></div>

      <!-- Modal Content Box -->
      <div
        class="relative bg-white rounded-2xl shadow-2xl p-6 md:p-8 max-w-sm w-full mx-auto z-10 transform scale-100 transition-all duration-300"
      >
        <!-- Top Right Close "X" Button [4] -->
        <button
          @click="closeModal"
          class="absolute top-4 right-4 p-1.5 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition duration-200"
          aria-label="Close modal"
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

        <!-- Center Content -->
        <div class="flex flex-col items-center text-center space-y-4 pt-2">
          <!-- Shield Lock Icon -->
          <div class="p-3.5 bg-blue-50 rounded-full text-blue-600">
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
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>

          <h3 class="text-xl font-bold text-gray-900">Join the Community</h3>
          <p class="text-sm text-gray-500 max-w-xs leading-relaxed">
            Please sign in or create an account to like, comment, and connect with other users
            [1.1.2].
          </p>

          <!-- Primary CTA Buttons [1.1.2] -->
          <div class="flex flex-col w-full gap-2 pt-3">
            <button
              @click="navigateTo('login')"
              class="w-full py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold rounded-full shadow hover:from-blue-600 hover:to-purple-600 active:scale-[0.98] transition duration-200"
            >
              Sign In
            </button>
            <button
              @click="navigateTo('register')"
              class="w-full py-2.5 border border-gray-300 text-gray-700 font-bold rounded-full hover:bg-gray-50 active:scale-[0.98] transition duration-200"
            >
              Create Account
            </button>
          </div>

          <!-- Dismiss CTA Button [4] -->
          <button
            @click="closeModal"
            class="text-xs text-gray-400 hover:text-gray-600 hover:underline pt-2 font-medium"
          >
            Keep browsing as guest
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* Smooth blur transition */
.backdrop-blur-sm {
  backdrop-filter: blur(4px);
}
</style>
