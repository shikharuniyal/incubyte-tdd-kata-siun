"""POST /api/vehicles/:id/purchase and POST /api/vehicles/:id/restock"""

import threading
import uuid

import pytest
from django.db import connections

from dealership.models import (
    Acquisition,
    InventoryEvent,
    OwnershipPeriod,
    Sale,
    UserRoleAssignment,
    Vehicle,
)

from .factories import client_for, create_dealership, create_user

pytestmark = pytest.mark.django_db

COROLLA = {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 1850000, "quantity": 2}
VIN_A = "MA3FB32S0R0123456"
VIN_B = "MA3FB32S0R0654321"


def purchase_url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}/purchase"


def restock_url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}/restock"


@pytest.fixture
def corolla(staff_client) -> dict:
    return staff_client.post("/api/vehicles", COROLLA, format="json").json()


@pytest.fixture
def sold_out(staff_client) -> dict:
    return staff_client.post("/api/vehicles", {**COROLLA, "model": "Camry", "quantity": 0}, format="json").json()


class TestPurchase:
    def test_decreases_the_quantity_by_one(self, customer_client, corolla):
        response = customer_client.post(purchase_url(corolla["id"]))

        assert response.status_code == 200
        assert response.json()["vehicle"]["quantity"] == 1
        assert response.json()["sale_id"]

    def test_records_a_completed_sale_to_the_buyer_at_the_listed_price(self, customer_client, customer_user, corolla):
        sale_id = customer_client.post(purchase_url(corolla["id"])).json()["sale_id"]

        sale = Sale.objects.get(sale_id=sale_id)
        assert sale.status == Sale.Status.COMPLETED
        assert sale.completed_at is not None
        assert sale.total_amount == 1850000
        assert sale.buyer.party_id == customer_user.person.party_id
        assert sale.created_by == customer_user
        [item] = sale.items.all()
        assert item.agreed_price == 1850000

    def test_marks_one_car_sold_and_logs_the_stock_change(self, customer_client, corolla):
        customer_client.post(purchase_url(corolla["id"]))

        sold = Acquisition.objects.get(listing_id=corolla["id"], inventory_status=Acquisition.Status.SOLD)
        assert sold.closed_at is not None
        event = InventoryEvent.objects.get(acquisition=sold, event_type=InventoryEvent.Type.SOLD)
        assert event.available_quantity_delta == -1

    def test_transfers_ownership_of_that_car_to_the_buyer(self, customer_client, customer_user, corolla):
        customer_client.post(purchase_url(corolla["id"]))

        sold = Acquisition.objects.get(listing_id=corolla["id"], inventory_status=Acquisition.Status.SOLD)
        current = OwnershipPeriod.objects.get(vehicle=sold.vehicle, ended_at__isnull=True)
        assert current.owner_party_id == customer_user.person.party_id

    def test_selling_the_last_car_leaves_quantity_zero(self, customer_client, corolla):
        customer_client.post(purchase_url(corolla["id"]))
        last = customer_client.post(purchase_url(corolla["id"]))

        assert last.status_code == 200
        assert last.json()["vehicle"]["quantity"] == 0

    def test_cannot_buy_when_out_of_stock(self, customer_client, sold_out):
        response = customer_client.post(purchase_url(sold_out["id"]))

        assert response.status_code == 409
        assert "out of stock" in response.json()["detail"]
        assert not Sale.objects.exists()

    def test_a_retried_request_with_the_same_idempotency_key_buys_once(self, customer_client, corolla):
        key = str(uuid.uuid4())

        first = customer_client.post(purchase_url(corolla["id"]), HTTP_IDEMPOTENCY_KEY=key)
        retry = customer_client.post(purchase_url(corolla["id"]), HTTP_IDEMPOTENCY_KEY=key)

        assert first.status_code == retry.status_code == 200
        assert first.json()["sale_id"] == retry.json()["sale_id"]
        assert retry.json()["vehicle"]["quantity"] == 1
        assert Sale.objects.count() == 1

    def test_idempotency_keys_are_scoped_to_the_user(self, customer_client, corolla):
        key = str(uuid.uuid4())
        other = client_for(create_user("other@example.com"))

        customer_client.post(purchase_url(corolla["id"]), HTTP_IDEMPOTENCY_KEY=key)
        other.post(purchase_url(corolla["id"]), HTTP_IDEMPOTENCY_KEY=key)

        assert Sale.objects.count() == 2

    def test_staff_can_also_buy(self, staff_client, corolla):
        assert staff_client.post(purchase_url(corolla["id"])).status_code == 200

    def test_unknown_vehicle_is_404(self, customer_client):
        assert customer_client.post(purchase_url(uuid.uuid4())).status_code == 404

    def test_deleted_vehicle_is_404(self, admin_client, customer_client, corolla):
        admin_client.delete(f"/api/vehicles/{corolla['id']}")

        assert customer_client.post(purchase_url(corolla["id"])).status_code == 404

    def test_requires_authentication(self, api_client, corolla):
        assert api_client.post(purchase_url(corolla["id"])).status_code == 401


class TestRestock:
    def test_admin_restock_increases_the_quantity(self, admin_client, corolla):
        response = admin_client.post(restock_url(corolla["id"]), {"quantity": 3}, format="json")

        assert response.status_code == 200
        assert response.json()["vehicle"]["quantity"] == 5
        assert response.json()["added"] == 3

    def test_logs_a_restock_event_per_car(self, admin_client, corolla):
        admin_client.post(restock_url(corolla["id"]), {"quantity": 3}, format="json")

        events = InventoryEvent.objects.filter(listing_id=corolla["id"], event_type=InventoryEvent.Type.RESTOCKED)
        assert [event.available_quantity_delta for event in events] == [1, 1, 1]

    def test_cars_without_a_known_vin_get_a_placeholder(self, admin_client, sold_out):
        admin_client.post(restock_url(sold_out["id"]), {"quantity": 1}, format="json")

        vehicle = Vehicle.objects.get(acquisitions__listing_id=sold_out["id"])
        assert vehicle.vin.startswith("PENDING-")

    def test_records_the_given_vins(self, admin_client, sold_out):
        response = admin_client.post(restock_url(sold_out["id"]), {"vins": [VIN_A, VIN_B.lower()]}, format="json")

        assert response.json()["vehicle"]["quantity"] == 2
        vins = set(Vehicle.objects.filter(acquisitions__listing_id=sold_out["id"]).values_list("vin", flat=True))
        assert vins == {VIN_A, VIN_B}

    def test_records_the_unit_cost(self, admin_client, sold_out):
        admin_client.post(restock_url(sold_out["id"]), {"quantity": 1, "unit_cost": 1500000}, format="json")

        assert Acquisition.objects.get(listing_id=sold_out["id"]).acquisition_cost == 1500000

    def test_buying_back_a_sold_car_reuses_its_vehicle_record(
        self, admin_client, customer_client, customer_user, sold_out
    ):
        admin_client.post(restock_url(sold_out["id"]), {"vins": [VIN_A]}, format="json")
        customer_client.post(purchase_url(sold_out["id"]))

        response = admin_client.post(restock_url(sold_out["id"]), {"vins": [VIN_A]}, format="json")

        assert response.status_code == 200
        vehicle = Vehicle.objects.get(vin=VIN_A)
        acquisitions = vehicle.acquisitions.order_by("acquired_at")
        assert [a.inventory_status for a in acquisitions] == [Acquisition.Status.SOLD, Acquisition.Status.AVAILABLE]
        returned = acquisitions.last()
        assert returned.acquisition_type == Acquisition.Type.USED_PURCHASE
        assert returned.source_party_id == customer_user.person.party_id
        current_owner = OwnershipPeriod.objects.get(vehicle=vehicle, ended_at__isnull=True)
        assert current_owner.owner_party_id != customer_user.person.party_id

    def test_a_car_already_in_stock_cannot_be_received_again(self, admin_client, sold_out):
        admin_client.post(restock_url(sold_out["id"]), {"vins": [VIN_A]}, format="json")

        response = admin_client.post(restock_url(sold_out["id"]), {"vins": [VIN_A]}, format="json")

        assert response.status_code == 409

    def test_a_vin_of_a_different_model_is_rejected(self, admin_client, staff_client, sold_out):
        admin_client.post(restock_url(sold_out["id"]), {"vins": [VIN_A]}, format="json")
        swift = staff_client.post(
            "/api/vehicles", {"make": "Maruti", "model": "Swift", "category": "Hatchback", "price": 700000}, format="json"
        ).json()

        response = admin_client.post(restock_url(swift["id"]), {"vins": [VIN_A]}, format="json")

        assert response.status_code == 400
        assert "vins" in response.json()

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"quantity": 0},
            {"quantity": -2},
            {"vins": ["TOO-SHORT"]},
            {"vins": ["MA3FB32S0R012345I"]},  # VINs never contain I, O or Q
            {"vins": [VIN_A, VIN_A]},
            {"quantity": 3, "vins": [VIN_A]},
            {"quantity": 1, "unit_cost": -1},
        ],
    )
    def test_rejects_invalid_requests(self, admin_client, corolla, payload):
        response = admin_client.post(restock_url(corolla["id"]), payload, format="json")

        assert response.status_code == 400

    def test_a_retried_request_with_the_same_idempotency_key_restocks_once(self, admin_client, corolla):
        key = str(uuid.uuid4())

        admin_client.post(restock_url(corolla["id"]), {"quantity": 2}, format="json", HTTP_IDEMPOTENCY_KEY=key)
        retry = admin_client.post(restock_url(corolla["id"]), {"quantity": 2}, format="json", HTTP_IDEMPOTENCY_KEY=key)

        assert retry.status_code == 200
        assert retry.json()["vehicle"]["quantity"] == 4

    def test_staff_who_are_not_admins_cannot_restock(self, staff_client, corolla):
        assert staff_client.post(restock_url(corolla["id"]), {"quantity": 1}, format="json").status_code == 403

    def test_customers_cannot_restock(self, customer_client, corolla):
        assert customer_client.post(restock_url(corolla["id"]), {"quantity": 1}, format="json").status_code == 403

    def test_admins_of_another_dealership_cannot_restock(self, corolla):
        outsider = create_user("x@other.test", role=UserRoleAssignment.Role.ADMIN, dealership=create_dealership("Other"))

        response = client_for(outsider).post(restock_url(corolla["id"]), {"quantity": 1}, format="json")

        assert response.status_code == 403

    def test_unknown_vehicle_is_404(self, admin_client):
        assert admin_client.post(restock_url(uuid.uuid4()), {"quantity": 1}, format="json").status_code == 404

    def test_requires_authentication(self, api_client, corolla):
        assert api_client.post(restock_url(corolla["id"]), {"quantity": 1}, format="json").status_code == 401


@pytest.mark.django_db(transaction=True)
def test_two_buyers_racing_for_the_last_car_cannot_both_get_it(transactional_db):
    """Real concurrent transactions on separate connections: exactly one purchase may succeed."""
    dealership = create_dealership()
    staff = create_user("staff@dealer.test", role=UserRoleAssignment.Role.STAFF, dealership=dealership)
    vehicle = client_for(staff).post("/api/vehicles", {**COROLLA, "quantity": 1}, format="json").json()
    buyers = [create_user(f"buyer{i}@example.com") for i in range(2)]
    start = threading.Barrier(len(buyers))
    statuses: list[int] = []

    def buy(user):
        try:
            client = client_for(user)
            start.wait()
            statuses.append(client.post(purchase_url(vehicle["id"])).status_code)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=buy, args=(buyer,)) for buyer in buyers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(statuses) == [200, 409]
    assert Sale.objects.count() == 1
    assert client_for(staff).get(f"/api/vehicles/{vehicle['id']}").json()["quantity"] == 0
