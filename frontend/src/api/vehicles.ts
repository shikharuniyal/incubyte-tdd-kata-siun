import { toSearchParams } from '../lib/search'
import type { RestockInput, Vehicle, VehicleFilterValues, VehicleInput } from '../types'
import { http } from './http'

/** Each click gets its own key, so a network retry of that click cannot buy or restock twice. */
function idempotencyHeader(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() }
}

export function listVehicles(): Promise<Vehicle[]> {
  return http.request<Vehicle[]>('/api/vehicles')
}

export function searchVehicles(filters: VehicleFilterValues): Promise<Vehicle[]> {
  return http.request<Vehicle[]>(`/api/vehicles/search?${toSearchParams(filters)}`)
}

export function createVehicle(input: VehicleInput): Promise<Vehicle> {
  return http.request<Vehicle>('/api/vehicles', { method: 'POST', body: input })
}

export function updateVehicle(id: string, changes: Partial<VehicleInput>): Promise<Vehicle> {
  return http.request<Vehicle>(`/api/vehicles/${id}`, { method: 'PUT', body: changes })
}

export function deleteVehicle(id: string): Promise<void> {
  return http.request<void>(`/api/vehicles/${id}`, { method: 'DELETE' })
}

export function purchaseVehicle(id: string): Promise<{ vehicle: Vehicle; sale_id: string }> {
  return http.request(`/api/vehicles/${id}/purchase`, { method: 'POST', headers: idempotencyHeader() })
}

export function restockVehicle(id: string, input: RestockInput): Promise<{ vehicle: Vehicle; added: number }> {
  return http.request(`/api/vehicles/${id}/restock`, { method: 'POST', body: input, headers: idempotencyHeader() })
}
