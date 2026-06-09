import axiosInstance from '@/services/axiosInstance'
import { useAuthStore } from '@/stores/auth'

type FallbackResult<T> = {
  data: T
}

function isNotFound(error: unknown) {
  return Boolean(
    error &&
      typeof error === 'object' &&
      'response' in error &&
      (error as { response?: { status?: number } }).response?.status === 404,
  )
}

function unwrapList<T>(data: any): T[] {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.messages)) return data.messages
  return []
}

function getCurrentUserId() {
  try {
    const authStore = useAuthStore()
    return authStore.currentUser?.id || (authStore as unknown as { user?: { id?: number } }).user?.id || null
  } catch {
    return null
  }
}

function normalizeConversationRow(row: any) {
  const participants = Array.isArray(row?.participants) ? row.participants : []
  const currentUserId = getCurrentUserId()
  const partner =
    participants.find((participant: any) => participant?.id !== currentUserId) ||
    participants[0] ||
    {}
  const username = partner?.username || row?.username || partner?.user?.username || ''

  return {
    ...partner,
    username,
    id: partner?.id ?? row?.id,
    conversation_id: row?.id,
    conversationId: row?.id,
    participants,
    unread_count: Number(row?.unread_count || 0),
    last_message: row?.last_message || '',
    last_message_time: row?.last_message_time || row?.updated_at || row?.created_at || null,
    last_message_is_mine: Boolean(row?.last_message_is_mine),
  }
}

async function requestWithFallback<T>(
  primaryUrl: string,
  fallbackUrl?: string,
  params?: Record<string, unknown>,
): Promise<FallbackResult<T>> {
  try {
    const response = await axiosInstance.get<T>(primaryUrl, { params })
    return { data: response.data }
  } catch (error) {
    if (!fallbackUrl || !isNotFound(error)) {
      throw error
    }
    const response = await axiosInstance.get<T>(fallbackUrl, { params })
    return { data: response.data }
  }
}

export async function getMessagingConversations() {
  const response = await requestWithFallback<any>(
    '/messaging/conversations/',
    '/conversations/',
  )
  const rows = unwrapList<any>(response.data)
  return rows.map(normalizeConversationRow)
}

export async function getMessagingUsers(query?: string) {
  const response = await requestWithFallback<any>(
    '/messaging/users/',
    '/search/users/',
    query ? { q: query } : undefined,
  )
  return unwrapList<any>(response.data)
}

async function resolveConversationUserId(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
) {
  const directUserId =
    typeof ref === 'number'
      ? ref
      : ref?.id || ref?.conversation_id || ref?.conversationId || null
  if (directUserId) return directUserId

  const username = typeof ref === 'object' ? ref?.username : null
  if (!username) return null

  const conversations = await getMessagingConversations()
  const match = conversations.find((conversation) => {
    if (username && conversation?.username === username) return true
    return false
  })
  if (match?.id) return match.id

  const users = await getMessagingUsers(username)
  const userMatch = users.find((user) => user?.username === username)
  return userMatch?.id || null
}

export async function getConversationMessages(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
  params?: Record<string, unknown>,
) {
  const userId = await resolveConversationUserId(ref)
  if (!userId) {
    return { messages: [], total_count: 0, has_more: false }
  }

  const primary = `/messaging/conversations/${userId}/messages/`
  const fallback = `/conversations/${userId}/messages/`
  const response = await requestWithFallback<any>(primary, fallback, params)
  const data = response.data || {}
  if (Array.isArray(data)) {
    return { messages: data, total_count: data.length, has_more: false }
  }
  return {
    messages: Array.isArray(data?.messages) ? data.messages : unwrapList<any>(data),
    total_count: Number(data?.total_count || 0),
    has_more: Boolean(data?.has_more),
  }
}

export async function markConversationAsRead(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
) {
  const userId = await resolveConversationUserId(ref)
  if (!userId) return null

  const primary = `/messaging/conversations/${userId}/read/`
  const fallback = `/conversations/${userId}/read/`

  try {
    const response = await axiosInstance.post(primary)
    return response.data
  } catch (error) {
    if (!isNotFound(error)) throw error
    const response = await axiosInstance.post(fallback)
    return response.data
  }
}

export async function sendConversationMessage(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
  payload: {
    content: string
    reply_to_message_id?: number | string | null
    recipientUsername?: string
    message_type?: 'text' | 'gif' | 'sticker' | 'file'
    gif_url?: string
    sticker_url?: string
    provider?: string
    provider_id?: string
    animated?: boolean
    media_title?: string
  },
) {
  const userId = await resolveConversationUserId(ref)
  if (!userId) {
    throw new Error('No recipient user id available')
  }

  try {
    const response = await axiosInstance.post(`/messaging/conversations/${userId}/send/`, payload)
    return response.data
  } catch (error) {
    if (!isNotFound(error)) throw error
    const response = await axiosInstance.post(`/conversations/${userId}/send/`, payload)
    return response.data
  }
}

export async function getUnreadMessageCountFromConversations() {
  const conversations = await getMessagingConversations()
  return conversations.reduce((sum, row) => sum + Number(row?.unread_count || 0), 0)
}
