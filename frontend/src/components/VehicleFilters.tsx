import { EMPTY_FILTERS, hasActiveFilters } from '../lib/search'
import type { VehicleFilterValues } from '../types'
import { Button } from './ui/Button'
import { SelectField, TextField } from './ui/Field'
import { SearchIcon } from './ui/icons'

interface VehicleFiltersProps {
  value: VehicleFilterValues
  categories: string[]
  onChange: (next: VehicleFilterValues) => void
}

/** Controlled search form: make, model, category and a price range. */
export function VehicleFilters({ value, categories, onChange }: VehicleFiltersProps) {
  const set = (field: keyof VehicleFilterValues) => (event: { target: { value: string } }) =>
    onChange({ ...value, [field]: event.target.value })

  return (
    <section aria-label="Search vehicles" className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/80 sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <SearchIcon className="size-4 text-brand-600" />
          Find a vehicle
        </h2>
        {hasActiveFilters(value) && (
          <Button variant="ghost" size="sm" onClick={() => onChange(EMPTY_FILTERS)}>
            Clear filters
          </Button>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div className="col-span-2 sm:col-span-1">
          <TextField label="Make" placeholder="e.g. Toyota" value={value.make} onChange={set('make')} autoComplete="off" />
        </div>
        <div className="col-span-2 sm:col-span-1">
          <TextField label="Model" placeholder="e.g. Creta" value={value.model} onChange={set('model')} autoComplete="off" />
        </div>
        <div className="col-span-2 lg:col-span-1">
          <SelectField label="Category" value={value.category} onChange={set('category')}>
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </SelectField>
        </div>
        <TextField
          label="Min price"
          type="number"
          inputMode="numeric"
          min={0}
          placeholder="₹ any"
          value={value.minPrice}
          onChange={set('minPrice')}
        />
        <TextField
          label="Max price"
          type="number"
          inputMode="numeric"
          min={0}
          placeholder="₹ any"
          value={value.maxPrice}
          onChange={set('maxPrice')}
        />
      </div>
    </section>
  )
}
