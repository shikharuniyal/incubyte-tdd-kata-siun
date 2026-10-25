import type { RegisterInput, User } from '../types'
import { http, tokenStore } from './http'

interface SessionResponse {
  access: string
  refresh: string
  user: User
}

function startSession(session: SessionResponse): User {
  tokenStore.set({ access: session.access, refresh: session.refresh })
  return session.user
}

export async function login(email: string, password: string): Promise<User> {
  return startSession(
    await http.request<SessionResponse>('/api/auth/login', { method: 'POST', body: { email, password }, auth: false }),
  )
}

export async function register(input: RegisterInput): Promise<User> {
  return startSession(
    await http.request<SessionResponse>('/api/auth/register', { method: 'POST', body: input, auth: false }),
  )
}

export async function logout(): Promise<void> {
  const tokens = tokenStore.get()
  tokenStore.clear()
  if (tokens) {
    // Best effort: the local session is already gone even if the server is unreachable.
    await http
      .request('/api/auth/logout', { method: 'POST', body: { refresh: tokens.refresh }, auth: false })
      .catch(() => undefined)
  }
}

/** The signed-in user, or null when there is no stored session. */
export async function currentUser(): Promise<User | null> {
  if (!tokenStore.get()) return null
  return http.request<User>('/api/auth/me')
}
