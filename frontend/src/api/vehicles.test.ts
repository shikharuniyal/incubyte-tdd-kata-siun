import { beforeEach, describe, expect, it, vi } from 'vitest'
import { EMPTY_FILTERS } from '../lib/search'
import { http } from './http'
import * as vehicles from './vehicles'

vi.mock('./http', () => ({ http: { request: vi.fn().mockResolvedValue(undefined) } }))
const request = vi.mocked(http.request)

beforeEach(() => request.mockClear())

describe('vehicles api', () => {
  it('lists vehicles', async () => {
    await vehicles.listVehicles()
    expect(request).toHaveBeenCalledWith('/api/vehicles')
  })

  it('searches with the API parameter names', async () => {
    await vehicles.searchVehicles({ ...EMPTY_FILTERS, make: 'Kia', maxPrice: '900000' })
    expect(request).toHaveBeenCalledWith('/api/vehicles/search?make=Kia&max_price=900000')
  })

  it('creates, updates and deletes', async () => {
    const input = { make: 'Kia', model: 'Seltos', category: 'SUV', price: 1 }
    await vehicles.createVehicle(input)
    await vehicles.updateVehicle('v1', { price: 2 })
    await vehicles.deleteVehicle('v1')

    expect(request).toHaveBeenNthCalledWith(1, '/api/vehicles', { method: 'POST', body: input })
    expect(request).toHaveBeenNthCalledWith(2, '/api/vehicles/v1', { method: 'PUT', body: { price: 2 } })
    expect(request).toHaveBeenNthCalledWith(3, '/api/vehicles/v1', { method: 'DELETE' })
  })

  it('sends a fresh idempotency key with every purchase and restock', async () => {
    await vehicles.purchaseVehicle('v1')
    await vehicles.purchaseVehicle('v1')
    await vehicles.restockVehicle('v1', { quantity: 2 })

    const keys = request.mock.calls.map(([, options]) => options?.headers?.['Idempotency-Key'])
    expect(request.mock.calls[0][0]).toBe('/api/vehicles/v1/purchase')
    expect(request.mock.calls[2][0]).toBe('/api/vehicles/v1/restock')
    expect(request.mock.calls[2][1]?.body).toEqual({ quantity: 2 })
    expect(new Set(keys).size).toBe(3)
    expect(keys.every(Boolean)).toBe(true)
  })
})
