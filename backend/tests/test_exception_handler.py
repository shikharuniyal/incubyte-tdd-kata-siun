"""Errors raised below the views are turned into consistent JSON responses."""

from django.db import IntegrityError

from config.exception_handler import api_exception_handler
from dealership.errors import Conflict, NotFound, PermissionDenied, ValidationFailed


def render(exc):
    return api_exception_handler(exc, context={})


def test_domain_errors_become_a_detail_message_with_their_status():
    response = render(NotFound("Vehicle not found."))

    assert response.status_code == 404
    assert response.data == {"detail": "Vehicle not found."}


def test_field_errors_are_reported_against_the_field():
    response = render(ValidationFailed("Choose one.", field="dealership_id"))

    assert response.status_code == 400
    assert response.data == {"dealership_id": ["Choose one."]}


def test_permission_and_conflict_statuses():
    assert render(PermissionDenied("no")).status_code == 403
    assert render(Conflict("busy")).status_code == 409


def test_a_database_integrity_error_is_a_409_conflict_not_a_500():
    response = render(IntegrityError("duplicate key value violates unique constraint"))

    assert response.status_code == 409
    assert "conflict" in response.data["detail"].lower()
    assert "duplicate key" not in response.data["detail"]


def test_unknown_errors_are_left_to_django():
    assert render(RuntimeError("boom")) is None
