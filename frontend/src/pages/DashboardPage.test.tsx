import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import * as vehiclesApi from '../api/vehicles'
import { aCustomer, anAdmin, aVehicle } from '../test/fixtures'
import { fakeAuth, renderWithProviders } from '../test/render'
import { DashboardPage } from './DashboardPage'

vi.mock('../api/vehicles')
const api = vi.mocked(vehiclesApi)

const corolla = aVehicle()
const creta = aVehicle({ id: 'creta', make: 'Hyundai', model: 'Creta', category: 'SUV', price: 1500000, quantity: 0 })

function renderDashboard(user = aCustomer()) {
  return renderWithProviders(<DashboardPage />, { auth: fakeAuth(user) })
}

function card(name: string) {
  return screen.getByRole('article', { name })
}

beforeEach(() => {
  vi.resetAllMocks()
  api.listVehicles.mockResolvedValue([corolla, creta])
  api.searchVehicles.mockResolvedValue([corolla])
})

describe('DashboardPage', () => {
  it('shows every available vehicle with its stock', async () => {
    renderDashboard()

    expect(await screen.findByRole('article', { name: 'Toyota Corolla' })).toBeInTheDocument()
    expect(within(card('Toyota Corolla')).getByText('3 in stock')).toBeInTheDocument()
    expect(within(card('Hyundai Creta')).getByRole('button', { name: /purchase/i })).toBeDisabled()
  })

  it('purchasing updates the quantity and confirms the sale', async () => {
    api.purchaseVehicle.mockResolvedValue({ vehicle: { ...corolla, quantity: 2 }, sale_id: 'sale-1' })
    renderDashboard()

    await userEvent.click(within(await screen.findByRole('article', { name: 'Toyota Corolla' })).getByRole('button', { name: /purchase/i }))

    expect(api.purchaseVehicle).toHaveBeenCalledWith(corolla.id)
    expect(await within(card('Toyota Corolla')).findByText('Only 2 left')).toBeInTheDocument()
    expect(await screen.findByText(/you bought a toyota corolla/i)).toBeInTheDocument()
  })

  it('explains why a purchase failed', async () => {
    api.purchaseVehicle.mockRejectedValue(new ApiError(409, 'Toyota Corolla is out of stock.'))
    renderDashboard()

    await userEvent.click(within(await screen.findByRole('article', { name: 'Toyota Corolla' })).getByRole('button', { name: /purchase/i }))

    expect(await screen.findByText('Toyota Corolla is out of stock.')).toBeInTheDocument()
  })

  it('searches the API when a filter is set', async () => {
    renderDashboard()
    await screen.findByRole('article', { name: 'Toyota Corolla' })

    await userEvent.type(screen.getByLabelText('Make'), 'toy')

    await waitFor(() => expect(api.searchVehicles).toHaveBeenLastCalledWith(expect.objectContaining({ make: 'toy' })))
    await waitFor(() => expect(screen.queryByRole('article', { name: 'Hyundai Creta' })).not.toBeInTheDocument())
  })

  it('shows a friendly message when nothing matches', async () => {
    api.searchVehicles.mockResolvedValue([])
    renderDashboard()
    await screen.findByRole('article', { name: 'Toyota Corolla' })

    await userEvent.type(screen.getByLabelText('Make'), 'Ferrari')

    expect(await screen.findByText(/no vehicles match/i)).toBeInTheDocument()
  })

  it('only shows "Add vehicle" to dealership staff', async () => {
    renderDashboard(aCustomer())
    await screen.findByRole('article', { name: 'Toyota Corolla' })
    expect(screen.queryByRole('button', { name: /add vehicle/i })).not.toBeInTheDocument()
  })

  it('lets an admin add a vehicle', async () => {
    const swift = aVehicle({ id: 'swift', make: 'Maruti', model: 'Swift', category: 'Hatchback', price: 700000, quantity: 4 })
    api.createVehicle.mockResolvedValue(swift)
    renderDashboard(anAdmin())

    await userEvent.click(await screen.findByRole('button', { name: /add vehicle/i }))
    const dialog = screen.getByRole('dialog')
    await userEvent.type(within(dialog).getByLabelText('Make'), 'Maruti')
    await userEvent.type(within(dialog).getByLabelText('Model'), 'Swift')
    await userEvent.type(within(dialog).getByLabelText('Category'), 'Hatchback')
    await userEvent.type(within(dialog).getByLabelText('Price (₹)'), '700000')
    await userEvent.type(within(dialog).getByLabelText('Quantity in stock'), '4')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Add vehicle' }))

    expect(api.createVehicle).toHaveBeenCalledWith(
      expect.objectContaining({ make: 'Maruti', model: 'Swift', category: 'Hatchback', price: 700000, quantity: 4 }),
    )
    expect(await screen.findByRole('article', { name: 'Maruti Swift' })).toBeInTheDocument()
  })

  it('lets an admin delete a vehicle after confirming', async () => {
    api.deleteVehicle.mockResolvedValue(undefined)
    renderDashboard(anAdmin())

    await userEvent.click(within(await screen.findByRole('article', { name: 'Toyota Corolla' })).getByRole('button', { name: 'Delete Toyota Corolla' }))
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Delete' }))

    expect(api.deleteVehicle).toHaveBeenCalledWith(corolla.id)
    await waitFor(() => expect(screen.queryByRole('article', { name: 'Toyota Corolla' })).not.toBeInTheDocument())
  })

  it('lets an admin restock a vehicle', async () => {
    api.restockVehicle.mockResolvedValue({ vehicle: { ...creta, quantity: 5 }, added: 5 })
    renderDashboard(anAdmin())

    await userEvent.click(within(await screen.findByRole('article', { name: 'Hyundai Creta' })).getByRole('button', { name: 'Restock Hyundai Creta' }))
    const dialog = screen.getByRole('dialog')
    await userEvent.clear(within(dialog).getByLabelText('Cars to add'))
    await userEvent.type(within(dialog).getByLabelText('Cars to add'), '5')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Restock' }))

    expect(api.restockVehicle).toHaveBeenCalledWith('creta', expect.objectContaining({ quantity: 5 }))
    expect(await within(card('Hyundai Creta')).findByText('5 in stock')).toBeInTheDocument()
  })
})
