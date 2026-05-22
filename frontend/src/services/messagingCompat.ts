import axiosInstance from '@/services/axiosInstance'

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
  return rows.map((row) => ({
    ...row,
    unread_count: Number(row?.unread_count || 0),
    last_message: row?.last_message || '',
    last_message_time: row?.last_message_time || row?.updated_at || row?.created_at || null,
    last_message_is_mine: Boolean(row?.last_message_is_mine),
  }))
}

export async function getMessagingUsers(query?: string) {
  const response = await requestWithFallback<any>(
    '/messaging/users/',
    '/search/users/',
    query ? { q: query } : undefined,
  )
  return unwrapList<any>(response.data)
}

export async function getConversationMessages(userId: number, params?: Record<string, unknown>) {
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

export async function sendConversationMessage(
  userId: number,
  payload: {
    content: string
    reply_to_message_id?: number | string | null
    recipientUsername?: string
  },
) {
  try {
    const response = await axiosInstance.post(
      `/messaging/conversations/${userId}/send/`,
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
