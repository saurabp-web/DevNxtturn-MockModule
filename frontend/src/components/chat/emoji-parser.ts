export type MessageToken =
  | { type: 'text'; value: string }
  | { type: 'link'; value: string; href: string }
  | { type: 'emoji'; value: string }

const URL_PATTERN = /(?:https?:\/\/|www\.)[^\s<]+/gi
const EMOJI_PATTERN =
  /(?:\p{Regional_Indicator}{2}|[#*0-9]\uFE0F?\u20E3|\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?(?:\u200D\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?)*)/gu

function escapeTrailingPunctuation(url: string) {
  let clean = url
  let trailing = ''

  while (/[),.!?:;]$/.test(clean)) {
    trailing = clean.slice(-1) + trailing
    clean = clean.slice(0, -1)
  }

  return { clean, trailing }
}

function normalizeHref(raw: string) {
  if (raw.startsWith('http://') || raw.startsWith('https://')) return raw
  return `https://${raw}`
}

const URL_MATCHER = /^(?:https?:\/\/|www\.)[^\s<]+$/i
const EMOJI_MATCHER =
  /^(?:\p{Regional_Indicator}{2}|[#*0-9]\uFE0F?\u20E3|\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?(?:\u200D\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?)*)$/u

export function tokenizeMessageText(text: string): MessageToken[] {
  const value = String(text || '')
  const tokens: MessageToken[] = []
  const combined = new RegExp(`${URL_PATTERN.source}|${EMOJI_PATTERN.source}|\\n`, 'giu')
  let lastIndex = 0

  for (const match of value.matchAll(combined)) {
    const index = match.index || 0
    if (index > lastIndex) {
      tokens.push({ type: 'text', value: value.slice(lastIndex, index) })
    }

    const segment = match[0]
    if (segment === '\n') {
      tokens.push({ type: 'text', value: '\n' })
    } else if (URL_MATCHER.test(segment)) {
      const { clean, trailing } = escapeTrailingPunctuation(segment)
      const href = normalizeHref(clean)
      tokens.push({ type: 'link', value: clean, href })
      if (trailing) {
        tokens.push({ type: 'text', value: trailing })
      }
    } else if (EMOJI_MATCHER.test(segment)) {
      tokens.push({ type: 'emoji', value: segment })
    } else {
      tokens.push({ type: 'text', value: segment })
    }

    lastIndex = index + segment.length
  }

  if (lastIndex < value.length) {
    tokens.push({ type: 'text', value: value.slice(lastIndex) })
  }

  return tokens
}

export function isEmojiOnlyMessage(tokens: MessageToken[]) {
  const hasRenderableText = tokens.some(
    (token) => token.type === 'text' && token.value.trim().length > 0,
  )
  const hasLink = tokens.some((token) => token.type === 'link')
  const emojiCount = tokens.filter((token) => token.type === 'emoji').length
  return emojiCount > 0 && !hasRenderableText && !hasLink
}

export function getEmojiCount(tokens: MessageToken[]) {
  return tokens.filter((token) => token.type === 'emoji').length
}
