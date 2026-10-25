export function Spinner({ label, className = 'size-6' }: { label?: string; className?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-3 text-slate-500">
      <svg className={`${className} animate-spin`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.2" strokeWidth="3" />
        <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {label && <span className="text-sm font-medium">{label}</span>}
    </span>
  )
}
