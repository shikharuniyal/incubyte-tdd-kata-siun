"""
Stock movements for a listing: receiving cars, selling them and removing them.

Quantity is never stored: it is the number of AVAILABLE acquisitions. So
every change to stock is a change to acquisition rows, recorded together
with an inventory event and the matching ownership change in one
transaction. The listing row is locked first, so concurrent operations on
the same listing run one after another and can never sell the same car
twice or oversell.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from dealership import audit
from dealership.errors import Conflict, NotFound, OutOfStock, ValidationFailed
from dealership.models import (
    Acquisition,
    AppUser,
    Customer,
    InventoryEvent,
    OwnershipPeriod,
    Sale,
    SaleItem,
    Vehicle,
    VehicleListing,
)

from . import policies

PLACEHOLDER_VIN_PREFIX = "PENDING-"


@transaction.atomic
def purchase(*, buyer: AppUser, listing_id: UUID, idempotency_key: str | None = None) -> Sale:
    """
    Sell one available car of the listing to the buyer.

    A retried request carrying the same idempotency key returns the sale
    made by the first attempt instead of buying a second car.
    """
    request_key = _request_key("purchase", buyer, idempotency_key)
    previous_sale = _sale_made_by(request_key)
    if previous_sale is not None:
        return previous_sale

    listing = lock_listing(listing_id)
    unit = (
        Acquisition.objects.select_for_update(skip_locked=True, of=("self",))
        .select_related("vehicle")
        .filter(listing=listing, inventory_status=Acquisition.Status.AVAILABLE)
        .order_by("acquired_at", "stock_number")  # Oldest stock leaves first.
        .first()
    )
    if unit is None:
        model = listing.vehicle_model
        raise OutOfStock(f"{model.make.name} {model.name} is out of stock.")

    at = timezone.now()
    customer, _ = Customer.objects.get_or_create(party_id=buyer.person_id)
    sale = Sale.objects.create(
        dealership=listing.dealership,
        buyer=customer,
        created_by=buyer,
        status=Sale.Status.COMPLETED,
        total_amount=listing.advertised_price,
        currency_code=listing.currency_code,
        completed_at=at,
    )
    SaleItem.objects.create(
        sale=sale, acquisition=unit, dealership=listing.dealership, agreed_price=listing.advertised_price
    )
    unit.inventory_status = Acquisition.Status.SOLD
    unit.closed_at = at
    unit.save(update_fields=["inventory_status", "closed_at"])
    transfer_ownership(unit.vehicle, to_party_id=customer.party_id, reason="SOLD", at=at)
    InventoryEvent.objects.create(
        acquisition=unit,
        listing=listing,
        performed_by=buyer,
        event_type=InventoryEvent.Type.SOLD,
        available_quantity_delta=-1,
        idempotency_key=request_key,
    )
    audit.record(
        actor=buyer,
        action="vehicle.purchased",
        entity_type="vehicle_listing",
        entity_id=listing.listing_id,
        sale_id=sale.sale_id,
        stock_number=unit.stock_number,
    )
    return sale


@transaction.atomic
def restock(
    *,
    actor: AppUser,
    listing_id: UUID,
    quantity: int,
    vins: list[str] | None = None,
    unit_cost: Decimal = Decimal("0"),
    idempotency_key: str | None = None,
) -> int:
    """Admin only: receive `quantity` cars (optionally with their VINs). Returns cars added."""
    listing = lock_listing(listing_id)
    policies.require_admin(actor, listing.dealership_id)

    request_key = _request_key("restock", actor, idempotency_key)
    if InventoryEvent.objects.filter(idempotency_key=f"{request_key}:0").exists():
        return quantity  # Already applied by an earlier attempt of this request.

    receive_units(
        listing,
        count=quantity,
        vins=vins,
        actor=actor,
        event_type=InventoryEvent.Type.RESTOCKED,
        request_key=request_key,
        unit_cost=unit_cost,
    )
    audit.record(
        actor=actor,
        action="vehicle.restocked",
        entity_type="vehicle_listing",
        entity_id=listing.listing_id,
        added=quantity,
    )
    return quantity


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
    vins: list[str] | None = None,
    unit_cost: Decimal = Decimal("0"),
) -> list[Acquisition]:
    """
    Bring `count` physical cars into stock against a listing.

    A car whose VIN the system already knows (it was sold and is now bought
    back) keeps its vehicle record and gets a new acquisition period.
    """
    dealer_party_id = listing.dealership.owner_party.party_id
    manufacturer_party_id = listing.vehicle_model.make.manufacturer.organization.party_id
    received = []
    for index in range(count):
        vehicle, previous_owner_id = _vehicle_to_receive(listing, vins[index] if vins else None)
        is_new_car = previous_owner_id is None and listing.condition_class == VehicleListing.Condition.NEW
        unit = Acquisition.objects.create(
            vehicle=vehicle,
            vehicle_model=listing.vehicle_model,
            listing=listing,
            dealership=listing.dealership,
            source_party_id=previous_owner_id or manufacturer_party_id,
            stock_number=new_stock_number(),
            acquisition_type=Acquisition.Type.NEW_SUPPLY if is_new_car else Acquisition.Type.USED_PURCHASE,
            ownership_type=Acquisition.Ownership.OWNED,
            inventory_status=Acquisition.Status.AVAILABLE,
            acquisition_cost=unit_cost,
            asking_price=listing.advertised_price,
            currency_code=listing.currency_code,
        )
        transfer_ownership(vehicle, to_party_id=dealer_party_id, reason="ACQUIRED", at=unit.acquired_at)
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


def transfer_ownership(vehicle: Vehicle, *, to_party_id: UUID, reason: str, at: datetime) -> None:
    """Close the car's current ownership period and open one for the new owner."""
    for period in OwnershipPeriod.objects.select_for_update().filter(vehicle=vehicle, ended_at__isnull=True):
        # The schema requires ended_at > started_at; guard against equal clock readings.
        period.ended_at = max(at, period.started_at + timedelta(microseconds=1))
        period.save(update_fields=["ended_at"])
        at = period.ended_at
    OwnershipPeriod.objects.create(vehicle=vehicle, owner_party_id=to_party_id, started_at=at, reason=reason)


def _vehicle_to_receive(listing: VehicleListing, vin: str | None) -> tuple[Vehicle, UUID | None]:
    """The vehicle record for an incoming car, and its previous owner if it is a known car."""
    if vin is None:
        return Vehicle.objects.create(vehicle_model=listing.vehicle_model, vin=placeholder_vin()), None

    vehicle = Vehicle.objects.select_for_update().filter(vin=vin).first()
    if vehicle is None:
        return Vehicle.objects.create(vehicle_model=listing.vehicle_model, vin=vin), None
    if vehicle.vehicle_model_id != listing.vehicle_model_id:
        raise ValidationFailed(f"VIN {vin} belongs to a different model.", field="vins")
    if vehicle.acquisitions.filter(closed_at__isnull=True).exists():
        raise Conflict(f"VIN {vin} is already in stock.")

    current_owner = OwnershipPeriod.objects.filter(vehicle=vehicle, ended_at__isnull=True).first()
    return vehicle, current_owner.owner_party_id if current_owner else None


def _sale_made_by(request_key: str) -> Sale | None:
    event = (
        InventoryEvent.objects.filter(idempotency_key=request_key)
        .select_related("acquisition__sale_item__sale")
        .first()
    )
    return event.acquisition.sale_item.sale if event else None


def _request_key(operation: str, user: AppUser, idempotency_key: str | None) -> str:
    """Client keys are scoped per user, so two users can never collide."""
    if idempotency_key:
        return f"{operation}:{user.user_id}:{idempotency_key}"
    return new_request_key(operation)


def placeholder_vin() -> str:
    """Identifier for a car whose VIN has not been recorded yet. Real VINs never contain '-'."""
    return f"{PLACEHOLDER_VIN_PREFIX}{uuid.uuid4().hex[:12].upper()}"


def new_stock_number() -> str:
    return f"STK-{uuid.uuid4().hex[:10].upper()}"


def new_request_key(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4()}"


def now() -> datetime:
    return timezone.now()
