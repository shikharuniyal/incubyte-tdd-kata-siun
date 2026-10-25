"""`python manage.py seed_demo` prepares a dealership, an admin, a customer and stocked vehicles."""

import pytest
from django.core.management import call_command

from accounts.services import authenticate_user
from dealership.models import AppUser, Dealership, UserRoleAssignment, VehicleInventory

pytestmark = pytest.mark.django_db


def seed(**options):
    call_command("seed_demo", admin_password="Admin-Pass-123", customer_password="Customer-Pass-123", **options)


def test_creates_an_admin_who_can_log_in():
    seed()

    admin = authenticate_user(email="admin@dealership.local", password="Admin-Pass-123")
    assert UserRoleAssignment.objects.filter(user=admin, role=UserRoleAssignment.Role.ADMIN).exists()


def test_creates_a_customer_without_staff_roles():
    seed()

    customer = authenticate_user(email="customer@dealership.local", password="Customer-Pass-123")
    assert not UserRoleAssignment.objects.filter(user=customer).exists()


def test_stocks_a_showroom_including_a_sold_out_vehicle():
    seed()

    vehicles = VehicleInventory.objects.all()
    assert vehicles.count() >= 8
    assert any(v.quantity == 0 for v in vehicles)
    assert sum(v.quantity for v in vehicles) > 10
    assert len({v.category for v in vehicles}) >= 4


def test_running_twice_does_not_duplicate_anything():
    seed()
    seed()

    assert Dealership.objects.count() == 1
    assert AppUser.objects.count() == 2
    assert VehicleInventory.objects.count() == len({(v.make, v.model_name) for v in VehicleInventory.objects.all()})
