"""Request-scoped logging context: every log record carries the current request ID."""

import logging
from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_installed = False


def current_request_id() -> str | None:
    return _request_id.get()


def set_request_id(request_id: str | None) -> None:
    _request_id.set(request_id)


def install_request_id_logging() -> None:
    """Add `request_id` to every LogRecord (works for any handler, including test capture)."""
    global _installed
    if _installed:
        return
    base_factory = logging.getLogRecordFactory()

    def factory(*args: object, **kwargs: object) -> logging.LogRecord:
        record = base_factory(*args, **kwargs)  # pyright: ignore[reportArgumentType]
        record.request_id = _request_id.get()
        return record

    logging.setLogRecordFactory(factory)
    _installed = True
