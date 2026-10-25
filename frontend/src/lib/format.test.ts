import { describe, expect, it } from 'vitest'
import { formatPrice, stockStatus } from './format'

describe('formatPrice', () => {
  it('formats rupees with Indian digit grouping and no needless decimals', () => {
    expect(formatPrice(1850000, 'INR')).toBe('₹18,50,000')
  })

  it('keeps paise when the amount has them', () => {
    expect(formatPrice(999.5, 'INR')).toBe('₹999.50')
  })
})

describe('stockStatus', () => {
  it('is sold out at zero', () => {
    expect(stockStatus(0)).toEqual({ label: 'Sold out', tone: 'danger' })
  })

  it('warns when only one or two are left', () => {
    expect(stockStatus(1)).toEqual({ label: 'Only 1 left', tone: 'warning' })
    expect(stockStatus(2)).toEqual({ label: 'Only 2 left', tone: 'warning' })
  })

  it('shows the count when well stocked', () => {
    expect(stockStatus(8)).toEqual({ label: '8 in stock', tone: 'success' })
  })
})
