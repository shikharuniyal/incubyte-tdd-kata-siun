import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { ApiError, errorMessage } from '../api/client'
import { useAuth } from '../auth/context'
import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/Field'
import type { RegisterInput } from '../types'
import { AuthLayout } from './AuthLayout'

const EMPTY: RegisterInput = { first_name: '', last_name: '', email: '', password: '' }

export function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<RegisterInput>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({})
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  const set = (field: keyof RegisterInput) => (event: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [field]: event.target.value }))

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setFieldErrors({})
    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fieldErrors).length) setFieldErrors(err.fieldErrors)
      else setError(errorMessage(err))
      setSubmitting(false)
    }
  }

  const fieldError = (name: keyof RegisterInput) => fieldErrors[name]?.join(' ')

  return (
    <AuthLayout title="Create your account" subtitle="Browse the showroom and buy your next car in a click.">
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {error && (
          <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-200">
            {error}
          </p>
        )}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="First name" autoComplete="given-name" required value={form.first_name} onChange={set('first_name')} error={fieldError('first_name')} />
          <TextField label="Last name" autoComplete="family-name" required value={form.last_name} onChange={set('last_name')} error={fieldError('last_name')} />
        </div>
        <TextField label="Email" type="email" autoComplete="email" required value={form.email} onChange={set('email')} error={fieldError('email')} />
        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          value={form.password}
          onChange={set('password')}
          error={fieldError('password')}
          hint="At least 8 characters; avoid common or all-numeric passwords."
        />
        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Already registered?{' '}
        <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-800">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
