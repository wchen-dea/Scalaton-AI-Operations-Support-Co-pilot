"""Per-source inbound rate limiting (`tech-arch §3`, `§6`; FR-016).

A sliding-window limiter rejects excess webhook requests at the edge boundary. The
scaffold uses an in-memory limiter behind this interface; a distributed limiter
replaces it for multi-replica deployments.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, per_minute: int, window_s: float = 60.0) -> None:
        self.per_minute = per_minute
        self.window_s = window_s
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, source: str, now: float | None = None) -> bool:
        """Return True if a request from ``source`` is within the limit, else False."""

        current = now if now is not None else time.monotonic()
        with self._lock:
            bucket = self._events[source]
            cutoff = current - self.window_s
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.per_minute:
                return False
            bucket.append(current)
            return True
