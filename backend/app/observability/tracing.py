"""Lightweight tracing span hooks (`tech-arch §9`, NFR-004).

A span is a thin context manager that records duration as a metric and logs entry/exit
with the active correlation ID. A live tracing backend replaces this later.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from .logging import get_logger
from .metrics import metrics

_log = get_logger("trace")


@contextmanager
def span(name: str) -> Iterator[None]:
    start = time.perf_counter()
    _log.debug("span start: %s", name)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        metrics.observe(f"span.{name}.seconds", elapsed)
        _log.debug("span end: %s (%.4fs)", name, elapsed)
