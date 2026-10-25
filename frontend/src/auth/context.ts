import { createContext, useContext } from 'react'
import type { RegisterInput, User } from '../types'

export interface AuthContextValue {
  user: User | null
  /** False until the stored session (if any) has been checked. */
  ready: boolean
  login(email: string, password: string): Promise<User>
  register(input: RegisterInput): Promise<User>
  logout(): Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
