import pytest
from rest_framework.test import APIClient

from dealership.models import UserRoleAssignment

from .factories import client_for, create_dealership, create_user


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """Real hashers are deliberately slow; tests only need a correct one."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def dealership(db):
    return create_dealership()


@pytest.fixture
def admin_user(dealership):
    return create_user("admin@dealer.test", role=UserRoleAssignment.Role.ADMIN, dealership=dealership)


@pytest.fixture
def staff_user(dealership):
    return create_user("staff@dealer.test", role=UserRoleAssignment.Role.STAFF, dealership=dealership)


@pytest.fixture
def customer_user(db):
    return create_user("customer@example.com")


@pytest.fixture
def admin_client(admin_user) -> APIClient:
    return client_for(admin_user)


@pytest.fixture
def staff_client(staff_user) -> APIClient:
    return client_for(staff_user)


@pytest.fixture
def customer_client(customer_user) -> APIClient:
    return client_for(customer_user)
