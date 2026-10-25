export type Role = 'ADMIN' | 'MANAGER' | 'STAFF'

export interface RoleAssignment {
  dealership_id: string
  dealership_name: string
  role: Role
}

export interface User {
  id: string
  email: string
  name: string
  roles: RoleAssignment[]
  is_admin: boolean
  is_staff: boolean
}

export type Condition = 'NEW' | 'USED' | 'REFURBISHED'

/** A vehicle as the API returns it: a dealership listing with its derived stock quantity. */
export interface Vehicle {
  id: string
  make: string
  model: string
  category: string
  price: number
  quantity: number
  condition: Condition
  currency_code: string
  model_year: number
  variant: string
  dealership_id: string
  dealership_name: string
}

/** Search form values, kept as strings exactly as typed. */
export interface VehicleFilterValues {
  make: string
  model: string
  category: string
  minPrice: string
  maxPrice: string
}

export interface VehicleInput {
  make: string
  model: string
  category: string
  price: number
  quantity?: number
  model_year?: number
  variant?: string
  condition?: Condition
  dealership_id?: string
}

export interface RestockInput {
  quantity: number
  vins?: string[]
  unit_cost?: number
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
}
