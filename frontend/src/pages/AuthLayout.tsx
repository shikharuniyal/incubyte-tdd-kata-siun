import type { ReactNode } from 'react'
import { Logo } from '../components/Logo'
import { CarIcon, CheckIcon } from '../components/ui/icons'

const HIGHLIGHTS = [
  'Live stock for every model, counted car by car',
  'Search by make, model, category and budget',
  'Safe purchasing: the last car can only be sold once',
]

/** Split screen used by the sign-in and registration pages. */
export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-ink lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(55,102,249,0.45),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(168,85,247,0.3),transparent_50%)]" />
        <CarIcon className="absolute -bottom-24 -right-20 size-[34rem] text-white/[0.04]" strokeWidth={0.8} />
        <div className="relative">
          <Logo />
        </div>
        <div className="relative max-w-md">
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight text-white">
            Every car on your lot, <span className="bg-gradient-to-r from-brand-300 to-fuchsia-300 bg-clip-text text-transparent">accounted for.</span>
          </h2>
          <ul className="mt-8 space-y-4">
            {HIGHLIGHTS.map((item) => (
              <li key={item} className="flex items-start gap-3 text-white/80">
                <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-brand-500/20 text-brand-300">
                  <CheckIcon className="size-4" />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-white/40">Car Dealership Inventory System · TDD Kata</p>
      </aside>

      <main className="flex items-center justify-center px-4 py-12 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden">
            <Logo tone="dark" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">{title}</h1>
          <p className="mt-2 text-slate-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </main>
    </div>
  )
}
