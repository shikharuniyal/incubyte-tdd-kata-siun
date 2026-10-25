import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { aCustomer } from '../test/fixtures'
import { fakeAuth, renderWithProviders } from '../test/render'
import { LoginPage } from './LoginPage'

async function signIn(email = 'asha@example.com', password = 'Str0ng-Passw0rd!') {
  await userEvent.type(screen.getByLabelText('Email'), email)
  await userEvent.type(screen.getByLabelText('Password'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
}

describe('LoginPage', () => {
  it('signs in with the entered credentials and opens the showroom', async () => {
    const login = vi.fn().mockResolvedValue(aCustomer())
    renderWithProviders(<LoginPage />, { auth: fakeAuth(null, { login }), route: '/login', path: '/login' })

    await signIn()

    expect(login).toHaveBeenCalledWith('asha@example.com', 'Str0ng-Passw0rd!')
    expect(await screen.findByText('Showroom home')).toBeInTheDocument()
  })

  it('shows the server’s message when sign-in fails', async () => {
    const login = vi.fn().mockRejectedValue(new ApiError(401, 'Invalid email or password.'))
    renderWithProviders(<LoginPage />, { auth: fakeAuth(null, { login }), route: '/login', path: '/login' })

    await signIn('asha@example.com', 'wrong')

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
    expect(screen.queryByText('Showroom home')).not.toBeInTheDocument()
  })

  it('links to registration', () => {
    renderWithProviders(<LoginPage />, { route: '/login', path: '/login' })

    expect(screen.getByRole('link', { name: /create an account/i })).toHaveAttribute('href', '/register')
  })

  it('sends a signed-in user straight to the showroom', async () => {
    renderWithProviders(<LoginPage />, { auth: fakeAuth(aCustomer()), route: '/login', path: '/login' })

    expect(await screen.findByText('Showroom home')).toBeInTheDocument()
  })
})
