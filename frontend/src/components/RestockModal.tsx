import { useState, type FormEvent } from 'react'
import { ApiError, errorMessage } from '../api/client'
import type { RestockInput, Vehicle } from '../types'
import { Button } from './ui/Button'
import { TextAreaField, TextField } from './ui/Field'
import { Modal } from './ui/Modal'

interface RestockModalProps {
  vehicle: Vehicle
  onClose: () => void
  onSubmit: (input: RestockInput) => Promise<void>
}

function parseVins(text: string): string[] {
  return text
    .split(/[\s,]+/)
    .map((vin) => vin.trim().toUpperCase())
    .filter(Boolean)
}

export function RestockModal({ vehicle, onClose, onSubmit }: RestockModalProps) {
  const [quantity, setQuantity] = useState('1')
  const [vinText, setVinText] = useState('')
  const [unitCost, setUnitCost] = useState('')
  const [errors, setErrors] = useState<Record<string, string[]>>({})
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const vins = parseVins(vinText)
  const count = vins.length || Number(quantity) || 0

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    setFormError('')
    const input: RestockInput = { quantity: count }
    if (vins.length) input.vins = vins
    if (unitCost !== '') input.unit_cost = Number(unitCost)
    try {
      await onSubmit(input)
    } catch (error) {
      if (error instanceof ApiError && Object.keys(error.fieldErrors).length) setErrors(error.fieldErrors)
      else setFormError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={`Restock ${vehicle.make} ${vehicle.model}`}
      description={`Currently ${vehicle.quantity} in stock. Each car added is a physical vehicle with its own VIN.`}
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {formError && (
          <p role="alert" className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700 ring-1 ring-rose-200">
            {formError}
          </p>
        )}
        <TextField
          label="Cars to add"
          type="number"
          inputMode="numeric"
          min={1}
          max={500}
          value={vins.length ? String(vins.length) : quantity}
          disabled={vins.length > 0}
          onChange={(e) => setQuantity(e.target.value)}
          error={errors.quantity?.[0]}
          hint={vins.length ? 'Counted from the VINs below.' : undefined}
        />
        <TextAreaField
          label="VINs (optional, one per line)"
          rows={3}
          value={vinText}
          onChange={(e) => setVinText(e.target.value)}
          error={errors.vins?.[0]}
          placeholder="MA3FB32S0R0123456"
          hint="Leave empty to record VINs later; each car gets a temporary ID."
        />
        <TextField
          label="Cost per car (₹, optional)"
          type="number"
          inputMode="decimal"
          min={0}
          value={unitCost}
          onChange={(e) => setUnitCost(e.target.value)}
          error={errors.unit_cost?.[0]}
        />
        <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving || count < 1}>
            {saving ? 'Restocking…' : 'Restock'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
