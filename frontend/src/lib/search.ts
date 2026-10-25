import type { VehicleFilterValues } from '../types'

export const EMPTY_FILTERS: VehicleFilterValues = { make: '', model: '', category: '', minPrice: '', maxPrice: '' }

/** Form field → query parameter expected by GET /api/vehicles/search. */
const PARAM_NAMES: Record<keyof VehicleFilterValues, string> = {
  make: 'make',
  model: 'model',
  category: 'category',
  minPrice: 'min_price',
  maxPrice: 'max_price',
}

export function toSearchParams(filters: VehicleFilterValues): URLSearchParams {
  const params = new URLSearchParams()
  for (const key of Object.keys(PARAM_NAMES) as (keyof VehicleFilterValues)[]) {
    const value = filters[key].trim()
    if (value) params.set(PARAM_NAMES[key], value)
  }
  return params
}

export function hasActiveFilters(filters: VehicleFilterValues): boolean {
  return Object.values(filters).some((value) => value.trim() !== '')
}
