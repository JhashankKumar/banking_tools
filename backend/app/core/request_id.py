import logging
import re
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.errors import error_response
from app.core.logging import set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")
logger = logging.getLogger(__name__)


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach a correlation ID to each request and turn unexpected errors into a generic 500.

    The client's X-Request-ID is reused only if well-formed.
    """
    supplied = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = supplied if _VALID_REQUEST_ID.match(supplied) else str(uuid.uuid4())
    request.state.request_id = request_id
    set_request_id(request_id)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
        response = error_response(500, "INTERNAL_ERROR", "Something went wrong")
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
