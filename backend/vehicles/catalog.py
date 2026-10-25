"""Use cases for the vehicle catalogue: adding listings and resolving makes/models."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.db import transaction

from dealership.errors import Conflict
from dealership.models import (
    AppUser,
    Dealership,
    InventoryEvent,
    Make,
    Manufacturer,
    Organization,
    Party,
    PriceChange,
    VehicleListing,
    VehicleModel,
)

from . import policies, stock


@dataclass(frozen=True)
class VehicleSpec:
    """What identifies the kind of car being listed."""

    make: str
    model: str
    category: str
    model_year: int
    variant: str = "BASE"


@transaction.atomic
def add_vehicle(
    *,
    actor: AppUser,
    spec: VehicleSpec,
    price: Decimal,
    quantity: int,
    condition: str = VehicleListing.Condition.NEW,
    currency_code: str = "INR",
    dealership_id: UUID | None = None,
) -> VehicleListing:
    dealership_id = policies.resolve_staff_dealership(actor, dealership_id)
    listing = VehicleListing.objects.create(
        dealership=Dealership.objects.get(dealership_id=dealership_id),
        vehicle_model=resolve_model(spec),
        condition_class=condition,
        advertised_price=price,
        currency_code=currency_code,
    )
    if quantity:
        stock.receive_units(
            listing,
            count=quantity,
            vins=None,
            actor=actor,
            event_type=InventoryEvent.Type.ACQUIRED,
            request_key=stock.new_request_key(f"create:{listing.listing_id}"),
        )
    return listing


@dataclass(frozen=True)
class VehicleChanges:
    """Fields an update may change. None means "leave as it is"."""

    make: str | None = None
    model: str | None = None
    category: str | None = None
    model_year: int | None = None
    variant: str | None = None
    price: Decimal | None = None
    condition: str | None = None


@transaction.atomic
def update_vehicle(*, actor: AppUser, listing_id: UUID, changes: VehicleChanges) -> VehicleListing:
    listing = stock.lock_listing(listing_id)
    policies.require_staff(actor, listing.dealership_id)

    _apply_model_changes(listing, changes)
    _apply_price_change(listing, changes.price, actor)
    if changes.condition:
        listing.condition_class = changes.condition
    listing.save(update_fields=["vehicle_model", "advertised_price", "condition_class"])
    return listing


@transaction.atomic
def delete_vehicle(*, actor: AppUser, listing_id: UUID) -> None:
    """Archive the listing (history is kept) and take its unsold cars out of stock."""
    listing = stock.lock_listing(listing_id)
    policies.require_admin(actor, listing.dealership_id)

    stock.remove_available_units(listing, actor=actor, request_key=stock.new_request_key(f"delete:{listing_id}"))
    listing.status = VehicleListing.Status.ARCHIVED
    listing.deleted_at = stock.now()
    listing.save(update_fields=["status", "deleted_at"])


def _apply_model_changes(listing: VehicleListing, changes: VehicleChanges) -> None:
    current = listing.vehicle_model
    wanted = VehicleSpec(
        make=changes.make or current.make.name,
        model=changes.model or current.name,
        category=changes.category or current.category,
        model_year=changes.model_year or current.model_year,
        variant=changes.variant or current.variant,
    )
    if _identity(wanted) == _identity(_spec_of(current)):
        if wanted.category != current.category:
            current.category = wanted.category
            current.save(update_fields=["category"])
        return

    if listing.acquisitions.exists():
        raise Conflict(
            "Make, model, year and variant cannot change once cars have been stocked "
            "against this vehicle. Add a new vehicle instead."
        )
    listing.vehicle_model = resolve_model(wanted)


def _apply_price_change(listing: VehicleListing, new_price: Decimal | None, actor: AppUser) -> None:
    if new_price is None or new_price == listing.advertised_price:
        return
    PriceChange.objects.create(
        listing=listing, changed_by=actor, old_price=listing.advertised_price, new_price=new_price
    )
    listing.advertised_price = new_price


def _spec_of(model: VehicleModel) -> VehicleSpec:
    return VehicleSpec(
        make=model.make.name,
        model=model.name,
        category=model.category,
        model_year=model.model_year,
        variant=model.variant,
    )


def _identity(spec: VehicleSpec) -> tuple:
    """What makes two specs the same model (names compare case-insensitively)."""
    return spec.make.lower(), spec.model.lower(), spec.model_year, spec.variant.lower()


def resolve_model(spec: VehicleSpec) -> VehicleModel:
    """Find the make/model matching the spec (case-insensitively) or create it."""
    make = Make.objects.filter(name__iexact=spec.make).first() or _create_make(spec.make)
    model, created = VehicleModel.objects.get_or_create(
        make=make,
        name__iexact=spec.model,
        model_year=spec.model_year,
        variant__iexact=spec.variant,
        defaults={"name": spec.model, "variant": spec.variant, "category": spec.category},
    )
    if not created and model.category != spec.category:
        model.category = spec.category
        model.save(update_fields=["category"])
    return model


def _create_make(name: str) -> Make:
    """A make the system has not seen yet; record its manufacturer as an organisation."""
    party = Party.objects.create(party_type=Party.Type.ORGANIZATION, display_name=name)
    organization = Organization.objects.create(party=party, registered_name=name)
    manufacturer = Manufacturer.objects.create(organization=organization)
    return Make.objects.create(manufacturer=manufacturer, name=name)
