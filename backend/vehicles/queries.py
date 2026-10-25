"""Read side: vehicles as the API shows them, built on the vehicle_inventory view."""

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


def get_vehicle(listing_id: UUID) -> VehicleInventory:
    vehicle = inventory().filter(pk=listing_id).first()
    if vehicle is None:
        raise NotFound("Vehicle not found.")
    return vehicle
