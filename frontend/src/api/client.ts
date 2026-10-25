/**
 * A small fetch wrapper for the dealership API.
 *
 * - Sends JSON and the bearer access token.
 * - On a 401 it spends the refresh token once, stores the new pair and
 *   retries; if that fails the session is ended.
 * - Turns error bodies ({"detail": ...} or {"field": [...]}) into ApiError.
 */

export interface Tokens {
  access: string
  refresh: string
}

export interface TokenStore {
  get(): Tokens | null
  set(tokens: Tokens): void
  clear(): void
}

export class ApiError extends Error {
  readonly status: number
  readonly fieldErrors: Record<string, string[]>

  constructor(status: number, message: string, fieldErrors: Record<string, string[]> = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

export interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
  /** Send the access token (default true). */
  auth?: boolean
}

interface ClientOptions {
  tokens: TokenStore
  baseUrl?: string
  fetchImpl?: typeof fetch
  onSessionExpired?: () => void
}

export type ApiClient = ReturnType<typeof createApiClient>

export function createApiClient({ tokens, baseUrl = '', fetchImpl, onSessionExpired }: ClientOptions) {
  const doFetch = fetchImpl ?? ((input: RequestInfo | URL, init?: RequestInit) => fetch(input, init))
  let refreshInFlight: Promise<boolean> | null = null

  async function send(path: string, options: RequestOptions, accessToken?: string): Promise<Response> {
    const headers: Record<string, string> = { Accept: 'application/json', ...options.headers }
    if (options.body !== undefined) headers['Content-Type'] = 'application/json'
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`
    try {
      return await doFetch(baseUrl + path, {
        method: options.method ?? 'GET',
        headers,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
      })
    } catch {
      throw new ApiError(0, 'Cannot reach the server. Check your connection and try again.')
    }
  }

  /** Concurrent 401s share one refresh, so a refresh token is never spent twice. */
  function refreshSession(): Promise<boolean> {
    const current = tokens.get()
    if (!current) return Promise.resolve(false)
    refreshInFlight ??= (async () => {
      const response = await send('/api/auth/refresh', { method: 'POST', body: { refresh: current.refresh } })
      if (!response.ok) return false
      tokens.set((await response.json()) as Tokens)
      return true
    })().finally(() => {
      refreshInFlight = null
    })
    return refreshInFlight
  }

  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const useAuth = options.auth !== false
    let response = await send(path, options, useAuth ? tokens.get()?.access : undefined)

    if (response.status === 401 && useAuth && tokens.get()) {
      if (await refreshSession()) {
        response = await send(path, options, tokens.get()?.access)
      } else {
        tokens.clear()
        onSessionExpired?.()
      }
    }
    return parse<T>(response)
  }

  return { request }
}

async function parse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T
  const data: unknown = await response.json().catch(() => null)
  if (response.ok) return data as T
  throw errorFrom(response.status, data)
}

function errorFrom(status: number, data: unknown): ApiError {
  if (data && typeof data === 'object') {
    const body = data as Record<string, unknown>
    if (typeof body.detail === 'string') return new ApiError(status, body.detail)

    const fieldErrors: Record<string, string[]> = {}
    for (const [field, messages] of Object.entries(body)) {
      if (Array.isArray(messages)) fieldErrors[field] = messages.map(String)
    }
    const first = Object.values(fieldErrors)[0]?.[0]
    if (first) return new ApiError(status, first, fieldErrors)
  }
  const fallback = status >= 500 ? 'Something went wrong on the server. Please try again.' : `Request failed (${status}).`
  return new ApiError(status, fallback)
}

/** Plain-language message for any error thrown while calling the API. */
export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Something went wrong. Please try again.'
}
