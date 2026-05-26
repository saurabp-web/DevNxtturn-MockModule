export type ChatMediaKind = 'gif' | 'sticker'

export type ChatMediaItem = {
  id: string
  kind: ChatMediaKind
  title: string
  provider: 'giphy' | 'local'
  providerId: string
  previewUrl: string
  sendUrl: string
  stillUrl: string
  width: number
  height: number
  animated: boolean
  layoutRatio: number
  tags: string[]
}

export type ChatMediaMessage = {
  type: ChatMediaKind
  gif_url: string
  sticker_url: string
  animated: boolean
  provider?: string
  provider_id?: string
}

export type ChatMediaSelection = ChatMediaItem

const RECENT_MEDIA_STORAGE_KEY = 'nxtturn.chat.recent-media'

export function normalizeRatio(width: number, height: number) {
  if (!width || !height) return 1
  return width / height
}

export function describeMediaItem(item: Pick<ChatMediaItem, 'kind' | 'title'>) {
  return `${item.kind === 'gif' ? 'GIF' : 'Sticker'}: ${item.title}`
}

export function buildChatMediaMessage(item: ChatMediaItem): ChatMediaMessage {
  return {
    type: item.kind,
    gif_url: item.kind === 'gif' ? item.sendUrl : '',
    sticker_url: item.kind === 'sticker' ? item.sendUrl : '',
    animated: item.animated,
    provider: item.provider,
    provider_id: item.providerId,
  }
}

export function isChatMediaMessage(content: unknown, messageType?: string) {
  return messageType === 'gif' || messageType === 'sticker'
}

export function getRecentMediaItems(kind: ChatMediaKind): ChatMediaItem[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(RECENT_MEDIA_STORAGE_KEY)
    const parsed = raw ? (JSON.parse(raw) as Record<string, ChatMediaItem[]>) : {}
    const items = parsed?.[kind]
    return Array.isArray(items) ? items.filter(Boolean).slice(0, 16) : []
  } catch {
    return []
  }
}

export function saveRecentMediaItem(item: ChatMediaItem) {
  if (typeof window === 'undefined' || !item?.providerId) return
  try {
    const raw = window.localStorage.getItem(RECENT_MEDIA_STORAGE_KEY)
    const parsed = raw ? (JSON.parse(raw) as Record<string, ChatMediaItem[]>) : { gif: [], sticker: [] }
    const kind = item.kind
    const current = Array.isArray(parsed?.[kind]) ? parsed[kind] : []
    const next = {
      ...parsed,
      [kind]: [item, ...current.filter((entry) => entry.providerId !== item.providerId)].slice(0, 16),
    }
    window.localStorage.setItem(RECENT_MEDIA_STORAGE_KEY, JSON.stringify(next))
  } catch {
    // ignore
  }
}
