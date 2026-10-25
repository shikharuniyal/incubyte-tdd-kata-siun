import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as authApi from '../api/auth'
import { SESSION_EXPIRED_EVENT } from '../api/http'
import { aCustomer } from '../test/fixtures'
import { AuthProvider } from './AuthContext'
import { useAuth } from './context'
import { RequireAuth } from './RequireAuth'

vi.mock('../api/auth')
const api = vi.mocked(authApi)

function WhoAmI() {
  const { user, login, logout } = useAuth()
  return (
    <div>
      <p>{user ? `Signed in as ${user.name}` : 'Signed out'}</p>
      <button onClick={() => void login('a@b.c', 'pw')}>login</button>
      <button onClick={() => void logout()}>logout</button>
    </div>
  )
}

function renderApp(route = '/') {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/login" element={<WhoAmI />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <p>Private showroom</p>
              </RequireAuth>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

beforeEach(() => vi.resetAllMocks())

describe('AuthProvider and RequireAuth', () => {
  it('restores a stored session and shows protected pages', async () => {
    api.currentUser.mockResolvedValue(aCustomer())

    renderApp('/')

    expect(await screen.findByText('Private showroom')).toBeInTheDocument()
  })

  it('sends visitors without a session to the login page', async () => {
    api.currentUser.mockResolvedValue(null)

    renderApp('/')

    expect(await screen.findByText('Signed out')).toBeInTheDocument()
    expect(screen.queryByText('Private showroom')).not.toBeInTheDocument()
  })

  it('treats a failed session check as signed out', async () => {
    api.currentUser.mockRejectedValue(new Error('offline'))

    renderApp('/')

    expect(await screen.findByText('Signed out')).toBeInTheDocument()
  })

  it('signs in and out', async () => {
    api.currentUser.mockResolvedValue(null)
    api.login.mockResolvedValue(aCustomer())
    api.logout.mockResolvedValue()
    renderApp('/login')

    await userEvent.click(await screen.findByRole('button', { name: 'login' }))
    expect(await screen.findByText('Signed in as Asha Kumar')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'logout' }))
    expect(await screen.findByText('Signed out')).toBeInTheDocument()
  })

  it('signs the user out when the API reports the session expired', async () => {
    api.currentUser.mockResolvedValue(aCustomer())
    renderApp('/login')
    expect(await screen.findByText('Signed in as Asha Kumar')).toBeInTheDocument()

    act(() => {
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    })

    expect(await screen.findByText('Signed out')).toBeInTheDocument()
  })

  it('useAuth outside the provider is a programming error', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<WhoAmI />)).toThrow('useAuth must be used inside <AuthProvider>')
  })
})
