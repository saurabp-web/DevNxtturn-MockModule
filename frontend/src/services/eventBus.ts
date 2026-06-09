// C:\Users\Vinay\Project\frontend\src/services/eventBus.ts
import mitt from 'mitt'

// Add all the new, specific scroll event types
type Events = {
  'navigation-started': void
  'reset-feed-form': void
  'scroll-to-top': void // For the Home Feed
  'scroll-profile-to-top': void
  'scroll-notifications-to-top': void
  'scroll-saved-posts-to-top': void
  'scroll-groups-to-top': void
  'trigger-profile-edit': string
  'connection-established': number
  'messaging-read-updated': void
  'messaging-presence-updated': { user_id: number; username?: string; is_online: boolean }
  'messaging-thread-read': {
    reader_id: number
    sender_id?: number
    updated_count?: number
    unread_count?: number
  }
}

const emitter = mitt<Events>()

export default emitter
