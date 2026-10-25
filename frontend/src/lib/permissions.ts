import type { Role, User, Vehicle } from '../types'

const STAFF_ROLES: Role[] = ['ADMIN', 'MANAGER', 'STAFF']

function hasRoleAt(user: User | null, dealershipId: string, roles: Role[]): boolean {
  return !!user?.roles.some((r) => r.dealership_id === dealershipId && roles.includes(r.role))
}

/** Add and edit vehicles: any staff role at the vehicle's dealership. */
export function canManage(user: User | null, vehicle: Vehicle): boolean {
  return hasRoleAt(user, vehicle.dealership_id, STAFF_ROLES)
}

/** Restock and delete: admins of the vehicle's dealership only. */
export function canAdminister(user: User | null, vehicle: Vehicle): boolean {
  return hasRoleAt(user, vehicle.dealership_id, ['ADMIN'])
}

export function canAddVehicles(user: User | null): boolean {
  return !!user?.roles.some((r) => STAFF_ROLES.includes(r.role))
}

/** Dealerships where the user may add vehicles. */
export function staffDealerships(user: User | null) {
  const seen = new Map<string, string>()
  for (const r of user?.roles ?? []) {
    if (STAFF_ROLES.includes(r.role)) seen.set(r.dealership_id, r.dealership_name)
  }
  return [...seen].map(([id, name]) => ({ id, name }))
}
