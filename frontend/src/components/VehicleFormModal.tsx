import { useState, type FormEvent } from 'react'
import { ApiError, errorMessage } from '../api/client'
import type { Condition, Vehicle, VehicleInput } from '../types'
import { Button } from './ui/Button'
import { SelectField, TextField } from './ui/Field'
import { Modal } from './ui/Modal'

interface VehicleFormModalProps {
  open: boolean
  /** When given, the form edits this vehicle; otherwise it adds a new one. */
  vehicle?: Vehicle | null
  dealerships: { id: string; name: string }[]
  categories: string[]
  onClose: () => void
  onSubmit: (input: VehicleInput) => Promise<void>
}

interface FormState {
  make: string
  model: string
  category: string
  price: string
  quantity: string
  model_year: string
  variant: string
  condition: Condition
  dealership_id: string
}

function initialState(vehicle: Vehicle | null | undefined, dealerships: { id: string }[]): FormState {
  return {
    make: vehicle?.make ?? '',
    model: vehicle?.model ?? '',
    category: vehicle?.category ?? '',
    price: vehicle ? String(vehicle.price) : '',
    quantity: '',
    model_year: String(vehicle?.model_year ?? new Date().getFullYear()),
    variant: vehicle?.variant ?? 'BASE',
    condition: vehicle?.condition ?? 'NEW',
    dealership_id: vehicle?.dealership_id ?? dealerships[0]?.id ?? '',
  }
}

export function VehicleFormModal({ open, vehicle, dealerships, categories, onClose, onSubmit }: VehicleFormModalProps) {
  const editing = !!vehicle
  const [form, setForm] = useState<FormState>(() => initialState(vehicle, dealerships))
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (field: keyof FormState) => (event: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [field]: event.target.value }))

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    setFormError('')
    const input: VehicleInput = {
      make: form.make.trim(),
      model: form.model.trim(),
      category: form.category.trim(),
      price: Number(form.price),
      model_year: Number(form.model_year),
      variant: form.variant.trim() || 'BASE',
      condition: form.condition,
    }
    if (!editing) {
      input.quantity = form.quantity === '' ? 0 : Number(form.quantity)
      if (dealerships.length > 1) input.dealership_id = form.dealership_id
    }
    try {
      await onSubmit(input)
    } catch (error) {
      if (error instanceof ApiError && Object.keys(error.fieldErrors).length) setErrors(error.fieldErrors)
      else setFormError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const fieldError = (name: string) => errors[name]?.[0]

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title={editing ? `Edit ${vehicle.make} ${vehicle.model}` : 'Add a vehicle'}
      description={
        editing
          ? 'Update the listing. Stock changes through purchases and restocking.'
          : 'List a model and how many cars of it are in stock.'
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {formError && (
          <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700 ring-1 ring-rose-200">
            {formError}
          </p>
        )}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Make" required value={form.make} onChange={set('make')} error={fieldError('make')} placeholder="Toyota" />
          <TextField label="Model" required value={form.model} onChange={set('model')} error={fieldError('model')} placeholder="Corolla Altis" />
          <TextField
            label="Category"
            required
            list="vehicle-categories"
            value={form.category}
            onChange={set('category')}
            error={fieldError('category')}
            placeholder="Sedan, SUV, Hatchback…"
          />
          <datalist id="vehicle-categories">
            {categories.map((category) => (
              <option key={category} value={category} />
            ))}
          </datalist>
          <TextField
            label="Price (₹)"
            type="number"
            inputMode="decimal"
            min={0}
            required
            value={form.price}
            onChange={set('price')}
            error={fieldError('price')}
            placeholder="1850000"
          />
          <TextField
            label="Model year"
            type="number"
            min={1900}
            max={2200}
            value={form.model_year}
            onChange={set('model_year')}
            error={fieldError('model_year')}
          />
          <TextField label="Variant" value={form.variant} onChange={set('variant')} error={fieldError('variant')} />
          <SelectField label="Condition" value={form.condition} onChange={set('condition')} error={fieldError('condition')}>
            <option value="NEW">New</option>
            <option value="USED">Pre-owned</option>
            <option value="REFURBISHED">Refurbished</option>
          </SelectField>
          {!editing && (
            <TextField
              label="Quantity in stock"
              type="number"
              inputMode="numeric"
              min={0}
              value={form.quantity}
              onChange={set('quantity')}
              error={fieldError('quantity')}
              placeholder="0"
              hint="One car per unit; VINs can be recorded when restocking."
            />
          )}
          {!editing && dealerships.length > 1 && (
            <SelectField label="Dealership" value={form.dealership_id} onChange={set('dealership_id')} error={fieldError('dealership_id')}>
              {dealerships.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </SelectField>
          )}
        </div>
        <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? 'Saving…' : editing ? 'Save changes' : 'Add vehicle'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
