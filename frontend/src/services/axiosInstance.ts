// C:\Users\Vinay\Project\frontend\src/services/axiosInstance.ts

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useToast } from 'vue-toastification'

let isOffline = false
let offlineToastId: string | number | null = null

const rawApiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/'
const apiBaseURL = rawApiBaseURL.replace(/\/+$|\/+(?=\?)|\/+(?=#)/g, '/')

const axiosInstance = axios.create({
  baseURL: apiBaseURL,
  timeout: 155000,
  headers: {
    Accept: 'application/json',
  },
})

axiosInstance.interceptors.request.use(
  (config) => {
    // 1. Normalize absolute URLs to relative paths so baseURL injection works consistently.
    if (config.url && config.url.startsWith('http')) {
      try {
        const url = new URL(config.url)
        config.url = url.pathname + url.search
      } catch (e) {
        console.error('URL Sanitization failed', e)
      }
    }

    // 2. Keep backend host resolution stable across environments.
    // If configured to use a relative /api/ proxy, leave /api/ requests as-is.
    // If configured to use an absolute backend URL that already contains /api/, avoid duplicating it.
    if (config.url && config.url.startsWith('/api/')) {
      if (apiBaseURL.match(/^https?:\/\/.*\/api\/?$/)) {
        config.url = config.url.replace(/^\/api/, '')
        config.baseURL = apiBaseURL
      } else if (apiBaseURL.startsWith('/')) {
        config.baseURL = ''
      } else {
        config.baseURL = apiBaseURL
      }
    } else {
      config.baseURL = apiBaseURL
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
    // 1. Identify if this request should be "Silent" (like a health check)
    const isHealthCheck = error.config?.url?.includes('health-check')

    // 2. Only show the error if it's a real network failure AND it's NOT a silent check
    if ((error.code === 'ERR_NETWORK' || !error.response) && !isHealthCheck) {
      if (!isOffline) {
        isOffline = true
        const toast = useToast()
        offlineToastId = toast.error(
          'You appear to be offline. Please check your internet connection.',
          {
            timeout: false,
            onClose: () => {
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
