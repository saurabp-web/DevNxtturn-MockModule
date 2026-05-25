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
    return authStore.currentUser?.id || authStore.user?.id || null
  } catch {
    return null
  }
}

function normalizeConversationRow(row: any) {
  const participants = Array.isArray(row?.participants) ? row.participants : []
  const currentUserId = getCurrentUserId()
  const partner =
    participants.find((participant) => participant?.id !== currentUserId) ||
    participants[0] ||
    {}

  return {
    ...partner,
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

async function resolveConversationId(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
) {
  const conversationId =
    typeof ref === 'number'
      ? ref
      : ref?.conversation_id || ref?.conversationId || null
  if (conversationId) return conversationId

  const username = typeof ref === 'object' ? ref?.username : null
  const userId = typeof ref === 'object' ? ref?.id : null
  const conversations = await getMessagingConversations()
  const match = conversations.find((conversation) => {
    if (username && conversation?.username === username) return true
    if (userId && Number(conversation?.id) === Number(userId)) return true
    return false
  })
  return match?.conversation_id || match?.conversationId || null
}

export async function getConversationMessages(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
  params?: Record<string, unknown>,
) {
  const conversationId = await resolveConversationId(ref)
  if (!conversationId) {
    return { messages: [], total_count: 0, has_more: false }
  }

  const primary = `/messaging/conversations/${conversationId}/messages/`
  const fallback = `/conversations/${conversationId}/messages/`
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

export async function sendConversationMessage(
  ref: number | { id?: number; conversation_id?: number; conversationId?: number; username?: string },
  payload: {
    content: string
    reply_to_message_id?: number | string | null
    recipientUsername?: string
  },
) {
  const conversationId = await resolveConversationId(ref)
  if (!conversationId) {
    const recipientUsername = payload.recipientUsername
    if (!recipientUsername) {
      throw new Error('No conversation id or recipient username available')
    }
    const response = await axiosInstance.post('/messages/send/', {
      recipient_username: recipientUsername,
      content: payload.content,
    })
    return response.data
  }

  try {
    const response = await axiosInstance.post(
      `/messaging/conversations/${conversationId}/send/`,
      payload,
    )
    return response.data
  } catch (error) {
    if (!isNotFound(error)) throw error

    const recipientUsername = payload.recipientUsername
    if (!recipientUsername) {
      throw error
    }

    const response = await axiosInstance.post('/messages/send/', {
      recipient_username: recipientUsername,
      content: payload.content,
    })
    return response.data
  }
}

export async function getUnreadMessageCountFromConversations() {
  const conversations = await getMessagingConversations()
  return conversations.reduce((sum, row) => sum + Number(row?.unread_count || 0), 0)
}
