import type { User, Vehicle } from '../types'

export const DEALERSHIP_ID = '11111111-1111-1111-1111-111111111111'

export function aVehicle(overrides: Partial<Vehicle> = {}): Vehicle {
  return {
    id: 'aaaaaaaa-0000-0000-0000-000000000001',
    make: 'Toyota',
    model: 'Corolla',
    category: 'Sedan',
    price: 1850000,
    quantity: 3,
    condition: 'NEW',
    currency_code: 'INR',
    model_year: 2024,
    variant: 'BASE',
    dealership_id: DEALERSHIP_ID,
    dealership_name: 'Incubyte Motors',
    ...overrides,
  }
}

export function aCustomer(overrides: Partial<User> = {}): User {
  return {
    id: 'u-1',
    email: 'customer@example.com',
    name: 'Asha Kumar',
    roles: [],
    is_admin: false,
    is_staff: false,
    ...overrides,
  }
}

export function anAdmin(overrides: Partial<User> = {}): User {
  return aCustomer({
    email: 'admin@dealer.test',
    name: 'Dealer Admin',
    roles: [{ dealership_id: DEALERSHIP_ID, dealership_name: 'Incubyte Motors', role: 'ADMIN' }],
    is_admin: true,
    is_staff: true,
    ...overrides,
  })
}

export function aStaffMember(overrides: Partial<User> = {}): User {
  return aCustomer({
    email: 'staff@dealer.test',
    name: 'Sales Staff',
    roles: [{ dealership_id: DEALERSHIP_ID, dealership_name: 'Incubyte Motors', role: 'STAFF' }],
    is_staff: true,
    ...overrides,
  })
}
