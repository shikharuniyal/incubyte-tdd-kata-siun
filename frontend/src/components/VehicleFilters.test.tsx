import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { EMPTY_FILTERS } from '../lib/search'
import type { VehicleFilterValues } from '../types'
import { VehicleFilters } from './VehicleFilters'

function ControlledFilters({ onChange, initial = EMPTY_FILTERS }: { onChange: (f: VehicleFilterValues) => void; initial?: VehicleFilterValues }) {
  const [value, setValue] = useState(initial)
  return (
    <VehicleFilters
      value={value}
      categories={['Hatchback', 'Sedan', 'SUV']}
      onChange={(next) => {
        setValue(next)
        onChange(next)
      }}
    />
  )
}

describe('VehicleFilters', () => {
  it('reports what the user types into each filter', async () => {
    const onChange = vi.fn()
    render(<ControlledFilters onChange={onChange} />)

    await userEvent.type(screen.getByLabelText('Make'), 'Toy')
    await userEvent.type(screen.getByLabelText('Max price'), '900000')

    expect(onChange).toHaveBeenLastCalledWith({ ...EMPTY_FILTERS, make: 'Toy', maxPrice: '900000' })
  })

  it('offers the known categories', async () => {
    const onChange = vi.fn()
    render(<ControlledFilters onChange={onChange} />)

    await userEvent.selectOptions(screen.getByLabelText('Category'), 'SUV')

    expect(onChange).toHaveBeenLastCalledWith({ ...EMPTY_FILTERS, category: 'SUV' })
  })

  it('clears every filter at once', async () => {
    const onChange = vi.fn()
    render(<ControlledFilters onChange={onChange} initial={{ ...EMPTY_FILTERS, make: 'Kia', minPrice: '5' }} />)

    await userEvent.click(screen.getByRole('button', { name: /clear filters/i }))

    expect(onChange).toHaveBeenLastCalledWith(EMPTY_FILTERS)
  })

  it('does not offer to clear when nothing is filtered', () => {
    render(<ControlledFilters onChange={vi.fn()} />)

    expect(screen.queryByRole('button', { name: /clear filters/i })).not.toBeInTheDocument()
  })
})
