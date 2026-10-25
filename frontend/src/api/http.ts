import { createApiClient, type Tokens, type TokenStore } from './client'

const STORAGE_KEY = 'dealership.session'
export const SESSION_EXPIRED_EVENT = 'dealership:session-expired'

/** Tokens persist in localStorage so a page reload keeps the user signed in. */
export const tokenStore: TokenStore = {
  get() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? (JSON.parse(raw) as Tokens) : null
    } catch {
      return null
    }
  },
  set(tokens) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
  },
  clear() {
    localStorage.removeItem(STORAGE_KEY)
  },
}

export const http = createApiClient({
  tokens: tokenStore,
  // Empty in development: Vite proxies /api to Django. Set VITE_API_URL when the API is elsewhere.
  baseUrl: import.meta.env.VITE_API_URL ?? '',
  onSessionExpired: () => window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT)),
})
