import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """Real hashers are deliberately slow; tests only need a correct one."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
