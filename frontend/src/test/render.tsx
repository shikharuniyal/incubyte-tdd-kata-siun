import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../auth/context'
import { ToastProvider } from '../components/ui/Toast'
import type { User } from '../types'

export function fakeAuth(user: User | null = null, overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    user,
    ready: true,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  }
}

interface Options {
  auth?: AuthContextValue
  route?: string
  path?: string
}

/** Render a page inside the router, auth and toast providers, with a marker page at "/". */
export function renderWithProviders(ui: ReactElement, { auth = fakeAuth(), route = '/', path = '/' }: Options = {}) {
  return render(
    <AuthContext.Provider value={auth}>
      <ToastProvider>
        <MemoryRouter initialEntries={[route]}>
          <Routes>
            <Route path={path} element={ui} />
            {path !== '/' && <Route path="/" element={<p>Showroom home</p>} />}
            {path !== '/login' && <Route path="/login" element={<p>Login page</p>} />}
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </AuthContext.Provider>,
  )
}
