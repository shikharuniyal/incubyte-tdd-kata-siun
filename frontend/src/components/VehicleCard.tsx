import { useId } from 'react'
import { formatPrice, stockStatus, type Tone } from '../lib/format'
import type { Vehicle } from '../types'
import { Button, IconButton } from './ui/Button'
import { BoxIcon, CarIcon, EditIcon, TrashIcon } from './ui/icons'

export interface VehicleCardProps {
  vehicle: Vehicle
  canManage: boolean
  canAdminister: boolean
  purchasing?: boolean
  onPurchase: (vehicle: Vehicle) => void
  onEdit?: (vehicle: Vehicle) => void
  onRestock?: (vehicle: Vehicle) => void
  onDelete?: (vehicle: Vehicle) => void
}

const STOCK_TONES: Record<Tone, string> = {
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  warning: 'bg-amber-50 text-amber-800 ring-amber-600/25',
  danger: 'bg-rose-50 text-rose-700 ring-rose-600/20',
}

const STOCK_DOTS: Record<Tone, string> = {
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  danger: 'bg-rose-500',
}

// Full class strings so Tailwind can see them at build time.
const ARTWORK = [
  'from-sky-500 via-brand-600 to-indigo-800',
  'from-emerald-400 via-teal-600 to-cyan-800',
  'from-amber-400 via-orange-500 to-rose-700',
  'from-fuchsia-500 via-purple-600 to-indigo-900',
  'from-slate-500 via-slate-700 to-ink',
  'from-rose-400 via-pink-600 to-purple-800',
]

function artworkFor(category: string): string {
  const hash = [...category.toLowerCase()].reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return ARTWORK[hash % ARTWORK.length]
}

const CONDITION_LABELS = { NEW: 'New', USED: 'Pre-owned', REFURBISHED: 'Refurbished' } as const

export function VehicleCard({
  vehicle,
  canManage,
  canAdminister,
  purchasing = false,
  onPurchase,
  onEdit,
  onRestock,
  onDelete,
}: VehicleCardProps) {
  const headingId = useId()
  const title = `${vehicle.make} ${vehicle.model}`
  const stock = stockStatus(vehicle.quantity)
  const soldOut = vehicle.quantity <= 0

  return (
    <article
      aria-labelledby={headingId}
      className="group flex flex-col overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200/80 transition hover:-translate-y-0.5 hover:shadow-xl hover:shadow-slate-300/40"
    >
      <div className={`relative h-36 bg-gradient-to-br ${artworkFor(vehicle.category)} ${soldOut ? 'grayscale-[60%]' : ''}`}>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_10%,rgba(255,255,255,0.25),transparent_55%)]" />
        <CarIcon className="absolute -bottom-6 -right-4 size-40 text-white/15" strokeWidth={1.2} />
        <div className="relative flex items-start justify-between p-4">
          <span className="rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold text-white ring-1 ring-white/25 backdrop-blur">
            {CONDITION_LABELS[vehicle.condition]}
          </span>
          <span className="text-xs font-semibold text-white/80">{vehicle.model_year}</span>
        </div>
        <p className="absolute bottom-3 left-4 text-xs font-medium uppercase tracking-[0.18em] text-white/80">
          {vehicle.make}
        </p>
      </div>

      <div className="flex flex-1 flex-col gap-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 id={headingId} className="truncate text-lg font-bold tracking-tight text-slate-900" title={title}>
              {title}
            </h3>
            <p className="mt-0.5 truncate text-sm text-slate-500">
              {vehicle.variant !== 'BASE' ? `${vehicle.variant} · ` : ''}
              {vehicle.dealership_name}
            </p>
          </div>
          <span className="shrink-0 rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
            {vehicle.category}
          </span>
        </div>

        <div className="flex items-end justify-between gap-3">
          <p className="text-2xl font-extrabold tracking-tight text-slate-900">
            {formatPrice(vehicle.price, vehicle.currency_code)}
          </p>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${STOCK_TONES[stock.tone]}`}>
            <span className={`size-1.5 rounded-full ${STOCK_DOTS[stock.tone]}`} aria-hidden="true" />
            {stock.label}
          </span>
        </div>

        <div className="mt-auto flex items-center gap-2 pt-1">
          <Button
            className="flex-1"
            disabled={soldOut || purchasing}
            onClick={() => onPurchase(vehicle)}
          >
            {purchasing ? 'Purchasing…' : 'Purchase'}
          </Button>
          {canManage && (
            <IconButton label={`Edit ${title}`} onClick={() => onEdit?.(vehicle)}>
              <EditIcon />
            </IconButton>
          )}
          {canAdminister && (
            <>
              <IconButton label={`Restock ${title}`} onClick={() => onRestock?.(vehicle)}>
                <BoxIcon />
              </IconButton>
              <IconButton label={`Delete ${title}`} tone="danger" onClick={() => onDelete?.(vehicle)}>
                <TrashIcon />
              </IconButton>
            </>
          )}
        </div>
      </div>
    </article>
  )
}
