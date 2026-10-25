import { describe, expect, it } from 'vitest'
import { EMPTY_FILTERS, hasActiveFilters, toSearchParams } from './search'

describe('toSearchParams', () => {
  it('sends only the filters that are set, trimmed, using the API names', () => {
    const params = toSearchParams({ make: ' toyota ', model: '', category: 'SUV', minPrice: '100000', maxPrice: '' })

    expect(params.toString()).toBe('make=toyota&category=SUV&min_price=100000')
  })

  it('is empty when nothing is set', () => {
    expect(toSearchParams(EMPTY_FILTERS).toString()).toBe('')
  })
})

describe('hasActiveFilters', () => {
  it('is false for empty or whitespace-only filters', () => {
    expect(hasActiveFilters(EMPTY_FILTERS)).toBe(false)
    expect(hasActiveFilters({ ...EMPTY_FILTERS, make: '   ' })).toBe(false)
  })

  it('is true when any filter is set', () => {
    expect(hasActiveFilters({ ...EMPTY_FILTERS, maxPrice: '500000' })).toBe(true)
  })
})
