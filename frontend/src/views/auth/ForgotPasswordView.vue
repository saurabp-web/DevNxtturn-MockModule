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
        <h2 class="text-lg font-bold text-gray-600 mt-1">Forgot Your Password?</h2>
        <p class="mt-2 text-center text-xs text-gray-600">
          No problem. Enter your email address below and we'll send you a link to reset it.
        </p>
      </div>

      <!-- Form Body -->
      <!-- Form Body -->
      <div class="px-6 py-5">
        <!-- 1. SUCCESS STATE: Shown ONLY after email is sent -->
        <div v-if="successMessage" class="text-center py-4 animate-in fade-in duration-500">
          <div class="text-4xl mb-3">📩</div>
          <h3 class="text-sm font-bold text-gray-800 mb-2">Check your email</h3>
          <p class="text-xs text-gray-600 leading-relaxed mb-6">
            We've sent a reset link to <br />
            <span class="font-semibold text-indigo-600">{{ email }}</span
            >. Check your inbox and spam folder.
          </p>
          <!-- This link resets the screen so they can try again if they made a typo -->
          <button @click="successMessage = null" class="text-xs text-indigo-600 hover:underline">
            Didn't get it? Try another email
          </button>
        </div>

        <!-- 2. INPUT STATE: Shown by default, HIDDEN after success -->
        <form v-else @submit.prevent="handleRequestReset" class="space-y-4">
          <!-- Error Message -->
          <div
            v-if="errorMessage"
            class="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-lg text-[10px] flex items-center gap-2"
          >
            <span>⚠️</span> {{ errorMessage }}
          </div>

          <!-- Email Input -->
          <div>
            <label for="email" class="block text-xs font-medium text-gray-700 mb-1"
              >Email Address</label
            >
            <input
              type="email"
              id="email"
              v-model="email"
              required
              :disabled="isLoading"
              placeholder="name@example.com"
              class="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
            />
          </div>

          <button
            type="submit"
            :disabled="Boolean(isLoading)"
            class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors disabled:bg-indigo-300 text-xs"
          >
            {{ isLoading ? 'Sending Link...' : 'Send Reset Link' }}
          </button>
        </form>

        <!-- Footer -->
        <div class="text-center text-xs text-gray-600 mt-4">
          <p>
            Remembered your password?
            <router-link
              :to="{ name: 'login' }"
              class="text-indigo-600 hover:text-indigo-500 font-medium hover:underline transition-colors"
            >
              Sign in
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'

const email = ref('')
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const toast = useToast()

const handleRequestReset = async () => {
  isLoading.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    const response = await axiosInstance.post('auth/password/reset/', {
      email: email.value,
    })

    // The API always returns a success message for security, as per our pytest test.
    successMessage.value =
      response.data.detail +
      ' If an account with this email exists, you will receive instructions shortly.'
    toast.success('Password reset request sent successfully.')
  } catch (error: any) {
    errorMessage.value =
      error.response?.data?.detail || 'An unexpected error occurred. Please try again.'
    toast.error(errorMessage.value)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.logo img {
  filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.1));
  border-radius: 6px;
}
</style>
