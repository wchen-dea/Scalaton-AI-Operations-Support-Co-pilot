"""Bounded retry with exponential backoff and jitter (`design §7`, `tech-arch §9`)."""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

from ..observability.metrics import metrics

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""


def retry_call(
    func: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay_s: float = 0.2,
    max_delay_s: float = 5.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
    jitter: Callable[[], float] = random.random,
    metric: str = "retry.count",
) -> T:
    """Call ``func`` with bounded retries on safe transient failures.

    Only exceptions in ``retry_on`` are retried; others propagate immediately so a
    non-transient failure is not masked.
    """

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except retry_on as exc:  # noqa: PERF203 - explicit retry loop
            last_exc = exc
            if attempt >= attempts:
                break
            metrics.increment(metric)
            delay = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
            sleep(delay + base_delay_s * jitter())
    raise RetryError(f"Exhausted {attempts} attempts") from last_exc
