"""Every change to vehicles and accounts leaves an audit_event row: who, what, which record."""

import pytest

from dealership.models import AppUser, AuditEvent

pytestmark = pytest.mark.django_db

COROLLA = {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 1850000, "quantity": 2}


@pytest.fixture
def corolla(staff_client) -> dict:
    return staff_client.post("/api/vehicles", COROLLA, format="json").json()


def only_event(action: str) -> AuditEvent:
    return AuditEvent.objects.get(action=action)


def test_registration_is_audited(api_client):
    api_client.post(
        "/api/auth/register",
        {"first_name": "Asha", "last_name": "Kumar", "email": "asha@example.com", "password": "Str0ng-Passw0rd!"},
        format="json",
    )

    user = AppUser.objects.get(email="asha@example.com")
    event = only_event("user.registered")
    assert (event.entity_type, event.entity_id, event.actor_user) == ("app_user", user.user_id, user)


def test_adding_a_vehicle_is_audited(staff_user, corolla):
    event = only_event("vehicle.created")

    assert event.actor_user == staff_user
    assert (event.entity_type, str(event.entity_id)) == ("vehicle_listing", corolla["id"])
    assert event.details["quantity"] == 2


def test_updating_a_vehicle_is_audited_with_the_changed_fields(staff_client, corolla):
    staff_client.put(f"/api/vehicles/{corolla['id']}", {"price": 1799000, "category": "Compact"}, format="json")

    event = only_event("vehicle.updated")
    assert sorted(event.details["changed"]) == ["category", "price"]


def test_deleting_a_vehicle_is_audited(admin_client, admin_user, corolla):
    admin_client.delete(f"/api/vehicles/{corolla['id']}")

    event = only_event("vehicle.deleted")
    assert event.actor_user == admin_user
    assert event.details["removed_units"] == 2


def test_restocking_is_audited(admin_client, corolla):
    admin_client.post(f"/api/vehicles/{corolla['id']}/restock", {"quantity": 3}, format="json")

    assert only_event("vehicle.restocked").details["added"] == 3


def test_a_purchase_is_audited_with_its_sale(customer_client, customer_user, corolla):
    sale_id = customer_client.post(f"/api/vehicles/{corolla['id']}/purchase").json()["sale_id"]

    event = only_event("vehicle.purchased")
    assert event.actor_user == customer_user
    assert event.details["sale_id"] == sale_id


def test_a_failed_purchase_leaves_no_audit_event(customer_client, staff_client):
    empty = staff_client.post("/api/vehicles", {**COROLLA, "quantity": 0}, format="json").json()

    customer_client.post(f"/api/vehicles/{empty['id']}/purchase")

    assert not AuditEvent.objects.filter(action="vehicle.purchased").exists()
