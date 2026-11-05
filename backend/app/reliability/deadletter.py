"""Dead-letter persistence for permanently failed events (`design §7`, `tech-arch §9`).

The scaffold uses an in-memory store behind this interface; a governed Delta table
replaces it later (NFR-007).
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DeadLetterEntry(BaseModel):
    event_id: str
    source: str
    correlation_id: str | None = None
    reason: str
    payload: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    replayed: bool = False


class DeadLetterStore:
    def __init__(self) -> None:
        self._entries: dict[str, DeadLetterEntry] = {}
        self._lock = threading.Lock()

    def add(self, entry: DeadLetterEntry) -> DeadLetterEntry:
        with self._lock:
            self._entries[entry.event_id] = entry
        return entry

    def get(self, event_id: str) -> DeadLetterEntry | None:
        with self._lock:
            return self._entries.get(event_id)

    def list(self, *, include_replayed: bool = False) -> list[DeadLetterEntry]:
        with self._lock:
            return [
                e for e in self._entries.values() if include_replayed or not e.replayed
            ]

    def mark_replayed(self, event_id: str) -> None:
        with self._lock:
            entry = self._entries.get(event_id)
            if entry is not None:
                entry.replayed = True
