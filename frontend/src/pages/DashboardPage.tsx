import { useCallback, useEffect, useMemo, useState } from 'react'
import { errorMessage } from '../api/client'
import * as vehiclesApi from '../api/vehicles'
import { useAuth } from '../auth/context'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { Navbar } from '../components/Navbar'
import { RestockModal } from '../components/RestockModal'
import { StatsBar } from '../components/StatsBar'
import { VehicleCard } from '../components/VehicleCard'
import { VehicleFilters } from '../components/VehicleFilters'
import { VehicleFormModal } from '../components/VehicleFormModal'
import { Button } from '../components/ui/Button'
import { CarIcon, PlusIcon } from '../components/ui/icons'
import { Spinner } from '../components/ui/Spinner'
import { useToast } from '../components/ui/toast-context'
import { canAddVehicles, canAdminister, canManage, staffDealerships } from '../lib/permissions'
import { EMPTY_FILTERS, hasActiveFilters } from '../lib/search'
import type { Vehicle, VehicleFilterValues } from '../types'

const SEARCH_DEBOUNCE_MS = 300

type Dialog =
  | { kind: 'add' }
  | { kind: 'edit'; vehicle: Vehicle }
  | { kind: 'restock'; vehicle: Vehicle }
  | { kind: 'delete'; vehicle: Vehicle }
  | null

function byName(a: Vehicle, b: Vehicle) {
  return `${a.make} ${a.model}`.localeCompare(`${b.make} ${b.model}`) || a.price - b.price
}

export function DashboardPage() {
  const { user } = useAuth()
  const toast = useToast()

  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [knownCategories, setKnownCategories] = useState<string[]>([])
  const [filters, setFilters] = useState<VehicleFilterValues>(EMPTY_FILTERS)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [purchasingId, setPurchasingId] = useState<string | null>(null)
  const [dialog, setDialog] = useState<Dialog>(null)
  const [reloadCount, setReloadCount] = useState(0)

  const filtering = hasActiveFilters(filters)

  // Load the catalogue (or search results), debouncing while the user types.
  useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(
      async () => {
        setLoading(true)
        setLoadError('')
        try {
          const result = filtering ? await vehiclesApi.searchVehicles(filters) : await vehiclesApi.listVehicles()
          if (cancelled) return
          setVehicles(result)
          setKnownCategories((current) => [...new Set([...current, ...result.map((v) => v.category)])].sort())
        } catch (error) {
          if (!cancelled) setLoadError(errorMessage(error))
        } finally {
          if (!cancelled) setLoading(false)
        }
      },
      filtering ? SEARCH_DEBOUNCE_MS : 0,
    )
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [filters, filtering, reloadCount])

  const replaceVehicle = useCallback((updated: Vehicle) => {
    setVehicles((current) => current.map((v) => (v.id === updated.id ? updated : v)))
  }, [])

  const closeDialog = useCallback(() => setDialog(null), [])

  async function purchase(vehicle: Vehicle) {
    setPurchasingId(vehicle.id)
    try {
      const { vehicle: updated, sale_id } = await vehiclesApi.purchaseVehicle(vehicle.id)
      replaceVehicle(updated)
      toast.success(`You bought a ${vehicle.make} ${vehicle.model}! Sale reference ${sale_id.slice(0, 8).toUpperCase()}.`)
    } catch (error) {
      toast.error(errorMessage(error))
    } finally {
      setPurchasingId(null)
    }
  }

  const dealerships = useMemo(() => staffDealerships(user), [user])

  return (
    <div className="min-h-screen">
      <Navbar />

      <section className="relative overflow-hidden bg-ink pb-24 pt-10 sm:pt-14">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(55,102,249,0.35),transparent_55%),radial-gradient(ellipse_at_bottom_left,rgba(168,85,247,0.22),transparent_50%)]" />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-brand-300">Hello, {user?.name.split(' ')[0]}</p>
              <h1 className="mt-1 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">The showroom</h1>
              <p className="mt-2 max-w-xl text-white/60">
                Every listing shows exactly how many cars are on the lot right now.
              </p>
            </div>
            {canAddVehicles(user) && (
              <Button size="lg" icon={<PlusIcon />} onClick={() => setDialog({ kind: 'add' })} className="shrink-0">
                Add vehicle
              </Button>
            )}
          </div>
          <div className="mt-8">
            <StatsBar vehicles={vehicles} />
          </div>
        </div>
      </section>

      <main className="relative mx-auto -mt-16 max-w-7xl space-y-8 px-4 pb-20 sm:px-6 lg:px-8">
        <VehicleFilters value={filters} categories={knownCategories} onChange={setFilters} />

        {loadError ? (
          <div role="alert" className="rounded-3xl bg-white p-10 text-center shadow-sm ring-1 ring-rose-200">
            <p className="font-semibold text-rose-700">{loadError}</p>
            <Button variant="secondary" className="mt-4" onClick={() => setReloadCount((n) => n + 1)}>
              Try again
            </Button>
          </div>
        ) : loading && vehicles.length === 0 ? (
          <div className="grid place-items-center py-24">
            <Spinner label="Loading vehicles" />
          </div>
        ) : vehicles.length === 0 ? (
          <div className="rounded-3xl border-2 border-dashed border-slate-200 bg-white/60 px-6 py-20 text-center">
            <CarIcon className="mx-auto size-12 text-slate-300" />
            <p className="mt-4 text-lg font-semibold text-slate-700">
              {filtering ? 'No vehicles match your filters.' : 'The showroom is empty.'}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              {filtering ? 'Try a wider price range or a different make.' : 'Staff can add the first vehicle.'}
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">
                {vehicles.length} {vehicles.length === 1 ? 'model' : 'models'}
                {filtering ? ' match your search' : ' in the showroom'}
              </p>
              {loading && <Spinner className="size-4" />}
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {vehicles.map((vehicle) => (
                <VehicleCard
                  key={vehicle.id}
                  vehicle={vehicle}
                  canManage={canManage(user, vehicle)}
                  canAdminister={canAdminister(user, vehicle)}
                  purchasing={purchasingId === vehicle.id}
                  onPurchase={purchase}
                  onEdit={(v) => setDialog({ kind: 'edit', vehicle: v })}
                  onRestock={(v) => setDialog({ kind: 'restock', vehicle: v })}
                  onDelete={(v) => setDialog({ kind: 'delete', vehicle: v })}
                />
              ))}
            </div>
          </>
        )}
      </main>

      {(dialog?.kind === 'add' || dialog?.kind === 'edit') && (
        <VehicleFormModal
          open
          key={dialog.kind === 'edit' ? dialog.vehicle.id : 'new'}
          vehicle={dialog.kind === 'edit' ? dialog.vehicle : null}
          dealerships={dealerships}
          categories={knownCategories}
          onClose={closeDialog}
          onSubmit={async (input) => {
            if (dialog.kind === 'edit') {
              const updated = await vehiclesApi.updateVehicle(dialog.vehicle.id, input)
              replaceVehicle(updated)
              toast.success(`${updated.make} ${updated.model} updated.`)
            } else {
              const created = await vehiclesApi.createVehicle(input)
              setVehicles((current) => [...current, created].sort(byName))
              setKnownCategories((current) => [...new Set([...current, created.category])].sort())
              toast.success(`${created.make} ${created.model} added with ${created.quantity} in stock.`)
            }
            closeDialog()
          }}
        />
      )}

      {dialog?.kind === 'restock' && (
        <RestockModal
          vehicle={dialog.vehicle}
          onClose={closeDialog}
          onSubmit={async (input) => {
            const { vehicle: updated, added } = await vehiclesApi.restockVehicle(dialog.vehicle.id, input)
            replaceVehicle(updated)
            toast.success(`Added ${added} × ${updated.make} ${updated.model}. Now ${updated.quantity} in stock.`)
            closeDialog()
          }}
        />
      )}

      {dialog?.kind === 'delete' && (
        <ConfirmDialog
          title={`Delete ${dialog.vehicle.make} ${dialog.vehicle.model}?`}
          message="The listing is removed from the showroom and its unsold cars are taken out of stock. Sales history is kept."
          confirmLabel="Delete"
          onClose={closeDialog}
          onConfirm={async () => {
            try {
              await vehiclesApi.deleteVehicle(dialog.vehicle.id)
              setVehicles((current) => current.filter((v) => v.id !== dialog.vehicle.id))
              toast.success(`${dialog.vehicle.make} ${dialog.vehicle.model} deleted.`)
              closeDialog()
            } catch (error) {
              toast.error(errorMessage(error))
            }
          }}
        />
      )}
    </div>
  )
}
