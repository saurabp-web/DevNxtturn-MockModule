export type EmojiAssetKind = 'webp' | 'lottie'

export type EmojiAssetCandidate = {
  emoji: string
  kind: EmojiAssetKind
  source: string
  loader?: () => Promise<unknown>
}

type GlobModule = Record<string, () => Promise<unknown>>

const emojiWebpModules = import.meta.glob('../../assets/emojis/**/*.{webp,png,jpg,jpeg,gif}', {
  import: 'default',
}) as GlobModule

const emojiLottieModules = import.meta.glob('../../assets/lottie/**/*.json', {
  import: 'default',
}) as GlobModule

const KNOWN_EMOJI_KIND: Record<string, EmojiAssetKind> = {
  '😀': 'webp',
  '😭': 'lottie',
  '🔥': 'webp',
  '❤️': 'lottie',
  '❤': 'lottie',
}

function toCodepoints(value: string) {
  return Array.from(String(value || ''))
    .map((char) => char.codePointAt(0)?.toString(16))
    .filter(Boolean)
    .join('-')
}

function buildCandidates(emoji: string) {
  const normalized = String(emoji || '').trim()
  if (!normalized) return []

  const stems = new Set<string>()
  const slug = toCodepoints(normalized)
  if (slug) stems.add(slug)

  const noVariation = slug.replace(/-fe0f/g, '')
  if (noVariation) stems.add(noVariation)

  const noJoiners = slug.replace(/-200d/g, '-')
  if (noJoiners) stems.add(noJoiners)

  return Array.from(stems)
}

function resolveGlob(modules: GlobModule, stems: string[], extension: string) {
  const moduleEntry = Object.entries(modules).find(([path]) =>
    stems.some((stem) => path.endsWith(`/${stem}.${extension}`)),
  )

  if (!moduleEntry) return null
  const [path, loader] = moduleEntry
  return { path, loader }
}

export function emojiToAssetSlug(emoji: string) {
  return toCodepoints(emoji)
}

export function resolveEmojiAsset(emoji: string): EmojiAssetCandidate | null {
  const candidates = buildCandidates(emoji)
  if (!candidates.length) return null

  const preferredKind = KNOWN_EMOJI_KIND[emoji] || 'webp'
  const orderedKinds: EmojiAssetKind[] =
    preferredKind === 'lottie' ? ['lottie', 'webp'] : ['webp', 'lottie']

  for (const kind of orderedKinds) {
    const modules = kind === 'lottie' ? emojiLottieModules : emojiWebpModules
    const extension = kind === 'lottie' ? 'json' : 'webp'
    const resolved = resolveGlob(modules, candidates, extension)

    if (resolved) {
      return {
        emoji,
        kind,
        source: resolved.path,
        loader: resolved.loader,
      }
    }
  }

  return null
}

export const QUICK_EMOJIS = ['😀', '😭', '🔥', '❤️', '👍', '😍']

