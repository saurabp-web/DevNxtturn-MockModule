type ChatRealtimeEvent =
  | 'connect'
  | 'disconnect'
  | 'message'
  | 'reaction'
  | 'typing'
  | 'seen'
  | 'status'
  | 'error'

type ChatRealtimePayload = Record<string, unknown>

type ChatRealtimeConfig = {
  userId: number | string
  token: string
  roomId: number | string
  namespace?: string
  onEvent?: (event: ChatRealtimeEvent, payload?: ChatRealtimePayload) => void
}

type Listener = (payload?: ChatRealtimePayload) => void

export class ChatRealtimeClient {
  private socket: WebSocket | null = null
  private listeners = new Map<ChatRealtimeEvent, Set<Listener>>()
  private reconnectTimer: number | null = null
  private reconnectAttempt = 0
  private connected = false
  private destroyed = false

  constructor(private config: ChatRealtimeConfig) {}

  on(event: ChatRealtimeEvent, listener: Listener) {
    const bucket = this.listeners.get(event) || new Set<Listener>()
    bucket.add(listener)
    this.listeners.set(event, bucket)
    return () => this.off(event, listener)
  }

  off(event: ChatRealtimeEvent, listener: Listener) {
    const bucket = this.listeners.get(event)
    if (!bucket) return
    bucket.delete(listener)
  }

  private emit(event: ChatRealtimeEvent, payload?: ChatRealtimePayload) {
    this.config.onEvent?.(event, payload)
    const bucket = this.listeners.get(event)
    if (!bucket) return
    for (const listener of bucket) {
      listener(payload)
    }
  }

  private getUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const base = import.meta.env.VITE_WS_BASE_URL || '/ws/'
    const namespace = this.config.namespace || 'chat'
    return `${protocol}//${host}${base}${namespace}/${this.config.roomId}/?token=${this.config.token}`
  }

  connect() {
    if (this.destroyed || this.socket || !this.config.token) return

    try {
      this.socket = new WebSocket(this.getUrl())
    } catch (error) {
      this.scheduleReconnect()
      this.emit('error', { error })
      return
    }

    this.socket.onopen = () => {
      this.connected = true
      this.reconnectAttempt = 0
      this.emit('connect')
      this.emit('status', { state: 'connected' })
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(String(event.data || '{}'))
        if (data?.message) {
          this.emit('message', data)
        } else if (data?.reaction) {
          this.emit('reaction', data.reaction)
        } else if (data?.typing) {
          this.emit('typing', data.typing)
        } else if (data?.seen) {
          this.emit('seen', data.seen)
        } else {
          this.emit('status', data)
        }
      } catch (error) {
        this.emit('error', { error })
      }
    }

    this.socket.onerror = (error) => {
      this.emit('error', { error })
      this.connected = false
    }

    this.socket.onclose = () => {
      this.connected = false
      this.socket = null
      this.emit('disconnect')
      this.emit('status', { state: 'disconnected' })
      this.scheduleReconnect()
    }
  }

  disconnect() {
    this.destroyed = true
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.connected = false
  }

  private scheduleReconnect() {
    if (this.destroyed) return
    if (this.reconnectTimer) window.clearTimeout(this.reconnectTimer)

    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 12000)
    this.reconnectAttempt += 1

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  send(event: string, payload: ChatRealtimePayload) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return false
    this.socket.send(JSON.stringify({ event, ...payload }))
    return true
  }

  sendMessage(payload: ChatRealtimePayload) {
    return this.send('message', payload)
  }

  sendReaction(payload: ChatRealtimePayload) {
    return this.send('reaction', payload)
  }

  sendTyping(payload: ChatRealtimePayload) {
    return this.send('typing', payload)
  }

  sendSeen(payload: ChatRealtimePayload) {
    return this.send('seen', payload)
  }

  isConnected() {
    return this.connected
  }
}

export function createChatRealtimeClient(config: ChatRealtimeConfig) {
  return new ChatRealtimeClient(config)
}

