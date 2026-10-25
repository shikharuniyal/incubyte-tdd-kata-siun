"""Demo data so a fresh installation has a dealership, accounts and a stocked showroom."""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from accounts.services import register_user
from dealership.models import (
    AppUser,
    DealerOrganization,
    Dealership,
    Organization,
    Party,
    Site,
    SiteArea,
    UserRoleAssignment,
    VehicleListing,
)

from . import catalog

DEALERSHIP_NAME = "Incubyte Motors - Main Branch"
DEALER_ORG_NAME = "Incubyte Motors Pvt Ltd"
ADMIN_EMAIL = "admin@dealership.local"
CUSTOMER_EMAIL = "customer@dealership.local"


@dataclass(frozen=True)
class DemoVehicle:
    make: str
    model: str
    category: str
    model_year: int
    price: int
    quantity: int
    condition: str = VehicleListing.Condition.NEW


SHOWROOM = [
    DemoVehicle("Toyota", "Corolla Altis", "Sedan", 2024, 1_850_000, 5),
    DemoVehicle("Toyota", "Fortuner", "SUV", 2024, 3_550_000, 3),
    DemoVehicle("Hyundai", "Creta", "SUV", 2024, 1_520_000, 4),
    DemoVehicle("Tata", "Nexon EV", "Electric", 2024, 1_450_000, 0),
    DemoVehicle("Maruti Suzuki", "Swift", "Hatchback", 2024, 699_000, 8),
    DemoVehicle("Mahindra", "Thar", "Off-road", 2023, 1_650_000, 2),
    DemoVehicle("Honda", "City", "Sedan", 2021, 985_000, 1, VehicleListing.Condition.USED),
    DemoVehicle("Kia", "Seltos", "SUV", 2024, 1_610_000, 6),
    DemoVehicle("BMW", "3 Series", "Luxury", 2024, 6_050_000, 1),
    DemoVehicle("Hyundai", "i20", "Hatchback", 2020, 640_000, 0, VehicleListing.Condition.REFURBISHED),
]


@transaction.atomic
def seed(*, admin_password: str, customer_password: str) -> Dealership:
    """Create whatever is missing. Safe to run repeatedly."""
    dealership = _dealership()
    admin = _user(ADMIN_EMAIL, "Dealer", "Admin", admin_password)
    UserRoleAssignment.objects.get_or_create(
        user=admin, dealership=dealership, role=UserRoleAssignment.Role.ADMIN, revoked_at=None
    )
    _user(CUSTOMER_EMAIL, "Demo", "Customer", customer_password)

    for vehicle in SHOWROOM:
        already_listed = VehicleListing.objects.filter(
            dealership=dealership,
            vehicle_model__make__name=vehicle.make,
            vehicle_model__name=vehicle.model,
        ).exists()
        if not already_listed:
            catalog.add_vehicle(
                actor=admin,
                spec=catalog.VehicleSpec(vehicle.make, vehicle.model, vehicle.category, vehicle.model_year),
                price=Decimal(vehicle.price),
                quantity=vehicle.quantity,
                condition=vehicle.condition,
                dealership_id=dealership.dealership_id,
            )
    return dealership


def _dealership() -> Dealership:
    existing = Dealership.objects.filter(name=DEALERSHIP_NAME).first()
    if existing:
        return existing

    party = Party.objects.create(party_type=Party.Type.ORGANIZATION, display_name=DEALER_ORG_NAME)
    organization = Organization.objects.create(party=party, registered_name=DEALER_ORG_NAME)
    dealer_org = DealerOrganization.objects.create(organization=organization)
    dealership = Dealership.objects.create(dealer_org=dealer_org, name=DEALERSHIP_NAME)
    site = Site.objects.create(
        dealership=dealership,
        owner_party=party,
        name="Main Showroom",
        address="12 MG Road, Bengaluru",
        site_type=Site.Type.BRANCH,
    )
    SiteArea.objects.create(site=site, name="Showroom Floor", area_type=SiteArea.Type.SHOWROOM, capacity=40)
    return dealership


def _user(email: str, first_name: str, last_name: str, password: str) -> AppUser:
    existing = AppUser.objects.filter(email=email).first()
    if existing:
        return existing
    return register_user(first_name=first_name, last_name=last_name, email=email, password=password)
