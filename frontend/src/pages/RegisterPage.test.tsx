import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { aCustomer } from '../test/fixtures'
import { fakeAuth, renderWithProviders } from '../test/render'
import { RegisterPage } from './RegisterPage'

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText('First name'), 'Asha')
  await userEvent.type(screen.getByLabelText('Last name'), 'Kumar')
  await userEvent.type(screen.getByLabelText('Email'), 'asha@example.com')
  await userEvent.type(screen.getByLabelText('Password'), 'Str0ng-Passw0rd!')
  await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
}

describe('RegisterPage', () => {
  it('creates the account and opens the showroom', async () => {
    const register = vi.fn().mockResolvedValue(aCustomer())
    renderWithProviders(<RegisterPage />, { auth: fakeAuth(null, { register }), route: '/register', path: '/register' })

    await fillAndSubmit()

    expect(register).toHaveBeenCalledWith({
      first_name: 'Asha',
      last_name: 'Kumar',
      email: 'asha@example.com',
      password: 'Str0ng-Passw0rd!',
    })
    expect(await screen.findByText('Showroom home')).toBeInTheDocument()
  })

  it('shows field errors next to the right field', async () => {
    const register = vi.fn().mockRejectedValue(
      new ApiError(400, 'This password is too common.', { password: ['This password is too common.'] }),
    )
    renderWithProviders(<RegisterPage />, { auth: fakeAuth(null, { register }), route: '/register', path: '/register' })

    await fillAndSubmit()

    expect(await screen.findByText('This password is too common.')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toHaveAttribute('aria-invalid', 'true')
  })
})
