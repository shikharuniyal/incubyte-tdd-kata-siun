import { CarIcon } from './ui/icons'

export function Logo({ tone = 'light' }: { tone?: 'light' | 'dark' }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 text-white shadow-lg shadow-brand-700/30">
        <CarIcon className="size-5" />
      </span>
      <span className={`text-base font-extrabold tracking-tight ${tone === 'light' ? 'text-white' : 'text-slate-900'}`}>
        Incubyte <span className="text-brand-400">Motors</span>
      </span>
    </span>
  )
}
