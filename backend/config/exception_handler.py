from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from dealership.errors import DomainError

CONCURRENT_CONFLICT = "The request conflicts with a concurrent change. Please retry."


def api_exception_handler(exc, context):
    """Render domain errors like DRF errors: {"detail": ...} or {"<field>": [...]}."""
    if isinstance(exc, DomainError):
        body = {exc.field: [exc.message]} if exc.field else {"detail": exc.message}
        return Response(body, status=exc.status_code)
    if isinstance(exc, IntegrityError):
        # A unique/foreign-key constraint caught a race the service could not see
        # (e.g. two requests creating the same VIN). Never leak the SQL message.
        return Response({"detail": CONCURRENT_CONFLICT}, status=status.HTTP_409_CONFLICT)
    return drf_exception_handler(exc, context)
