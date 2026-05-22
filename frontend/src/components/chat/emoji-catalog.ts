import emojiData from '@emoji-mart/data'

export type EmojiToneIndex = 0 | 1 | 2 | 3 | 4 | 5

export type EmojiRecord = {
  alias: string
  id: string
  name: string
  native: string
  keywords: string[]
  categoryId: string
  hasSkinTones: boolean
  skins: string[]
}

export type EmojiCategory = {
  id: string
  label: string
  icon: string
}

const CATEGORY_META: Record<string, EmojiCategory> = {
  people: { id: 'people', label: 'Smileys', icon: '🙂' },
  nature: { id: 'nature', label: 'Nature', icon: '🌿' },
  foods: { id: 'foods', label: 'Food', icon: '🍔' },
  activity: { id: 'activity', label: 'Activity', icon: '⚽' },
  places: { id: 'places', label: 'Places', icon: '📍' },
  objects: { id: 'objects', label: 'Objects', icon: '💡' },
  symbols: { id: 'symbols', label: 'Symbols', icon: '❤️' },
  flags: { id: 'flags', label: 'Flags', icon: '🚩' },
}

const emojiDataset = emojiData as {
  categories?: Array<{ id: string; emojis?: string[] }>
  emojis?: Record<string, { id?: string; name?: string; keywords?: string[]; skins?: Array<{ native?: string }> }>
}

export const EMOJI_CATEGORIES: EmojiCategory[] = (emojiDataset.categories || []).map(
  (category: { id: string }) =>
    CATEGORY_META[category.id] || {
      id: category.id,
      label: category.id,
      icon: '•',
    },
)

export const QUICK_REACTIONS = ['👍', '❤️', '😂', '🔥', '😍', '🎉']
export const RECENT_EMOJI_STORAGE_KEY = 'loopline.chat.recent-emojis'
export const FAVORITE_EMOJIS = ['😀', '😂', '😍', '❤️', '🔥', '🎉', '👍', '🙏', '🥳', '😭', '😎', '🤔']
export const HAND_ACTION_EMOJIS = [
  '👋',
  '🤚',
  '🖐️',
  '✋',
  '🖖',
  '🫱',
  '🫲',
  '🫳',
  '🫴',
  '🫰',
  '🤞',
  '✌️',
  '🤟',
  '🤘',
  '🤙',
  '👌',
  '🤌',
  '🤝',
  '👍',
  '👎',
  '✊',
  '👊',
  '🤛',
  '🤜',
  '👏',
  '🙌',
  '👐',
  '🤲',
  '🙏',
  '☝️',
  '👈',
  '👉',
  '👆',
  '👇',
  '🫵',
  '🫶',
  '💅',
]

const skinToneOrder: EmojiToneIndex[] = [0, 1, 2, 3, 4, 5]

function getNativeSkin(skins: { native?: string }[] | undefined, index: EmojiToneIndex) {
  if (!skins || !skins.length) return ''
  const toneIndex = skinToneOrder[index] ?? 0
  return skins[Math.min(toneIndex, skins.length - 1)]?.native || skins[0]?.native || ''
}

export function getRecentEmojis(): string[] {
  if (typeof window === 'undefined') return []

  try {
    const raw = window.localStorage.getItem(RECENT_EMOJI_STORAGE_KEY)
    const parsed = raw ? (JSON.parse(raw) as string[]) : []
    return Array.isArray(parsed) ? parsed.filter(Boolean).slice(0, 24) : []
  } catch {
    return []
  }
}

export function saveRecentEmoji(emoji: string) {
  if (typeof window === 'undefined' || !emoji) return

  try {
    const current = getRecentEmojis()
    const next = [emoji, ...current.filter((item) => item !== emoji)].slice(0, 24)
    window.localStorage.setItem(RECENT_EMOJI_STORAGE_KEY, JSON.stringify(next))
  } catch {
    // Ignore storage failures.
  }
}

function buildEmojiRecord(alias: string, categoryId: string): EmojiRecord | null {
  const entry = (emojiDataset.emojis || {})[alias]
  if (!entry) return null

  const skins = Array.isArray(entry.skins) ? entry.skins : []
  const nativeSkins = skins.map((skin: { native?: string }) => skin?.native || '').filter(Boolean)
  const native = nativeSkins[0] || ''

  if (!native) return null

  return {
    alias,
    id: entry.id || alias,
    name: entry.name || alias,
    native,
    keywords: Array.isArray(entry.keywords) ? entry.keywords : [],
    categoryId,
    hasSkinTones: nativeSkins.length > 1,
    skins: nativeSkins,
  }
}

export const EMOJI_CATALOG: Record<string, EmojiRecord> = {}
export const CATEGORY_EMOJIS: Record<string, EmojiRecord[]> = {}

for (const category of emojiDataset.categories || []) {
  CATEGORY_EMOJIS[category.id] = []

  for (const alias of category.emojis || []) {
    const record = buildEmojiRecord(alias, category.id)
    if (!record) continue
    EMOJI_CATALOG[alias] = record
    CATEGORY_EMOJIS[category.id].push(record)
  }
}

export function getEmojiNative(alias: string, tone: EmojiToneIndex = 0) {
  const record = EMOJI_CATALOG[alias]
  if (!record) return alias
  if (!record.hasSkinTones) return record.native
  return getNativeSkin((emojiDataset.emojis || {})[alias]?.skins, tone) || record.native
}

export function getEmojiByNative(native: string) {
  const value = String(native || '').trim()
  return Object.values(EMOJI_CATALOG).find((record) => record.native === value || record.skins.includes(value)) || null
}

export function searchEmojiCatalog(query: string) {
  const needle = String(query || '').trim().toLowerCase()
  if (!needle) return []

  const results: EmojiRecord[] = []
  const seen = new Set<string>()

  for (const category of EMOJI_CATEGORIES) {
    for (const record of CATEGORY_EMOJIS[category.id] || []) {
      const haystack = [record.alias, record.name, record.native, ...record.keywords].join(' ').toLowerCase()
      if (!haystack.includes(needle) || seen.has(record.alias)) continue
      seen.add(record.alias)
      results.push(record)
      if (results.length >= 256) return results
    }
  }

  return results
}

export function isCelebrationEmoji(emoji: string) {
  return ['❤️', '❤', '🔥', '😍', '😂', '🎉', '👍', '💖', '💘', '🥰'].includes(String(emoji || '').trim())
}

export function normalizeEmojiInput(emoji: string) {
  const input = String(emoji || '').trim()
  if (!input) return ''

  const record = getEmojiByNative(input)
  return record?.native || input
}
