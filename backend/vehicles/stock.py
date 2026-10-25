"""
Stock movements for a listing.

Quantity is never stored: it is the number of AVAILABLE acquisitions. So
every change to stock is a change to acquisition rows, recorded together
with an inventory event and the matching ownership change in one
transaction.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from uuid import UUID

from django.db import transaction
from django.utils import timezone

from dealership.errors import NotFound
from dealership.models import (
    Acquisition,
    AppUser,
    InventoryEvent,
    OwnershipPeriod,
    Party,
    Vehicle,
    VehicleListing,
)

PLACEHOLDER_VIN_PREFIX = "PENDING-"


def lock_listing(listing_id: UUID) -> VehicleListing:
    """
    Load an active listing and lock its row until the transaction ends.

    FOR NO KEY UPDATE serialises stock changes on one listing (purchase,
    restock, delete) without blocking inserts that merely reference it.
    """
    listing = (
        VehicleListing.objects.select_for_update(no_key=True, of=("self",))
        .select_related("vehicle_model__make", "dealership")
        .filter(listing_id=listing_id, status=VehicleListing.Status.ACTIVE, deleted_at__isnull=True)
        .first()
    )
    if listing is None:
        raise NotFound("Vehicle not found.")
    return listing


@transaction.atomic
def receive_units(
    listing: VehicleListing,
    *,
    count: int,
    actor: AppUser,
    event_type: str,
    request_key: str,
    unit_cost: Decimal = Decimal("0"),
) -> list[Acquisition]:
    """Bring `count` new physical cars into stock against a listing."""
    dealer_party = listing.dealership.owner_party
    manufacturer_party = listing.vehicle_model.make.manufacturer.organization.party
    received = []
    for index in range(count):
        vehicle = Vehicle.objects.create(vehicle_model=listing.vehicle_model, vin=placeholder_vin())
        unit = Acquisition.objects.create(
            vehicle=vehicle,
            vehicle_model=listing.vehicle_model,
            listing=listing,
            dealership=listing.dealership,
            source_party=manufacturer_party,
            stock_number=new_stock_number(),
            acquisition_type=Acquisition.Type.NEW_SUPPLY,
            ownership_type=Acquisition.Ownership.OWNED,
            inventory_status=Acquisition.Status.AVAILABLE,
            acquisition_cost=unit_cost,
            asking_price=listing.advertised_price,
            currency_code=listing.currency_code,
        )
        transfer_ownership(vehicle, to=dealer_party, reason="ACQUIRED", at=unit.acquired_at)
        InventoryEvent.objects.create(
            acquisition=unit,
            listing=listing,
            performed_by=actor,
            event_type=event_type,
            available_quantity_delta=1,
            idempotency_key=f"{request_key}:{index}",
        )
        received.append(unit)
    return received


def remove_available_units(listing: VehicleListing, *, actor: AppUser, request_key: str) -> int:
    """Take every unsold car of a listing out of stock. Returns how many were removed."""
    at = timezone.now()
    units = listing.acquisitions.select_for_update().filter(inventory_status=Acquisition.Status.AVAILABLE)
    removed = 0
    for index, unit in enumerate(units.order_by("acquired_at", "stock_number")):
        unit.inventory_status = Acquisition.Status.REMOVED
        unit.closed_at = at
        unit.save(update_fields=["inventory_status", "closed_at"])
        InventoryEvent.objects.create(
            acquisition=unit,
            listing=listing,
            performed_by=actor,
            event_type=InventoryEvent.Type.REMOVED,
            available_quantity_delta=-1,
            idempotency_key=f"{request_key}:{index}",
        )
        removed += 1
    return removed


def transfer_ownership(vehicle: Vehicle, *, to: Party, reason: str, at: datetime) -> None:
    """Close the car's current ownership period and open one for the new owner."""
    for period in OwnershipPeriod.objects.select_for_update().filter(vehicle=vehicle, ended_at__isnull=True):
        # The schema requires ended_at > started_at; guard against equal clock readings.
        period.ended_at = max(at, period.started_at + timedelta(microseconds=1))
        period.save(update_fields=["ended_at"])
        at = period.ended_at
    OwnershipPeriod.objects.create(vehicle=vehicle, owner_party=to, started_at=at, reason=reason)


def placeholder_vin() -> str:
    """Identifier for a car whose VIN has not been recorded yet. Real VINs never contain '-'."""
    return f"{PLACEHOLDER_VIN_PREFIX}{uuid.uuid4().hex[:12].upper()}"


def new_stock_number() -> str:
    return f"STK-{uuid.uuid4().hex[:10].upper()}"


def new_request_key(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4()}"


def now() -> datetime:
    return timezone.now()
