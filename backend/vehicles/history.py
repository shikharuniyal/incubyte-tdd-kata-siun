"""Audit-trail entries about a vehicle listing."""

from dealership import audit
from dealership.models import AppUser, VehicleListing

ENTITY_TYPE = "vehicle_listing"


def record(actor: AppUser, action: str, listing: VehicleListing, **details) -> None:
    audit.record(actor=actor, action=action, entity_type=ENTITY_TYPE, entity_id=listing.listing_id, **details)
