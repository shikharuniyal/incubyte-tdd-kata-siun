export type Tone = 'success' | 'warning' | 'danger'

export interface StockStatus {
  label: string
  tone: Tone
}

const LOW_STOCK_THRESHOLD = 2

/** ₹18,50,000 — Indian digit grouping, decimals only when the amount has paise. */
export function formatPrice(amount: number, currency = 'INR'): string {
  const fractionDigits = Number.isInteger(amount) ? 0 : 2
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(amount)
}

/** Compact form for dashboards, e.g. ₹1.2 Cr or ₹45.5 L. */
export function formatCompactPrice(amount: number): string {
  if (amount >= 1_00_00_000) return `₹${(amount / 1_00_00_000).toFixed(1)} Cr`
  if (amount >= 1_00_000) return `₹${(amount / 1_00_000).toFixed(1)} L`
  return formatPrice(amount)
}

export function stockStatus(quantity: number): StockStatus {
  if (quantity <= 0) return { label: 'Sold out', tone: 'danger' }
  if (quantity <= LOW_STOCK_THRESHOLD) return { label: `Only ${quantity} left`, tone: 'warning' }
  return { label: `${quantity} in stock`, tone: 'success' }
}
