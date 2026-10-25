"""The Django migrations must build exactly the reference schema in database/schema.sql."""

import pytest
from django.db import connection

REFERENCE_TABLES = {
    "party", "person", "organization", "customer", "manufacturer",
    "dealer_organization", "dealer_network", "network_membership",
    "dealership", "site", "site_area", "make", "vehicle_model", "vehicle",
    "vehicle_listing", "app_user", "user_role_assignment", "auth_session",
    "acquisition", "ownership_period", "inspection", "refurbishment_order",
    "refurbishment_cost", "location_event", "inventory_event", "price_change",
    "vehicle_document", "reservation", "sale", "sale_item", "payment",
    "trade_in", "audit_event",
}


def _relations(kind: str) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = %s",
            [kind],
        )
        return {row[0] for row in cursor.fetchall()}


@pytest.mark.django_db
def test_migrations_create_every_reference_table():
    missing = REFERENCE_TABLES - _relations("BASE TABLE")
    assert not missing, f"tables missing from the database: {sorted(missing)}"


@pytest.mark.django_db
def test_migrations_create_the_vehicle_inventory_view():
    assert "vehicle_inventory" in _relations("VIEW")
