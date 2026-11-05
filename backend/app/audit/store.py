"""Append-only audit store.

Records an immutable event for every inbound event, model decision, external write,
approval, and failure (`design §6`). Each event carries event type, actor or service
principal, correlation ID, source ID, timestamp, outcome, payload hash, and external
record ID (`tech-arch §5`). Raw secrets and unnecessary personal data are never stored.
The scaffold uses an in-memory append-only list behind this interface; a governed Delta
table replaces it later (NFR-007).
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def payload_hash(payload: object) -> str:
    """Stable SHA-256 of a payload for tamper-evident auditing (never the raw payload)."""

    data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class AuditEvent(BaseModel):
    event_type: str
    actor: str
    correlation_id: str | None = None
    source_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    outcome: str = "ok"
    payload_hash: str | None = None
    external_record_id: str | None = None


class AuditStore:
    """In-memory append-only audit store."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = threading.Lock()

    def record(self, event: AuditEvent) -> AuditEvent:
        with self._lock:
            self._events.append(event)
        return event

    def record_event(
        self,
        *,
        event_type: str,
        actor: str,
        correlation_id: str | None = None,
        source_id: str | None = None,
        outcome: str = "ok",
        payload: object | None = None,
        external_record_id: str | None = None,
    ) -> AuditEvent:
        return self.record(
            AuditEvent(
                event_type=event_type,
                actor=actor,
                correlation_id=correlation_id,
                source_id=source_id,
                outcome=outcome,
                payload_hash=payload_hash(payload) if payload is not None else None,
                external_record_id=external_record_id,
            )
        )

    def events(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)

    def find(self, *, correlation_id: str | None = None, event_type: str | None = None) -> list[AuditEvent]:
        return [
            e
            for e in self.events()
            if (correlation_id is None or e.correlation_id == correlation_id)
            and (event_type is None or e.event_type == event_type)
        ]
