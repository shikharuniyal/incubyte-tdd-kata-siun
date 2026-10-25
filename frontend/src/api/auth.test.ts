import { beforeEach, describe, expect, it, vi } from 'vitest'
import { aCustomer } from '../test/fixtures'
import * as auth from './auth'
import { tokenStore } from './http'

// A plain stub (not a vi.fn spy) so a rejected request is handled exactly as in production.
const stub = vi.hoisted(() => ({
  calls: [] as unknown[][],
  respond: (async () => undefined) as (...args: unknown[]) => Promise<unknown>,
}))

vi.mock('./http', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./http')>()
  return {
    ...actual,
    http: {
      request: (...args: unknown[]) => {
        stub.calls.push(args)
        return stub.respond(...args)
      },
    },
  }
})

beforeEach(() => {
  stub.calls = []
  stub.respond = async () => undefined
})

describe('auth api', () => {
  it('login stores the token pair and returns the user', async () => {
    stub.respond = async () => ({ access: 'A', refresh: 'R', user: aCustomer() })

    const user = await auth.login('asha@example.com', 'pw')

    expect(user).toEqual(aCustomer())
    expect(tokenStore.get()).toEqual({ access: 'A', refresh: 'R' })
    expect(stub.calls).toEqual([
      ['/api/auth/login', { method: 'POST', body: { email: 'asha@example.com', password: 'pw' }, auth: false }],
    ])
  })

  it('register starts a session too', async () => {
    stub.respond = async () => ({ access: 'A2', refresh: 'R2', user: aCustomer() })

    await auth.register({ first_name: 'A', last_name: 'K', email: 'a@k.com', password: 'pw' })

    expect(tokenStore.get()).toEqual({ access: 'A2', refresh: 'R2' })
  })

  it('logout forgets the tokens even if the server cannot be reached', async () => {
    tokenStore.set({ access: 'A', refresh: 'R' })
    stub.respond = async () => {
      throw new Error('offline')
    }

    await expect(auth.logout()).resolves.toBeUndefined()

    expect(tokenStore.get()).toBeNull()
    expect(stub.calls).toEqual([['/api/auth/logout', { method: 'POST', body: { refresh: 'R' }, auth: false }]])
  })

  it('logout without a session does not call the server', async () => {
    await auth.logout()

    expect(stub.calls).toEqual([])
  })

  it('currentUser is null without a stored session and asks the API otherwise', async () => {
    expect(await auth.currentUser()).toBeNull()
    expect(stub.calls).toEqual([])

    tokenStore.set({ access: 'A', refresh: 'R' })
    stub.respond = async () => aCustomer()
    expect(await auth.currentUser()).toEqual(aCustomer())
    expect(stub.calls).toEqual([['/api/auth/me']])
  })

  it('treats unreadable stored tokens as no session', () => {
    localStorage.setItem('dealership.session', '{not json')
    expect(tokenStore.get()).toBeNull()
  })
})
