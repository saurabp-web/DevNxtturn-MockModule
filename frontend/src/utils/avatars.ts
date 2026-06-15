import defaultAvatar from '@/assets/images/default-avatar.svg'

// Safely gets the base URL for local media files
const API_URL_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace('/api/', '')

/**
 * Professional Palette: Modern, high-contrast colors.
 * Deterministic: The same user always gets the same color.
 */
const AVATAR_COLORS = [
  '#4F46E5', // Indigo
  '#059669', // Emerald
  '#D97706', // Amber
  '#DC2626', // Red
  '#2563EB', // Blue
  '#7C3AED', // Purple
  '#DB2777', // Pink
  '#0891B2', // Cyan
  '#EA580C', // Orange
  '#475569', // Slate
]

/**
 * Generates a consistent color index based on a string (Full Name).
 */
function getColorFromName(name: string): string {
  let hash = 0
  const str = name || 'User'
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % AVATAR_COLORS.length
  return AVATAR_COLORS[index]
}

/**
 * Creates a circular SVG data URL with initials and a deterministic background color.
 */
function createInitialsAvatar(initials: string, fullName: string): string {
  const color = getColorFromName(fullName)

  // SVG Logic:
  // 1. <circle> creates the perfect circular shape you requested.
  // 2. dominant-baseline and text-anchor center the text perfectly.
  const svg = `
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="50" fill="${color}" />
      <text
        x="50%"
        y="50%"
        dominant-baseline="central"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="45"
        fill="white"
        font-weight="bold"
      >
        ${initials.toUpperCase()}
      </text>
    </svg>
  `

  return `data:image/svg+xml;base64,${btoa(svg)}`
}

/**
 * The Centralized Avatar Orchestrator (Symmetrical Hybrid & Privacy-First Version) [4].
 *
 * This hybrid signature supports both Rahi's first/last name declarations
 * and our dynamic display_name/username privacy-first lookups natively [17].
 */
export function getAvatarUrl(
  pictureUrl: string | null | undefined,
  param2?: string | null | undefined, // Can be firstName or displayName
  param3?: string | null | undefined, // Can be lastName or username
  colorSeed?: string | null,
): string {
  // 1. Priority: Custom Photo (handles GCS Cloud, Local Media, and Docker host overrides)
  if (pictureUrl) {
    let cleanUrl = pictureUrl

    // Self-Healing Docker Fix:
    if (cleanUrl.includes('backend:8000')) {
      cleanUrl = cleanUrl.replace(/https?:\/\/backend:8000/, '')
    }

    if (cleanUrl.startsWith('http')) {
      try {
        const parsed = new URL(cleanUrl)
        if (parsed.hostname === 'backend') {
          return `${parsed.pathname}${parsed.search}${parsed.hash}`
        }
      } catch {
        // Fall through
      }
      return cleanUrl
    }
    return `${API_URL_BASE}${cleanUrl}`
  }

  // 2. Fallback: Symmetrical Initials & Color seed generation [4]
  const name1 = (param2 && param2.trim()) || ''
  const name2 = (param3 && param3.trim()) || ''

  let nameToUse = 'U'
  let initial = 'U'

  if (name1 && name2) {
    nameToUse = `${name1} ${name2}`.trim()
    initial = name1.charAt(0).toUpperCase() // Matches the clean single-letter design
  } else if (name1) {
    nameToUse = name1
    initial = name1.charAt(0).toUpperCase()
  } else if (name2) {
    nameToUse = name2
    initial = name2.charAt(0).toUpperCase()
  }

  const colorKey = (colorSeed || nameToUse || 'User').trim()

  return createInitialsAvatar(initial, colorKey)
}

/**
 * General utility for non-avatar media files.
 */
export function buildMediaUrl(url: string | null | undefined): string {
  if (!url) return ''
  if (url.startsWith('http')) {
    try {
      const parsed = new URL(url)
      if (parsed.hostname === 'backend') {
        return `${parsed.pathname}${parsed.search}${parsed.hash}`
      }
    } catch {
      // Fall through and return the original URL if parsing fails.
    }
    return url
  }
  return `${API_URL_BASE}${url}`
}
