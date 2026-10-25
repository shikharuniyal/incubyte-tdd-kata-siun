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

from django.db import transaction
from django.utils import timezone

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
