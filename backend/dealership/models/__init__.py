"""
Django models for the tables in database/schema.sql.

Every model is unmanaged: the schema (with its CHECK constraints, partial
unique indexes, composite foreign keys and the vehicle_inventory view) is
created by migration 0001 from the SQL file itself, so the SQL stays the
single source of truth for the database structure.
"""

from .access import AppUser, AuthSession, UserRoleAssignment
from .audit import AuditEvent
from .catalog import Make, Vehicle, VehicleInventory, VehicleListing, VehicleModel
from .parties import (
    Customer,
    DealerOrganization,
    Dealership,
    Manufacturer,
    Organization,
    Party,
    Person,
    Site,
    SiteArea,
)
from .sales import Sale, SaleItem
from .stock import Acquisition, InventoryEvent, OwnershipPeriod, PriceChange

__all__ = [
    "Acquisition", "AppUser", "AuditEvent", "AuthSession", "Customer",
    "DealerOrganization", "Dealership", "InventoryEvent", "Make", "Manufacturer",
    "Organization", "OwnershipPeriod", "Party", "Person", "PriceChange", "Sale",
    "SaleItem", "Site", "SiteArea", "UserRoleAssignment", "Vehicle",
    "VehicleInventory", "VehicleListing", "VehicleModel",
]
