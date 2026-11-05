"""Structured, correlation-ID-aware logging (`tech-arch §9`, NFR-004).

A context variable carries the active correlation ID so every log line emitted during
a workflow is attributable to it without threading the ID through every call.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

_CONFIGURED = False


class _CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id.get() or "-"
        return True


def configure_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] [cid=%(correlation_id)s] %(message)s"
        )
    )
    handler.addFilter(_CorrelationFilter())
    root = logging.getLogger("app")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")


def set_correlation_id(correlation_id: str | None) -> None:
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str | None:
    return _correlation_id.get()
