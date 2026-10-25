"""Dealership-scoped roles. A user may hold different roles at different dealerships."""

from collections.abc import Iterable
from uuid import UUID

from django.db.models import QuerySet

from dealership.models import AppUser, UserRoleAssignment

Role = UserRoleAssignment.Role
STAFF_ROLES = (Role.ADMIN, Role.MANAGER, Role.STAFF)


def active_role_assignments(user: AppUser) -> QuerySet[UserRoleAssignment]:
    return UserRoleAssignment.objects.filter(user=user, revoked_at__isnull=True).select_related("dealership")


def has_role(user: AppUser, dealership_id: UUID, roles: Iterable[str]) -> bool:
    return active_role_assignments(user).filter(dealership_id=dealership_id, role__in=list(roles)).exists()
