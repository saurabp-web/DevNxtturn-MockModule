// src/services/adminAuth.ts
//
// Separate from axiosInstance.ts on purpose: the rest of the app
// authenticates with a Token header (see stores/auth.ts), but the
// Exam Admin panel is gatekept by Django's own /admin/login/ page,
// which only sets a session cookie — no token. This file checks
// that session cookie directly instead of forcing a Token header.

import axios from 'axios'

const rawApiBaseURL = import.meta.env.VITE_API_BASE_URL || '/api/'
const apiBaseURL = rawApiBaseURL.replace(/\/+$|\/+(?=\?)|\/+(?=#)/g, '/')

export interface AdminSessionUser {
  id: number
  username: string
  email: string
  is_staff: boolean
  is_superuser: boolean
}

/**
 * Checks whether the current browser session (Django session cookie,
 * set by /admin/login/) is authenticated and staff. Returns null if
 * not logged in via that session.
 */
export async function fetchAdminSessionUser(): Promise<AdminSessionUser | null> {
  try {
    const res = await axios.get<AdminSessionUser>(`${apiBaseURL}admin/session-user/`, {
      withCredentials: true, // send the Django session cookie
      // Deliberately no Authorization header here — we want to know
      // if the SESSION (not a token) is authenticated. This endpoint
      // is isolated from the app's token-based endpoints (see
      // AdminSessionUserView) so it never interferes with regular
      // token login/CSRF behavior.
    })
    return res.data
  } catch {
    return null
  }
}

/**
 * Redirects the browser to Django's real admin login page, with
 * `next` pointing back to wherever the user was trying to go in the
 * Vue app (e.g. /exam-admin).
 */
export function redirectToDjangoAdminLogin(returnPath: string) {
  const next = encodeURIComponent(returnPath)
  window.location.href = `/admin/login/?next=${next}`
}