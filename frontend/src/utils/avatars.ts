// src/utils/avatars.ts
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
 * The Centralized Avatar Orchestrator (Privacy-First Version).
 *
 * Hierarchy of Truth:
 * 1. pictureUrl: If a photo is set, show it.
 * 2. displayName: If no photo, use the chosen Public Alias (e.g., "WebR").
 * 3. username: If no Alias, use the System ID (e.g., "rahi1").
 * 4. 'U': Absolute fallback.
 */
export function getAvatarUrl(
  pictureUrl: string | null | undefined,
  displayName: string | null | undefined,
  username: string | null | undefined,
): string {
  // 1. Priority: Custom Photo (handles GCS Cloud and Local Media)
  if (pictureUrl) {
    let cleanUrl = pictureUrl

    // Self-Healing Docker Fix:
    // If the URL contains 'backend:8000', strip the internal Docker host
    // so it falls back to a relative path and loads through the Vite proxy instead.
    if (cleanUrl.includes('backend:8000')) {
      cleanUrl = cleanUrl.replace(/https?:\/\/backend:8000/, '')
    }

    if (cleanUrl.startsWith('http')) return cleanUrl
    return `${API_URL_BASE}${cleanUrl}`
  }

  // 2. Identify the 'Public Identity' for the initial and the color hash.
  // We intentionally ignore first_name/last_name here to protect user privacy.
  const nameToUse = (displayName && displayName.trim()) || (username && username.trim()) || 'U'

  // 3. Take the first character (e.g., 'W' from 'WebR' or 'R' from 'rahi1')
  const initial = nameToUse.charAt(0).toUpperCase()

  // 4. Generate the circular SVG
  // We use initials.substring(0, 1) because we only want one letter in the circle now for a cleaner look.
  return createInitialsAvatar(initial, nameToUse)
}

/**
 * General utility for non-avatar media files.
 */
export function buildMediaUrl(url: string | null | undefined): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_URL_BASE}${url}`
}
