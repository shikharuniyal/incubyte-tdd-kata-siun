import { describe, expect, it } from 'vitest'
import { aCustomer, anAdmin, aStaffMember, aVehicle } from '../test/fixtures'
import { canAddVehicles, canAdminister, canManage } from './permissions'

const vehicle = aVehicle()
const elsewhere = aVehicle({ dealership_id: 'another-dealership' })

describe('canManage (add/edit)', () => {
  it('allows staff and admins of the vehicle’s dealership', () => {
    expect(canManage(aStaffMember(), vehicle)).toBe(true)
    expect(canManage(anAdmin(), vehicle)).toBe(true)
  })

  it('denies customers, anonymous users and staff of other dealerships', () => {
    expect(canManage(aCustomer(), vehicle)).toBe(false)
    expect(canManage(null, vehicle)).toBe(false)
    expect(canManage(aStaffMember(), elsewhere)).toBe(false)
  })
})

describe('canAdminister (restock/delete)', () => {
  it('allows only admins of the vehicle’s dealership', () => {
    expect(canAdminister(anAdmin(), vehicle)).toBe(true)
    expect(canAdminister(aStaffMember(), vehicle)).toBe(false)
    expect(canAdminister(anAdmin(), elsewhere)).toBe(false)
  })
})

describe('canAddVehicles', () => {
  it('is true for anyone with a staff role', () => {
    expect(canAddVehicles(aStaffMember())).toBe(true)
    expect(canAddVehicles(aCustomer())).toBe(false)
    expect(canAddVehicles(null)).toBe(false)
  })
})
