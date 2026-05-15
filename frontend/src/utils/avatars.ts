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
 * The Centralized Avatar Orchestrator.
 * Priority: 1. Custom Photo -> 2. Colorful Circular Initial -> 3. System Default
 */
export function getAvatarUrl(
  pictureUrl: string | null | undefined,
  firstName: string | null | undefined,
  lastName: string | null | undefined,
): string {
  // 1. Use custom photo if it exists (handles both Cloud GCS and Local Media)
  if (pictureUrl) {
    if (pictureUrl.startsWith('http')) return pictureUrl
    return `${API_URL_BASE}${pictureUrl}`
  }

  // 2. Generate Initial-based Circle if name exists
  const fName = firstName || ''
  const lName = lastName || ''
  const initials = `${fName?.[0] || ''}${lName?.[0] || ''}`
  const fullName = `${fName} ${lName}`.trim()

  if (initials) {
    // We pass fullName to ensures "abc" and "aab" get different colors
    return createInitialsAvatar(initials.substring(0, 2), fullName)
  }

  // 3. Absolute Fallback
  return defaultAvatar
}

/**
 * General utility for non-avatar media files.
 */
export function buildMediaUrl(url: string | null | undefined): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${API_URL_BASE}${url}`
}
