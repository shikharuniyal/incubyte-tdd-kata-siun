"""POST /api/vehicles and GET /api/vehicles."""

import pytest
from django.utils import timezone

from dealership.models import (
    Acquisition,
    InventoryEvent,
    Make,
    OwnershipPeriod,
    UserRoleAssignment,
    Vehicle,
    VehicleListing,
)

from .factories import client_for, create_dealership, create_user, grant_role

pytestmark = pytest.mark.django_db

VEHICLES_URL = "/api/vehicles"

COROLLA = {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 1850000, "quantity": 3}


def add_vehicle(client, **overrides):
    return client.post(VEHICLES_URL, {**COROLLA, **overrides}, format="json")


class TestCreateVehicle:
    def test_staff_can_add_a_vehicle(self, staff_client, dealership):
        response = add_vehicle(staff_client)

        assert response.status_code == 201
        body = response.json()
        assert body["id"]
        assert body["make"] == "Toyota"
        assert body["model"] == "Corolla"
        assert body["category"] == "Sedan"
        assert body["price"] == 1850000
        assert body["quantity"] == 3
        assert body["condition"] == "NEW"
        assert body["currency_code"] == "INR"
        assert body["dealership_id"] == str(dealership.dealership_id)

    def test_each_unit_in_stock_is_a_physical_car_with_its_own_vin(self, staff_client):
        listing_id = add_vehicle(staff_client).json()["id"]

        units = Acquisition.objects.filter(listing_id=listing_id)
        assert units.count() == 3
        assert all(unit.inventory_status == Acquisition.Status.AVAILABLE for unit in units)
        assert Vehicle.objects.values("vin").distinct().count() == 3
        assert len({unit.stock_number for unit in units}) == 3

    def test_records_stock_events_and_dealer_ownership(self, staff_client, dealership):
        listing_id = add_vehicle(staff_client).json()["id"]

        events = InventoryEvent.objects.filter(listing_id=listing_id)
        assert events.count() == 3
        assert {event.available_quantity_delta for event in events} == {1}
        owners = OwnershipPeriod.objects.filter(ended_at__isnull=True).values_list("owner_party_id", flat=True)
        assert set(owners) == {dealership.dealer_org.organization.party_id}

    def test_reuses_an_existing_make_case_insensitively(self, staff_client):
        add_vehicle(staff_client)
        add_vehicle(staff_client, make="TOYOTA", model="Camry")

        assert Make.objects.count() == 1

    def test_quantity_defaults_to_zero(self, staff_client):
        payload = {k: v for k, v in COROLLA.items() if k != "quantity"}

        response = staff_client.post(VEHICLES_URL, payload, format="json")

        assert response.status_code == 201
        assert response.json()["quantity"] == 0

    def test_accepts_optional_year_variant_and_condition(self, staff_client):
        response = add_vehicle(staff_client, model_year=2022, variant="ZX", condition="USED")

        body = response.json()
        assert body["model_year"] == 2022
        assert body["variant"] == "ZX"
        assert body["condition"] == "USED"

    def test_customers_cannot_add_vehicles(self, customer_client):
        response = add_vehicle(customer_client)

        assert response.status_code == 403
        assert not VehicleListing.objects.exists()

    def test_requires_authentication(self, api_client):
        assert add_vehicle(api_client).status_code == 401

    @pytest.mark.parametrize("field", ["make", "model", "category", "price"])
    def test_requires_core_fields(self, staff_client, field):
        payload = {k: v for k, v in COROLLA.items() if k != field}

        response = staff_client.post(VEHICLES_URL, payload, format="json")

        assert response.status_code == 400
        assert field in response.json()

    @pytest.mark.parametrize("field, value", [("price", -1), ("quantity", -1), ("make", "   "), ("condition", "BROKEN")])
    def test_rejects_invalid_values(self, staff_client, field, value):
        response = add_vehicle(staff_client, **{field: value})

        assert response.status_code == 400
        assert field in response.json()

    def test_staff_of_several_dealerships_must_choose_one(self, staff_user, staff_client):
        other = create_dealership("Second Branch")
        grant_role(staff_user, other, UserRoleAssignment.Role.STAFF)

        without_choice = add_vehicle(staff_client)
        with_choice = add_vehicle(staff_client, dealership_id=str(other.dealership_id))

        assert without_choice.status_code == 400
        assert "dealership_id" in without_choice.json()
        assert with_choice.status_code == 201
        assert with_choice.json()["dealership_id"] == str(other.dealership_id)

    def test_cannot_add_to_a_dealership_without_a_role_there(self, staff_client):
        other = create_dealership("Someone Else's Dealership")

        response = add_vehicle(staff_client, dealership_id=str(other.dealership_id))

        assert response.status_code == 403


class TestListVehicles:
    def test_lists_every_vehicle_with_its_quantity(self, staff_client, customer_client):
        add_vehicle(staff_client)
        add_vehicle(staff_client, make="Hyundai", model="Creta", category="SUV", price=1500000, quantity=0)

        response = customer_client.get(VEHICLES_URL)

        assert response.status_code == 200
        quantities = {(v["make"], v["model"]): v["quantity"] for v in response.json()}
        assert quantities == {("Toyota", "Corolla"): 3, ("Hyundai", "Creta"): 0}

    def test_quantity_counts_only_cars_still_available(self, staff_client, customer_client):
        listing_id = add_vehicle(staff_client).json()["id"]
        sold = Acquisition.objects.filter(listing_id=listing_id).first()
        sold.inventory_status = Acquisition.Status.SOLD
        sold.closed_at = timezone.now()
        sold.save()

        [vehicle] = customer_client.get(VEHICLES_URL).json()

        assert vehicle["quantity"] == 2

    def test_hides_deleted_vehicles(self, staff_client, customer_client):
        listing_id = add_vehicle(staff_client).json()["id"]
        VehicleListing.objects.filter(listing_id=listing_id).update(
            status=VehicleListing.Status.ARCHIVED, deleted_at=timezone.now()
        )

        assert customer_client.get(VEHICLES_URL).json() == []

    def test_requires_authentication(self, api_client):
        assert api_client.get(VEHICLES_URL).status_code == 401

    def test_a_user_from_another_dealership_sees_the_same_catalogue(self, staff_client):
        add_vehicle(staff_client)
        outsider = create_user("outsider@other.test", role=UserRoleAssignment.Role.STAFF, dealership=create_dealership("Other"))

        assert len(client_for(outsider).get(VEHICLES_URL).json()) == 1
