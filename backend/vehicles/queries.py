"""Read side: vehicles as the API shows them, built on the vehicle_inventory view."""

from decimal import Decimal
from uuid import UUID

from django.db.models import F, OuterRef, QuerySet, Subquery

from dealership.errors import NotFound
from dealership.models import VehicleInventory, VehicleListing


def inventory() -> QuerySet[VehicleInventory]:
    """All active listings with their derived quantity, plus model year and variant."""
    listing = VehicleListing.objects.filter(listing_id=OuterRef("pk"))
    return (
        VehicleInventory.objects.filter(status=VehicleListing.Status.ACTIVE)
        .annotate(
            model_year=Subquery(listing.values("vehicle_model__model_year")[:1]),
            variant=Subquery(listing.values("vehicle_model__variant")[:1]),
            dealership_name=F("dealership__name"),
        )
        .order_by("make", "model_name", "price", "id")
    )


def search(
    *,
    make: str | None = None,
    model: str | None = None,
    category: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
) -> QuerySet[VehicleInventory]:
    """Case-insensitive partial matches on text; inclusive price bounds. Filters combine."""
    vehicles = inventory()
    if make:
        vehicles = vehicles.filter(make__icontains=make)
    if model:
        vehicles = vehicles.filter(model_name__icontains=model)
    if category:
        vehicles = vehicles.filter(category__icontains=category)
    if min_price is not None:
        vehicles = vehicles.filter(price__gte=min_price)
    if max_price is not None:
        vehicles = vehicles.filter(price__lte=max_price)
    return vehicles


def get_vehicle(listing_id: UUID) -> VehicleInventory:
    vehicle = inventory().filter(pk=listing_id).first()
    if vehicle is None:
        raise NotFound("Vehicle not found.")
    return vehicle
