"""
Business-rule failures raised by the service layer.

Services know nothing about HTTP; config.exception_handler maps these
errors to response status codes in one place.
"""


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str, *, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


class ValidationFailed(DomainError):
    status_code = 400


class PermissionDenied(DomainError):
    status_code = 403


class NotFound(DomainError):
    status_code = 404


class Conflict(DomainError):
    status_code = 409


class OutOfStock(Conflict):
    pass
