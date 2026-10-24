"""Application errors and the error envelope (docs/project/API_AND_CODE_CONVENTIONS.md §1.2).

Services raise AppError subclasses; handlers registered in create_app() turn them into
{"error": {code, message, details, request_id}}. Codes are listed in §1.3 of the conventions.
"""

from collections.abc import Mapping, Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import current_request_id


class AppError(Exception):
    status: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Something went wrong"
    headers: Mapping[str, str] | None = None
    details: Sequence[Mapping[str, str]] = ()


class NotAuthenticatedError(AppError):
    status = 401
    code = "AUTH_NOT_AUTHENTICATED"
    message = "Not authenticated"
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidCredentialsError(AppError):
    status = 401
    code = "AUTH_INVALID_CREDENTIALS"
    message = "Invalid username or password"
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(AppError):
    status = 403
    code = "AUTH_FORBIDDEN"
    message = "Forbidden"


class NotFoundError(AppError):
    """Base for "<thing> not found" errors; subclasses set only `code` and `message`."""

    status = 404


def error_response(
    status: int,
    code: str,
    message: str,
    *,
    details: Sequence[Mapping[str, str]] = (),
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = {
        "error": {
            "code": code,
            "message": message,
            "details": [dict(d) for d in details],
            "request_id": current_request_id(),
        }
    }
    return JSONResponse(status_code=status, content=body, headers=dict(headers or {}))


_HTTP_CODES = {404: ("NOT_FOUND", "Not found"), 405: ("METHOD_NOT_ALLOWED", "Method not allowed")}


async def _app_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)  # noqa: S101  (registered for AppError only)
    return error_response(
        exc.status, exc.code, exc.message, details=exc.details, headers=exc.headers
    )


async def _validation_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101
    # Location and message only: the submitted value may be a password or other secret.
    details = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": str(err["msg"])}
        for err in exc.errors()
    ]
    return error_response(422, "VALIDATION_FAILED", "Request validation failed", details=details)


async def _http_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101
    code, message = _HTTP_CODES.get(exc.status_code, ("HTTP_ERROR", "Request failed"))
    return error_response(exc.status_code, code, message, headers=exc.headers)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
