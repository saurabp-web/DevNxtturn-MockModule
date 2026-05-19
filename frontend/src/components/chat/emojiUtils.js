const DEFAULT_EMOJI_WEBP_BASE_URL =
  import.meta.env.VITE_EMOJI_WEBP_BASE_URL || 'https://fonts.gstatic.com/s/e/notoemoji/latest'

export const EMOJI_WEBP_BASE_URL = DEFAULT_EMOJI_WEBP_BASE_URL.replace(/\/$/, '')

export function emojiToAssetSlug(emoji) {
  return Array.from(String(emoji || ''))
    .map((char) => char.codePointAt(0)?.toString(16))
    .filter(Boolean)
    .join('-')
}

export function getEmojiWebpUrl(emoji) {
  if (!EMOJI_WEBP_BASE_URL) return ''
  const slug = emojiToAssetSlug(emoji)
  if (!slug) return ''
  return `${EMOJI_WEBP_BASE_URL}/${slug}/512.webp`
}
