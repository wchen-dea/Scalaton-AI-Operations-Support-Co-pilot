"""Minimal in-memory metrics registry (`tech-arch §9`).

The scaffold records the metric names the specifications call out (latency, workflow
duration, model latency, token usage, retry count, connector failures, rate-limit
rejections) as counters/observations. A live telemetry backend replaces this later.
"""

from __future__ import annotations

import threading
from collections import defaultdict


class Metrics:
    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._observations: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def increment(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self._observations[name].append(value)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "observations": {k: list(v) for k, v in self._observations.items()},
            }


# Process-wide default registry.
metrics = Metrics()
