import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

const VARIANTS: Record<Variant, string> = {
  primary:
    'bg-brand-600 text-white shadow-sm shadow-brand-600/30 hover:bg-brand-700 focus-visible:outline-brand-600 disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none',
  secondary:
    'bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 focus-visible:outline-brand-600 disabled:text-slate-400',
  danger:
    'bg-rose-600 text-white shadow-sm shadow-rose-600/30 hover:bg-rose-700 focus-visible:outline-rose-600 disabled:bg-rose-300',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-brand-600 disabled:text-slate-300',
}

const SIZES: Record<Size, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-5 text-base gap-2',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: ReactNode
}

export function Button({ variant = 'primary', size = 'md', icon, className = '', children, type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center rounded-xl font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </button>
  )
}

/** A square icon-only button; `label` is its accessible name. */
export function IconButton({
  label,
  children,
  tone = 'neutral',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; tone?: 'neutral' | 'danger' }) {
  const colors =
    tone === 'danger'
      ? 'text-slate-500 hover:bg-rose-50 hover:text-rose-600'
      : 'text-slate-500 hover:bg-brand-50 hover:text-brand-700'
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`grid size-9 place-items-center rounded-lg transition focus-visible:outline-2 focus-visible:outline-brand-600 ${colors}`}
      {...props}
    >
      {children}
    </button>
  )
}
