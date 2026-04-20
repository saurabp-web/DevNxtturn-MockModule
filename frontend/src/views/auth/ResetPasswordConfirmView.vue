<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const newPassword1 = ref('')
const newPassword2 = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)

// HARDENING: State to track if the link is actually usable
const isLinkValid = ref<boolean | null>(null)

// State for the password visibility toggles
const showPassword1 = ref(false)
const showPassword2 = ref(false)

const uid = ref<string>('')
const token = ref<string>('')

// HARDENING: Reactive logic to lock the button
const passwordsMismatch = computed(() => {
  return newPassword1.value && newPassword2.value && newPassword1.value !== newPassword2.value
})

const isSubmitDisabled = computed(() => {
  return (
    isLoading.value || passwordsMismatch.value || !newPassword1.value || isLinkValid.value === false
  )
})

onMounted(async () => {
  uid.value = route.params.uid as string
  token.value = route.params.token as string

  // SILENT CHECK: Verify the link before the user types a single letter
  try {
    await axiosInstance.get(`auth/password/reset/validate/${uid.value}/${token.value}/`)
    isLinkValid.value = true
  } catch (err) {
    isLinkValid.value = false
    errorMessage.value = 'This password reset link is invalid or has expired.'
  }
})

const handleResetConfirm = async () => {
  isLoading.value = true
  errorMessage.value = null

  try {
    const payload = {
      uid: uid.value,
      token: token.value,
      new_password1: newPassword1.value,
      new_password2: newPassword2.value,
    }

    await axiosInstance.post('auth/password/reset/confirm/', payload)

    successMessage.value = 'Your password has been reset successfully!'
    toast.success('Success! Redirecting to login...')

    setTimeout(() => {
      router.push({ name: 'login' })
    }, 2000)
  } catch (error: any) {
    const errorData = error.response?.data
    if (errorData) {
      errorMessage.value = Object.values(errorData).flat().join(' ')
    } else {
      errorMessage.value = 'An unexpected error occurred. The link may be invalid or expired.'
    }
    toast.error(errorMessage.value)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div
    class="min-h-screen w-full bg-gradient-to-br from-[#667eea] to-[#764ba2] flex items-center justify-center p-4"
  >
    <div class="w-full max-w-sm bg-white rounded-2xl shadow-xl overflow-hidden">
      <!-- Header -->
      <div class="px-6 pt-6 pb-4 text-center border-b border-gray-100">
        <div class="logo flex justify-center mb-2">
          <span
            class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent text-2xl font-bold"
            >NxtTurn</span
          >
        </div>
        <h2 class="text-lg font-bold text-gray-600 mt-1">Choose a New Password</h2>
      </div>

      <!-- Main Body -->
      <div class="px-6 py-5">
        <!-- 1. LOADING: Checking the link -->
        <div v-if="isLinkValid === null" class="text-center py-8">
          <div
            class="animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"
          ></div>
          <p class="text-xs text-gray-500">Verifying security link...</p>
        </div>

        <!-- 2. EXPIRED: Warning -->
        <div v-else-if="isLinkValid === false" class="text-center py-6">
          <div class="text-red-500 text-5xl mb-4">⚠️</div>
          <h3 class="text-sm font-bold text-gray-800 mb-2">Link Expired</h3>
          <p class="text-xs text-gray-600 leading-relaxed mb-6">
            For your security, reset links only last 1 hour. <br />Please request a new one.
          </p>
          <router-link
            :to="{ name: 'ForgotPassword' }"
            class="block w-full py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold shadow-md"
          >
            Request New Link
          </router-link>
        </div>

        <!-- 3. VALID: Show the form -->
        <form v-else @submit.prevent="handleResetConfirm" class="space-y-4">
          <div
            v-if="successMessage"
            class="bg-green-50 border-l-4 border-green-500 text-green-700 p-3 rounded-lg text-xs"
          >
            {{ successMessage }}
          </div>

          <div
            v-if="errorMessage"
            class="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-lg text-[10px]"
          >
            {{ errorMessage }}
          </div>

          <template v-if="!successMessage">
            <!-- New Password Input (ID ADDED FOR CYPRESS) -->
            <div class="relative">
              <label for="new_password1" class="block text-xs font-medium text-gray-700 mb-1"
                >New Password</label
              >
              <input
                id="new_password1"
                :type="showPassword1 ? 'text' : 'password'"
                v-model="newPassword1"
                required
                class="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg focus:ring-1 focus:ring-indigo-500 outline-none"
              />
              <button
                type="button"
                @click="showPassword1 = !showPassword1"
                class="absolute right-3 top-7 text-gray-400"
              >
                <svg
                  v-if="showPassword1"
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18"
                  />
                </svg>
                <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
            </div>

            <!-- Confirm Password Input (ID ADDED FOR CYPRESS) -->
            <div class="relative">
              <label for="new_password2" class="block text-xs font-medium text-gray-700 mb-1"
                >Confirm New Password</label
              >
              <input
                id="new_password2"
                :type="showPassword2 ? 'text' : 'password'"
                v-model="newPassword2"
                required
                class="w-full px-3 py-2 text-xs border rounded-lg outline-none transition-colors"
                :class="
                  passwordsMismatch
                    ? 'border-red-500 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-indigo-500'
                "
              />
              <button
                type="button"
                @click="showPassword2 = !showPassword2"
                class="absolute right-3 top-7 text-gray-400"
              >
                <svg
                  v-if="showPassword2"
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18"
                  />
                </svg>
                <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
              <p v-if="passwordsMismatch" class="mt-1 text-[10px] text-red-600">
                Passwords do not match.
              </p>
            </div>

            <button
              type="submit"
              :disabled="Boolean(isSubmitDisabled)"
              class="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg disabled:bg-indigo-300 disabled:cursor-not-allowed text-xs shadow-md"
            >
              {{ isLoading ? 'Resetting...' : 'Reset Password' }}
            </button>
          </template>
        </form>

        <!-- Footer -->
        <div class="text-center text-xs text-gray-600 mt-6 pt-4 border-t border-gray-50">
          Already remembered?
          <router-link :to="{ name: 'login' }" class="text-indigo-600 font-medium hover:underline"
            >Sign in</router-link
          >
        </div>
      </div>
    </div>
  </div>
</template>
