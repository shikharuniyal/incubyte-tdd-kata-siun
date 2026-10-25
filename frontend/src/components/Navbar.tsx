import { useAuth } from '../auth/context'
import { Logo } from './Logo'
import { LogoutIcon } from './ui/icons'

function roleLabel(isAdmin: boolean, isStaff: boolean) {
  if (isAdmin) return { text: 'Admin', classes: 'bg-amber-400/15 text-amber-200 ring-amber-300/30' }
  if (isStaff) return { text: 'Staff', classes: 'bg-sky-400/15 text-sky-200 ring-sky-300/30' }
  return { text: 'Customer', classes: 'bg-white/10 text-white/80 ring-white/20' }
}

export function Navbar() {
  const { user, logout } = useAuth()
  if (!user) return null
  const role = roleLabel(user.is_admin, user.is_staff)
  const initials = user.name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-ink/90 backdrop-blur supports-[backdrop-filter]:bg-ink/75">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Logo />
        <div className="flex items-center gap-3">
          <span className={`hidden rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset sm:inline ${role.classes}`}>
            {role.text}
          </span>
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold text-white">{user.name}</p>
            <p className="text-xs text-white/50">{user.email}</p>
          </div>
          <span className="grid size-9 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-brand-700 text-sm font-bold text-white" aria-hidden="true">
            {initials}
          </span>
          <button
            type="button"
            onClick={() => void logout()}
            className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-white/70 transition hover:bg-white/10 hover:text-white"
          >
            <LogoutIcon className="size-4" />
            <span className="hidden sm:inline">Sign out</span>
          </button>
        </div>
      </div>
    </header>
  )
}
