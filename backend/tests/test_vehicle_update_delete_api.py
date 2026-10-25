"""GET, PUT and DELETE /api/vehicles/:id"""

import uuid

import pytest

from dealership.models import (
    Acquisition,
    InventoryEvent,
    PriceChange,
    UserRoleAssignment,
    VehicleListing,
)

from .factories import client_for, create_dealership, create_user

pytestmark = pytest.mark.django_db

COROLLA = {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 1850000, "quantity": 2}


def url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}"


@pytest.fixture
def corolla(staff_client) -> dict:
    return staff_client.post("/api/vehicles", COROLLA, format="json").json()


@pytest.fixture
def unstocked(staff_client) -> dict:
    return staff_client.post("/api/vehicles", {**COROLLA, "quantity": 0}, format="json").json()


class TestGetVehicle:
    def test_returns_one_vehicle(self, customer_client, corolla):
        response = customer_client.get(url(corolla["id"]))

        assert response.status_code == 200
        assert response.json() == corolla

    def test_unknown_id_is_404(self, customer_client):
        assert customer_client.get(url(uuid.uuid4())).status_code == 404


class TestUpdateVehicle:
    def test_staff_can_change_the_price(self, staff_client, corolla):
        response = staff_client.put(url(corolla["id"]), {"price": 1799000}, format="json")

        assert response.status_code == 200
        assert response.json()["price"] == 1799000
        assert response.json()["quantity"] == 2

    def test_a_price_change_is_recorded(self, staff_client, staff_user, corolla):
        staff_client.put(url(corolla["id"]), {"price": 1799000}, format="json")

        change = PriceChange.objects.get(listing_id=corolla["id"])
        assert (change.old_price, change.new_price) == (1850000, 1799000)
        assert change.changed_by == staff_user

    def test_an_unchanged_price_records_nothing(self, staff_client, corolla):
        staff_client.put(url(corolla["id"]), {"price": 1850000}, format="json")

        assert not PriceChange.objects.exists()

    def test_can_change_category_and_condition(self, staff_client, corolla):
        response = staff_client.put(url(corolla["id"]), {"category": "Compact Sedan", "condition": "USED"}, format="json")

        assert response.json()["category"] == "Compact Sedan"
        assert response.json()["condition"] == "USED"

    def test_can_rename_make_and_model_before_any_car_is_stocked(self, staff_client, unstocked):
        response = staff_client.put(url(unstocked["id"]), {"make": "Honda", "model": "City"}, format="json")

        assert response.status_code == 200
        assert (response.json()["make"], response.json()["model"]) == ("Honda", "City")

    def test_cannot_change_the_model_of_cars_already_in_stock(self, staff_client, corolla):
        response = staff_client.put(url(corolla["id"]), {"model": "Camry"}, format="json")

        assert response.status_code == 409
        assert staff_client.get(url(corolla["id"])).json()["model"] == "Corolla"

    def test_a_case_only_rename_is_not_a_model_change(self, staff_client, corolla):
        response = staff_client.put(url(corolla["id"]), {"make": "TOYOTA", "model": "corolla"}, format="json")

        assert response.status_code == 200

    def test_quantity_cannot_be_edited_directly(self, staff_client, corolla):
        response = staff_client.put(url(corolla["id"]), {"quantity": 10}, format="json")

        assert response.status_code == 400
        assert "quantity" in response.json()

    def test_rejects_an_invalid_price(self, staff_client, corolla):
        response = staff_client.put(url(corolla["id"]), {"price": -5}, format="json")

        assert response.status_code == 400

    def test_customers_cannot_update(self, customer_client, corolla):
        response = customer_client.put(url(corolla["id"]), {"price": 1}, format="json")

        assert response.status_code == 403

    def test_staff_of_another_dealership_cannot_update(self, corolla):
        outsider = create_user("x@other.test", role=UserRoleAssignment.Role.ADMIN, dealership=create_dealership("Other"))

        response = client_for(outsider).put(url(corolla["id"]), {"price": 1}, format="json")

        assert response.status_code == 403

    def test_unknown_vehicle_is_404(self, staff_client):
        assert staff_client.put(url(uuid.uuid4()), {"price": 1}, format="json").status_code == 404

    def test_requires_authentication(self, api_client, corolla):
        assert api_client.put(url(corolla["id"]), {"price": 1}, format="json").status_code == 401


class TestDeleteVehicle:
    def test_admin_can_delete_a_vehicle(self, admin_client, customer_client, corolla):
        response = admin_client.delete(url(corolla["id"]))

        assert response.status_code == 204
        assert customer_client.get("/api/vehicles").json() == []
        assert customer_client.get(url(corolla["id"])).status_code == 404

    def test_delete_archives_the_listing_instead_of_erasing_history(self, admin_client, corolla):
        admin_client.delete(url(corolla["id"]))

        listing = VehicleListing.objects.get(listing_id=corolla["id"])
        assert listing.status == VehicleListing.Status.ARCHIVED
        assert listing.deleted_at is not None

    def test_unsold_cars_are_taken_out_of_stock(self, admin_client, corolla):
        admin_client.delete(url(corolla["id"]))

        units = Acquisition.objects.filter(listing_id=corolla["id"])
        assert {unit.inventory_status for unit in units} == {Acquisition.Status.REMOVED}
        assert all(unit.closed_at for unit in units)
        removals = InventoryEvent.objects.filter(listing_id=corolla["id"], event_type=InventoryEvent.Type.REMOVED)
        assert [event.available_quantity_delta for event in removals] == [-1, -1]

    def test_staff_who_are_not_admins_cannot_delete(self, staff_client, corolla):
        assert staff_client.delete(url(corolla["id"])).status_code == 403

    def test_customers_cannot_delete(self, customer_client, corolla):
        assert customer_client.delete(url(corolla["id"])).status_code == 403

    def test_admins_of_another_dealership_cannot_delete(self, corolla):
        outsider = create_user("x@other.test", role=UserRoleAssignment.Role.ADMIN, dealership=create_dealership("Other"))

        assert client_for(outsider).delete(url(corolla["id"])).status_code == 403

    def test_deleting_twice_is_404(self, admin_client, corolla):
        admin_client.delete(url(corolla["id"]))

        assert admin_client.delete(url(corolla["id"])).status_code == 404

    def test_requires_authentication(self, api_client, corolla):
        assert api_client.delete(url(corolla["id"])).status_code == 401
