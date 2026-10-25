"""Who may do what to a dealership's vehicles."""

from uuid import UUID

from accounts.roles import STAFF_ROLES, Role, active_role_assignments, has_role
from dealership.errors import PermissionDenied, ValidationFailed
from dealership.models import AppUser


def require_staff(user: AppUser, dealership_id: UUID) -> None:
    if not has_role(user, dealership_id, STAFF_ROLES):
        raise PermissionDenied("Only staff of this dealership can manage its vehicles.")


def require_admin(user: AppUser, dealership_id: UUID) -> None:
    if not has_role(user, dealership_id, [Role.ADMIN]):
        raise PermissionDenied("Only an admin of this dealership can do this.")


def resolve_staff_dealership(user: AppUser, dealership_id: UUID | None) -> UUID:
    """The dealership a new vehicle belongs to: the one requested, or the user's only one."""
    if dealership_id is not None:
        require_staff(user, dealership_id)
        return dealership_id

    dealership_ids = {
        assignment.dealership_id
        for assignment in active_role_assignments(user).filter(role__in=STAFF_ROLES)
    }
    if not dealership_ids:
        raise PermissionDenied("Only dealership staff can add vehicles.")
    if len(dealership_ids) > 1:
        raise ValidationFailed("You work at several dealerships; choose one.", field="dealership_id")
    return dealership_ids.pop()
