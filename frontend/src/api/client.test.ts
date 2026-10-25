import { describe, expect, it, vi } from 'vitest'
import { ApiError, createApiClient, type Tokens, type TokenStore } from './client'

function memoryStore(initial: Tokens | null = null): TokenStore {
  let tokens = initial
  return {
    get: () => tokens,
    set: (next) => {
      tokens = next
    },
    clear: () => {
      tokens = null
    },
  }
}

function jsonResponse(status: number, body?: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('api client', () => {
  it('sends JSON with the access token', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }))
    const api = createApiClient({ tokens: memoryStore({ access: 'A1', refresh: 'R1' }), fetchImpl })

    const result = await api.request('/api/vehicles', { method: 'POST', body: { make: 'Toyota' } })

    expect(result).toEqual({ ok: true })
    const [url, init] = fetchImpl.mock.calls[0]
    expect(url).toBe('/api/vehicles')
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ make: 'Toyota' }))
    expect(init.headers.Authorization).toBe('Bearer A1')
    expect(init.headers['Content-Type']).toBe('application/json')
  })

  it('omits the token for public endpoints', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, {}))
    const api = createApiClient({ tokens: memoryStore({ access: 'A1', refresh: 'R1' }), fetchImpl })

    await api.request('/api/auth/login', { method: 'POST', body: {}, auth: false })

    expect(fetchImpl.mock.calls[0][1].headers.Authorization).toBeUndefined()
  })

  it('refreshes an expired access token once and retries the request', async () => {
    const store = memoryStore({ access: 'OLD', refresh: 'R1' })
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid or expired token.' }))
      .mockResolvedValueOnce(jsonResponse(200, { access: 'NEW', refresh: 'R2' }))
      .mockResolvedValueOnce(jsonResponse(200, [{ id: 1 }]))
    const api = createApiClient({ tokens: store, fetchImpl })

    const result = await api.request('/api/vehicles')

    expect(result).toEqual([{ id: 1 }])
    expect(fetchImpl.mock.calls[1][0]).toBe('/api/auth/refresh')
    expect(fetchImpl.mock.calls[1][1].body).toBe(JSON.stringify({ refresh: 'R1' }))
    expect(fetchImpl.mock.calls[2][1].headers.Authorization).toBe('Bearer NEW')
    expect(store.get()).toEqual({ access: 'NEW', refresh: 'R2' })
  })

  it('ends the session when the refresh token is rejected', async () => {
    const store = memoryStore({ access: 'OLD', refresh: 'R1' })
    const onSessionExpired = vi.fn()
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'expired' }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: 'Invalid or expired refresh token.' }))
    const api = createApiClient({ tokens: store, fetchImpl, onSessionExpired })

    await expect(api.request('/api/vehicles')).rejects.toMatchObject({ status: 401 })
    expect(store.get()).toBeNull()
    expect(onSessionExpired).toHaveBeenCalledOnce()
  })

  it('turns an error detail into an ApiError message', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(409, { detail: 'Toyota Corolla is out of stock.' }))
    const api = createApiClient({ tokens: memoryStore(), fetchImpl })

    const error = await api.request('/api/vehicles/1/purchase', { method: 'POST' }).catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(409)
    expect(error.message).toBe('Toyota Corolla is out of stock.')
  })

  it('exposes field validation errors', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(400, { email: ['An account with this email already exists.'] }))
    const api = createApiClient({ tokens: memoryStore(), fetchImpl })

    const error = await api.request('/api/auth/register', { method: 'POST', body: {}, auth: false }).catch((e) => e)

    expect(error.fieldErrors).toEqual({ email: ['An account with this email already exists.'] })
    expect(error.message).toBe('An account with this email already exists.')
  })

  it('returns undefined for 204 No Content', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    const api = createApiClient({ tokens: memoryStore({ access: 'A', refresh: 'R' }), fetchImpl })

    await expect(api.request('/api/vehicles/1', { method: 'DELETE' })).resolves.toBeUndefined()
  })

  it('reports network failures in plain language', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    const api = createApiClient({ tokens: memoryStore(), fetchImpl })

    await expect(api.request('/api/vehicles')).rejects.toThrow('Cannot reach the server')
  })
})
