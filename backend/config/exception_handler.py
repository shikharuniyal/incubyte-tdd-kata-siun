from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from dealership.errors import DomainError


def api_exception_handler(exc, context):
    """Render domain errors like DRF errors: {"detail": ...} or {"<field>": [...]}."""
    if isinstance(exc, DomainError):
        body = {exc.field: [exc.message]} if exc.field else {"detail": exc.message}
        return Response(body, status=exc.status_code)
    return drf_exception_handler(exc, context)
