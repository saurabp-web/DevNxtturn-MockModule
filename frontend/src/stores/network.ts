import { defineStore } from 'pinia'
import { ref } from 'vue'
import axiosInstance from '@/services/axiosInstance'
import type { NetworkUser, DiscoveryResponse } from '@/types'

export const useNetworkStore = defineStore('network', () => {
  // --- STATE ---
  const followers = ref<NetworkUser[]>([])
  const following = ref<NetworkUser[]>([])
  const connections = ref<NetworkUser[]>([])
  const discoverResults = ref<DiscoveryResponse | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const pending = ref<NetworkUser[]>([])
  const mutualCache = ref<{ [username: string]: NetworkUser[] }>({})

  const nextUrls = ref({
    followers: null as string | null,
    following: null as string | null,
    connections: null as string | null,
    pending: null as string | null,
  })

  // --- ACTIONS (Corrected Paths) ---

  async function fetchFollowers(url: string | null = null) {
    isLoading.value = true
    error.value = null

    // 1. Use the provided URL (for page 2, 3...) or the default (for page 1)
    const apiUrl = url || '/network/followers/'

    try {
      const response = await axiosInstance.get(apiUrl)

      if (url) {
        // 2. APPEND: If we are loading a next page, add new results to the bottom
        followers.value = [...followers.value, ...response.data.results]
      } else {
        // 3. REFRESH: If no URL is provided, start the list fresh
        followers.value = response.data.results
      }

      // 4. Save the 'next' URL from the server so we know where the next page is
      nextUrls.value.followers = response.data.next
    } catch (err: any) {
      error.value = 'Failed to load followers'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchFollowing(url: string | null = null) {
    isLoading.value = true
    error.value = null
    const apiUrl = url || '/network/following/'
    try {
      const response = await axiosInstance.get(apiUrl)
      if (url) {
        // APPEND to existing list
        following.value = [...following.value, ...response.data.results]
      } else {
        // FRESH LOAD
        following.value = response.data.results
      }
      // Store the pointer for the next page of Following
      nextUrls.value.following = response.data.next
    } catch (err: any) {
      error.value = 'Failed to load following list'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchConnections(url: string | null = null) {
    isLoading.value = true
    error.value = null
    const apiUrl = url || '/network/connections/'
    try {
      const response = await axiosInstance.get(apiUrl)
      if (url) {
        connections.value = [...connections.value, ...response.data.results]
      } else {
        connections.value = response.data.results
      }
      // Store the pointer for the next page of Connections
      nextUrls.value.connections = response.data.next
    } catch (err: any) {
      error.value = 'Failed to load connections'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchMutualConnections(username: string, url: string | null = null) {
    // --- THE CACHE SHIELD ---
    // If we already loaded this user's mutual connections, load them from memory instantly!
    if (!url && mutualCache.value[username]) {
      connections.value = mutualCache.value[username]
      nextUrls.value.connections = null // No next page URL needed since they are pre-loaded
      return
    }

    isLoading.value = true
    error.value = null
    const apiUrl = url || `/profiles/${username}/mutual-connections/`

    try {
      const response = await axiosInstance.get(apiUrl)
      if (url) {
        connections.value = [...connections.value, ...response.data.results]
      } else {
        connections.value = response.data.results
        // Save to our memory bank for future fast clicks!
        mutualCache.value[username] = response.data.results
      }

      nextUrls.value.connections = response.data.next
    } catch (err: any) {
      error.value = 'Failed to load mutual connections'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPending(url: string | null = null) {
    isLoading.value = true
    error.value = null
    const apiUrl = url || '/network/pending/'
    try {
      const response = await axiosInstance.get(apiUrl)
      if (url) {
        pending.value = [...pending.value, ...response.data.results]
      } else {
        pending.value = response.data.results
      }
      // Store the pointer for the next page of Pending Requests
      nextUrls.value.pending = response.data.next
    } catch (err: any) {
      error.value = 'Failed to load pending requests'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDiscover() {
    isLoading.value = true
    error.value = null
    try {
      const response = await axiosInstance.get<DiscoveryResponse>('/network/discover/')
      discoverResults.value = response.data
    } catch (err: any) {
      error.value = 'Failed to load recommendations'
      console.error(err)
    } finally {
      isLoading.value = false
    }
  }

  // --- SYNC ACTION: Remove user from all suggestion buckets ---
  function forceSyncConnection(userId: any) {
    if (!discoverResults.value) return
    const targetId = Number(userId)

    // We loop through all categories (mutual_connections, alumni, etc.)
    // and filter out the user we just connected with.
    Object.keys(discoverResults.value).forEach((key) => {
      const category = key as keyof DiscoveryResponse
      const list = discoverResults.value![category]

      if (Array.isArray(list)) {
        // Remove the user from this specific bucket
        ;(discoverResults.value as any)[category] = list.filter(
          (user) => Number(user.id) !== targetId,
        )
      }
    })
    console.log('⚡ NETWORK STORE: User removed from suggestions:', targetId)
  }

  /**

    Resets the store's state, called on logout.
    */
  function reset() {
    followers.value = []
    following.value = []
    connections.value = []
    discoverResults.value = null
    error.value = null
    isLoading.value = false

    mutualCache.value = {}

    // Reset pagination URLs ---
    nextUrls.value = {
      followers: null,
      following: null,
      connections: null,
      pending: null,
    }
  }

  return {
    // State
    followers,
    following,
    connections,
    pending,
    nextUrls,
    discoverResults,
    isLoading,
    error,
    // Actions
    fetchFollowers,
    fetchFollowing,
    fetchConnections,
    fetchMutualConnections,
    fetchPending,
    fetchDiscover,
    reset,
    forceSyncConnection,
  }
})
