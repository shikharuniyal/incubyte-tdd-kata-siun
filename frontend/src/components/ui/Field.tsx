import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

const CONTROL =
  'block w-full rounded-xl border-0 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-brand-500 disabled:bg-slate-100 disabled:text-slate-500 aria-[invalid=true]:ring-rose-400 aria-[invalid=true]:focus:ring-rose-500'

interface FieldShellProps {
  id: string
  label: string
  error?: string
  hint?: string
  children: ReactNode
}

function FieldShell({ id, label, error, hint, children }: FieldShellProps) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-sm text-rose-600">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="text-xs text-slate-500">
            {hint}
          </p>
        )
      )}
    </div>
  )
}

function describedBy(id: string, error?: string, hint?: string) {
  if (error) return `${id}-error`
  return hint ? `${id}-hint` : undefined
}

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string }

export function TextField({ label, error, hint, id, className = '', ...props }: TextFieldProps) {
  const generated = useId()
  const inputId = id ?? generated
  return (
    <FieldShell id={inputId} label={label} error={error} hint={hint}>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(inputId, error, hint)}
        className={`${CONTROL} ${className}`}
        {...props}
      />
    </FieldShell>
  )
}

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & { label: string; error?: string; hint?: string }

export function SelectField({ label, error, hint, id, children, className = '', ...props }: SelectFieldProps) {
  const generated = useId()
  const selectId = id ?? generated
  return (
    <FieldShell id={selectId} label={label} error={error} hint={hint}>
      <select
        id={selectId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(selectId, error, hint)}
        className={`${CONTROL} pr-9 ${className}`}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  )
}

type TextAreaFieldProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; error?: string; hint?: string }

export function TextAreaField({ label, error, hint, id, className = '', ...props }: TextAreaFieldProps) {
  const generated = useId()
  const areaId = id ?? generated
  return (
    <FieldShell id={areaId} label={label} error={error} hint={hint}>
      <textarea
        id={areaId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(areaId, error, hint)}
        className={`${CONTROL} font-mono ${className}`}
        {...props}
      />
    </FieldShell>
  )
}
