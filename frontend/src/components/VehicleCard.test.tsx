import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { aVehicle } from '../test/fixtures'
import { VehicleCard, type VehicleCardProps } from './VehicleCard'

function renderCard(props: Partial<VehicleCardProps> = {}) {
  const handlers = { onPurchase: vi.fn(), onEdit: vi.fn(), onRestock: vi.fn(), onDelete: vi.fn() }
  render(<VehicleCard vehicle={aVehicle()} canManage={false} canAdminister={false} {...handlers} {...props} />)
  return handlers
}

describe('VehicleCard', () => {
  it('shows the vehicle’s make, model, category, price and stock', () => {
    renderCard()

    expect(screen.getByRole('heading', { name: 'Toyota Corolla' })).toBeInTheDocument()
    expect(screen.getByText('Sedan')).toBeInTheDocument()
    expect(screen.getByText('₹18,50,000')).toBeInTheDocument()
    expect(screen.getByText('3 in stock')).toBeInTheDocument()
  })

  it('lets a customer purchase a vehicle that is in stock', async () => {
    const { onPurchase } = renderCard()

    await userEvent.click(screen.getByRole('button', { name: /purchase/i }))

    expect(onPurchase).toHaveBeenCalledWith(aVehicle())
  })

  it('disables Purchase when the quantity is zero', async () => {
    const { onPurchase } = renderCard({ vehicle: aVehicle({ quantity: 0 }) })

    const button = screen.getByRole('button', { name: /purchase/i })
    expect(button).toBeDisabled()
    expect(screen.getByText('Sold out')).toBeInTheDocument()
    await userEvent.click(button)
    expect(onPurchase).not.toHaveBeenCalled()
  })

  it('disables Purchase while a purchase is in progress', () => {
    renderCard({ purchasing: true })

    expect(screen.getByRole('button', { name: /purchasing/i })).toBeDisabled()
  })

  it('hides management actions from customers', () => {
    renderCard()

    expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /restock/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
  })

  it('lets staff edit but not restock or delete', () => {
    renderCard({ canManage: true })

    expect(screen.getByRole('button', { name: 'Edit Toyota Corolla' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /restock/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
  })

  it('gives admins edit, restock and delete actions', async () => {
    const { onEdit, onRestock, onDelete } = renderCard({ canManage: true, canAdminister: true })

    await userEvent.click(screen.getByRole('button', { name: 'Edit Toyota Corolla' }))
    await userEvent.click(screen.getByRole('button', { name: 'Restock Toyota Corolla' }))
    await userEvent.click(screen.getByRole('button', { name: 'Delete Toyota Corolla' }))

    expect(onEdit).toHaveBeenCalledOnce()
    expect(onRestock).toHaveBeenCalledOnce()
    expect(onDelete).toHaveBeenCalledOnce()
  })
})
