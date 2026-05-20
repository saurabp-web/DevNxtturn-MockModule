// C:\Users\Vinay\Project\frontend\src\stores\notification.ts
// --- DEFINITIVE, COMPLETE & CORRECTED VERSION ---

import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useToast } from 'vue-toastification'
import type { User } from './auth'
import { useAuthStore } from './auth'
import eventBus from '@/services/eventBus'
// --- Interface Definitions ---
export interface NotificationActor extends User {}
export interface NotificationRelatedObject {
  type: string
  id: number
  display_text: string
  object_id?: number
  slug?: string
}
export interface Notification {
  id: number
  actor: NotificationActor
  verb: string
  notification_type: string
  target: NotificationRelatedObject | null
  action_object: NotificationRelatedObject | null
  timestamp: string
  is_read: boolean
  context_snippet: string | null
  is_following_back: boolean
  is_declined?: boolean
}
export interface PaginatedNotificationResponse {
  count: number
  next: string | null
  previous: string | null
  results: Notification[]
}

export const useNotificationStore = defineStore('notification', () => {
  const toast = useToast()
  const authStore = useAuthStore()

  const notifications = ref<Notification[]>([])
  const unreadCount = ref<number>(0)
  const isLoadingList = ref<boolean>(false)
  const isLoadingCount = ref<boolean>(false)
  const error = ref<string | null>(null)
  const pagination = ref({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
    totalPages: 0,
    pageSize: 10,
  })
  const ITEMS_PER_PAGE_NOTIFICATIONS = 10
  const hasLoadedInitialList = ref<boolean>(false)

  async function fetchUnreadCount() {
    if (!authStore.isAuthenticated) return

    isLoadingCount.value = true
    try {
      const response = await axiosInstance.get<{ unread_count: number }>(
        '/notifications/unread-count/',
      )
      unreadCount.value = response.data.unread_count
    } catch (err: any) {
      console.error('NotificationStore: Error fetching unread count:', err)
      unreadCount.value = 0
    } finally {
      isLoadingCount.value = false
    }
  }

  async function fetchNotifications(page: number = 1) {
    if (!authStore.isAuthenticated) {
      error.value = 'You must be logged in to view notifications.'
      return
    }

    isLoadingList.value = true
    error.value = null
    if (page === 1) {
    }
    try {
      const response = await axiosInstance.get<PaginatedNotificationResponse>('/notifications/', {
        params: { page: page },
      })
      const data = response.data
      if (page === 1) {
        notifications.value = data.results
      } else {
        notifications.value.push(...data.results)
      }
      pagination.value.count = data.count
      pagination.value.next = data.next
      pagination.value.previous = data.previous
      pagination.value.currentPage = page
      pagination.value.totalPages =
        data.count > 0 ? Math.ceil(data.count / ITEMS_PER_PAGE_NOTIFICATIONS) : 0

      hasLoadedInitialList.value = true
    } catch (err: any) {
      console.error('NotificationStore: Error fetching notifications:', err)
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch notifications.'
    } finally {
      isLoadingList.value = false
    }
  }

  async function markNotificationsAsRead(notificationIds: number[], skipFetchCount = false) {
    if (!authStore.isAuthenticated) return { success: false }
    if (!notificationIds || notificationIds.length === 0) return { success: false }
    try {
      await axiosInstance.post('/notifications/mark-as-read/', {
        notification_ids: notificationIds,
      })
      notifications.value.forEach((n) => {
        if (notificationIds.includes(n.id) && !n.is_read) {
          n.is_read = true
        }
      })

      // Only fetch the unread count if we didn't explicitly ask to skip it
      if (!skipFetchCount) {
        await fetchUnreadCount()
      }

      return { success: true }
    } catch (err: any) {
      console.error('NotificationStore: Error marking notifications as read:', err)
      error.value = err.response?.data?.detail || 'Failed to mark notifications as read.'
      return { success: false, error: error.value }
    }
  }

  async function markAllAsRead() {
    if (!authStore.isAuthenticated) return { success: false }
    try {
      await axiosInstance.post('/notifications/mark-all-as-read/')
      notifications.value.forEach((notification) => {
        notification.is_read = true
      })
      unreadCount.value = 0
      return { success: true }
    } catch (err: any) {
      console.error('NotificationStore: Error marking all notifications as read:', err)
      error.value = err.response?.data?.detail || 'Failed to mark all notifications as read.'
      return { success: false, error: error.value }
    }
  }

  function addLiveNotification(newNotification: Notification) {
    // 1. THE CLICKER'S SHIELD: Check if we already transformed a row for this user.
    // If we have a row from this person that is already marked as 'is_following_back',
    // it means WE were the one who clicked the button. We don't want a duplicate at the top.
    const isSelfActionDuplicate = notifications.value.some(
      (n) =>
        Number(n.actor.id) === Number(newNotification.actor.id) && n.is_following_back === true,
    )

    if (isSelfActionDuplicate && newNotification.notification_type === 'connection_accepted') {
      console.log('🚫 STORE: Ignoring duplicate WebSocket for clicker to preserve scroll position.')
      return // EXIT HERE: User 2 stays looking at their row at position #20.
    }

    // 2. THE WAITER'S EXPERIENCE: If we reached here, this is a fresh alert for the user.
    // We clean up any old 'pending' or 'follow' rows from this person first.
    if (newNotification.notification_type === 'connection_accepted') {
      notifications.value = notifications.value.filter((n) => {
        const isSamePerson = Number(n.actor.id) === Number(newNotification.actor.id)
        const isOldRow = ['connection_request', 'follow'].includes(n.notification_type)
        return !(isSamePerson && isOldRow)
      })
    }

    // 3. ADD TO TOP: Standard logic for new alerts
    notifications.value.unshift(newNotification)
    unreadCount.value++

    // 4. TOAST: Only show the popup toast for true new alerts (Waiter experience)
    toast.info(`${newNotification.actor.username} ${newNotification.verb}`)
  }

  function resetState() {
    notifications.value = []
    unreadCount.value = 0
    isLoadingList.value = false
    isLoadingCount.value = false
    error.value = null
    pagination.value = {
      count: 0,
      next: null,
      previous: null,
      currentPage: 1,
      totalPages: 0,
      pageSize: 10,
    }
    hasLoadedInitialList.value = false
  }

  async function forceSyncConnection(userId: any) {
    const targetId = Number(userId)

    // 1. Find all UNREAD notifications for this user in memory
    const unreadItems = notifications.value.filter(
      (n) => Number(n.actor.id) === targetId && !n.is_read,
    )

    // 2. If we found unread items, tell the backend to mark them read
    if (unreadItems.length > 0) {
      const ids = unreadItems.map((n) => n.id)
      await markNotificationsAsRead(ids) // This syncs the Database
      console.log(`📉 STORE: Sent mark-as-read to DB for IDs:`, ids)
    }

    // 3. Update the rows IN-PLACE for immediate visual feedback
    notifications.value.forEach((n) => {
      if (Number(n.actor.id) === targetId) {
        n.is_read = true // Ensure it's marked read locally
        if (n.notification_type === 'follow') {
          n.is_following_back = true
          n.verb = 'you followed back and established a connection'
        } else if (n.notification_type === 'connection_request') {
          n.is_following_back = true
          n.verb = 'is now connected with you'
        }
      }
    })

    // 4. THE MASTER SYNC: Re-fetch the count from the server to be 100% sure
    await fetchUnreadCount()
    console.log('✨ STORE: In-place transformation and Count Sync complete.')
  }

  function removeNotificationById(notificationId: number) {
    // 1. Find the specific notification in memory
    const target = notifications.value.find((n) => n.id === notificationId)
    if (!target) return

    // 2. THE SAFETY NET: If the user just clicked a button, they are seeing
    // local feedback (is_declined or is_following_back).
    // We skip the immediate removal so they have time to read it.
    if (target.is_declined || target.is_following_back) {
      console.log('⏳ STORE: Preservation mode active. Skipping real-time wipe to show feedback.')
      return
    }

    // 3. Otherwise, perform the normal real-time removal
    if (!target.is_read && unreadCount.value > 0) {
      unreadCount.value--
    }
    notifications.value = notifications.value.filter((n) => n.id !== notificationId)
  }

  async function declineNotificationInPlace(notificationId: number) {
    const target = notifications.value.find((n) => n.id === notificationId)
    if (!target) return

    // 1. Keep the previous read state before we update it
    const wasUnread = !target.is_read

    // 2. Set local feedback state immediately so the WebSocket ignore logic activates
    target.is_declined = true
    target.is_read = true
    target.verb = 'declined the request'

    // 3. If it was unread, update the count locally and sync with the database
    if (wasUnread) {
      if (unreadCount.value > 0) unreadCount.value--
      await markNotificationsAsRead([notificationId])
    }

    console.log(`📉 STORE: Local decline applied to ID: ${notificationId}. Database synced.`)
  }

  return {
    notifications,
    unreadCount,
    isLoadingList,
    isLoadingCount,
    error,
    pagination,
    hasLoadedInitialList,
    fetchNotifications,
    fetchUnreadCount,
    markNotificationsAsRead,
    markAllAsRead,
    addLiveNotification,
    resetState,
    forceSyncConnection,
    declineNotificationInPlace,

    removeNotificationById,
  }
})
