"""Small builders for test data. They create real rows in the test database."""

from rest_framework.test import APIClient

from accounts.services import register_user
from accounts.tokens import issue_access_token
from dealership.models import (
    AppUser,
    DealerOrganization,
    Dealership,
    Organization,
    Party,
    UserRoleAssignment,
)

PASSWORD = "Str0ng-Passw0rd!"


def create_dealership(name: str = "Incubyte Motors") -> Dealership:
    party = Party.objects.create(party_type=Party.Type.ORGANIZATION, display_name=f"{name} Pvt Ltd")
    organization = Organization.objects.create(party=party, registered_name=f"{name} Pvt Ltd")
    dealer_org = DealerOrganization.objects.create(organization=organization)
    return Dealership.objects.create(dealer_org=dealer_org, name=name)


def create_user(email: str, *, role: str | None = None, dealership: Dealership | None = None) -> AppUser:
    user = register_user(first_name="Test", last_name="User", email=email, password=PASSWORD)
    if role:
        grant_role(user, dealership, role)
    return user


def grant_role(user: AppUser, dealership: Dealership, role: str) -> UserRoleAssignment:
    return UserRoleAssignment.objects.create(user=user, dealership=dealership, role=role)


def client_for(user: AppUser) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_access_token(user)}")
    return client
