import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { AlertIcon, CheckIcon, CloseIcon } from './icons'
import { ToastContext, type ToastApi } from './toast-context'

type ToastTone = 'success' | 'error'

interface Toast {
  id: number
  tone: ToastTone
  message: string
}

const DISMISS_AFTER_MS = 5000

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: number) => setToasts((current) => current.filter((t) => t.id !== id)), [])

  const show = useCallback(
    (tone: ToastTone, message: string) => {
      const id = Date.now() + Math.random()
      setToasts((current) => [...current.slice(-3), { id, tone, message }])
      window.setTimeout(() => dismiss(id), DISMISS_AFTER_MS)
    },
    [dismiss],
  )

  const api = useMemo<ToastApi>(
    () => ({ success: (m) => show('success', m), error: (m) => show('error', m) }),
    [show],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4 sm:bottom-6 sm:items-end sm:px-6">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.tone === 'error' ? 'alert' : 'status'}
            className={`pointer-events-auto flex w-full max-w-sm animate-toast-in items-start gap-3 rounded-2xl px-4 py-3 text-sm font-medium shadow-xl ring-1 ${
              toast.tone === 'success'
                ? 'bg-emerald-950 text-emerald-50 ring-emerald-800'
                : 'bg-rose-950 text-rose-50 ring-rose-800'
            }`}
          >
            <span className={`mt-0.5 ${toast.tone === 'success' ? 'text-emerald-300' : 'text-rose-300'}`}>
              {toast.tone === 'success' ? <CheckIcon /> : <AlertIcon />}
            </span>
            <p className="flex-1 leading-relaxed">{toast.message}</p>
            <button type="button" onClick={() => dismiss(toast.id)} aria-label="Dismiss" className="opacity-60 hover:opacity-100">
              <CloseIcon className="size-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
