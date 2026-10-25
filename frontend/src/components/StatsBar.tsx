import { formatCompactPrice } from '../lib/format'
import type { Vehicle } from '../types'

export function StatsBar({ vehicles }: { vehicles: Vehicle[] }) {
  const carsInStock = vehicles.reduce((sum, v) => sum + v.quantity, 0)
  const soldOut = vehicles.filter((v) => v.quantity === 0).length
  const stockValue = vehicles.reduce((sum, v) => sum + v.quantity * v.price, 0)

  const stats = [
    { label: 'Models listed', value: String(vehicles.length) },
    { label: 'Cars in stock', value: String(carsInStock) },
    { label: 'Sold out', value: String(soldOut) },
    { label: 'Stock value', value: formatCompactPrice(stockValue) },
  ]

  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.label} className="rounded-2xl bg-white/5 px-4 py-3 ring-1 ring-white/10 backdrop-blur">
          <dt className="text-xs font-medium uppercase tracking-wider text-white/50">{stat.label}</dt>
          <dd className="mt-1 text-2xl font-bold tracking-tight text-white">{stat.value}</dd>
        </div>
      ))}
    </dl>
  )
}
