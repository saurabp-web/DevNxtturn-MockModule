// C:\Users\Vinay\Project\frontend\src/services/axiosInstance.ts

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'

let isOffline = false
let offlineToastId: string | number | null = null

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 155000,
  headers: {
    Accept: 'application/json',
  },
})

axiosInstance.interceptors.request.use(
  (config) => {
    // 1. If the URL is absolute (http...), strip it to a relative path
    if (config.url && config.url.startsWith('http')) {
      try {
        const url = new URL(config.url)
        config.url = url.pathname + url.search
      } catch (e) {
        console.error('URL Sanitization failed', e)
      }
    }

    // 2. THE FIX: If the path already starts with /api/, remove the baseURL prefix
    // to prevent double /api//api/
    if (config.url && config.url.startsWith('/api/')) {
      config.baseURL = ''
    } else {
      config.baseURL = import.meta.env.VITE_API_BASE_URL
    }

    const authStore = useAuthStore()
    const token = authStore.authToken
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

axiosInstance.interceptors.response.use(
  // Handles SUCCESSFUL responses
  (response) => {
    // --- THIS IS THE FIX ---
    // If we were previously offline, this successful request means we are back online.
    if (isOffline) {
      const toast = useToast()

      // Dismiss the persistent offline toast if it exists.
      if (offlineToastId) {
        toast.dismiss(offlineToastId)
      }

      // Show the success message and reset the state. The onClose will also
      // fire, but resetting it here ensures it's always correct.
      toast.success('You are back online!', { timeout: 3000 })
      isOffline = false
      offlineToastId = null
    }
    // --- END OF FIX ---
    return response
  },
  // Handles ALL errors
  (error) => {
    if (error.code === 'ERR_NETWORK' || !error.response) {
      if (!isOffline) {
        isOffline = true
        const toast = useToast()
        offlineToastId = toast.error(
          'You appear to be offline. Please check your internet connection.',
          {
            timeout: false,
            onClose: () => {
              // This ensures that if the user manually closes the toast,
              // we are ready to show another one on the next network error.
              isOffline = false
              offlineToastId = null
            },
          },
        )
      }
    } else if (error.response && error.response.status === 401) {
      const authStore = useAuthStore()
      if (authStore.authToken) {
        authStore.logout()
      }
    }
    return Promise.reject(error)
  },
)

export default axiosInstance
