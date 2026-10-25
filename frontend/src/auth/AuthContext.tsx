import { useEffect, useMemo, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { SESSION_EXPIRED_EVENT } from '../api/http'
import type { User } from '../types'
import { AuthContext, type AuthContextValue } from './context'

/** Holds the signed-in user and restores the session from storage on page load. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let active = true
    authApi
      .currentUser()
      .then((current) => active && setUser(current))
      .catch(() => active && setUser(null))
      .finally(() => active && setReady(true))

    const onExpired = () => setUser(null)
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired)
    return () => {
      active = false
      window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      ready,
      async login(email, password) {
        const signedIn = await authApi.login(email, password)
        setUser(signedIn)
        return signedIn
      },
      async register(input) {
        const created = await authApi.register(input)
        setUser(created)
        return created
      },
      async logout() {
        await authApi.logout()
        setUser(null)
      },
    }),
    [user, ready],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
