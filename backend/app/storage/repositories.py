"""In-memory governed storage plane (`ADR-SCALATON-002`).

Composes the ADR-SCALATON-002 datasets behind one `Repositories` container so ingestion,
workflow, and session code persists through a uniform governed-storage port. The scaffold
uses thread-safe in-memory repositories; a Unity Catalog Delta-backed implementation
replaces each repository later behind the same interfaces (Release 2). The existing audit
and dead-letter stores are composed here, not rewritten.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from ..audit.store import AuditStore
from ..reliability.deadletter import DeadLetterStore
from .models import (
    BronzeInboundEvent,
    ExternalAction,
    SessionMessage,
    SilverNormalizedEvent,
    WorkflowRun,
)


class BronzeEventRepository:
    """Append-only, immutable store of raw provider events (`ADR-SCALATON-002 §3`).

    Raw records are never overwritten (`ADR-SCALATON-002 §4` step 4). A governed Delta
    table replaces this store later.
    """

    def __init__(self) -> None:
        self._events: list[BronzeInboundEvent] = []
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def append(self, event: BronzeInboundEvent) -> BronzeInboundEvent:
        with self._lock:
            self._events.append(event)
            self._seen.add(event.event_id)
        return event

    def has_event(self, event_id: str) -> bool:
        with self._lock:
            return event_id in self._seen

    def list(self) -> list[BronzeInboundEvent]:
        with self._lock:
            return list(self._events)

    def get(self, event_id: str) -> BronzeInboundEvent | None:
        with self._lock:
            return next((e for e in self._events if e.event_id == event_id), None)


class SilverEventRepository:
    """Canonical normalized events keyed by event ID (`ADR-SCALATON-002 §3`)."""

    def __init__(self) -> None:
        self._events: dict[str, SilverNormalizedEvent] = {}
        self._lock = threading.Lock()

    def upsert(self, event: SilverNormalizedEvent) -> SilverNormalizedEvent:
        with self._lock:
            self._events[event.event_id] = event
        return event

    def get(self, event_id: str) -> SilverNormalizedEvent | None:
        with self._lock:
            return self._events.get(event_id)

    def list(self) -> list[SilverNormalizedEvent]:
        with self._lock:
            return list(self._events.values())


class WorkflowRunRepository:
    """Durable workflow runs keyed by correlation ID (`ADR-SCALATON-002 §3`, `§5.1`).

    This is the authoritative workflow record; the service's in-memory record map is a
    non-authoritative cache (`ADR-SCALATON-002 §9`).
    """

    def __init__(self) -> None:
        self._runs: dict[str, WorkflowRun] = {}
        self._lock = threading.Lock()

    def upsert(self, run: WorkflowRun) -> WorkflowRun:
        with self._lock:
            existing = self._runs.get(run.correlation_id)
            if existing is not None:
                run.created_at = existing.created_at
            self._runs[run.correlation_id] = run
        return run

    def get(self, correlation_id: str) -> WorkflowRun | None:
        with self._lock:
            return self._runs.get(correlation_id)

    def list(self) -> list[WorkflowRun]:
        with self._lock:
            return list(self._runs.values())


class ExternalActionRepository:
    """Idempotency-keyed external-write ledger (`ADR-SCALATON-002 §3`)."""

    def __init__(self) -> None:
        self._actions: dict[str, ExternalAction] = {}
        self._lock = threading.Lock()

    def record(self, action: ExternalAction) -> ExternalAction:
        with self._lock:
            self._actions.setdefault(action.idempotency_key, action)
            return self._actions[action.idempotency_key]

    def get(self, idempotency_key: str) -> ExternalAction | None:
        with self._lock:
            return self._actions.get(idempotency_key)

    def list(self) -> list[ExternalAction]:
        with self._lock:
            return list(self._actions.values())


class SessionMessageRepository:
    """Redacted conversation memory keyed by session (`ADR-SCALATON-002 §5.2`).

    Content is redacted by the caller before it is stored (`ADR-SCALATON-002 §8`).
    """

    def __init__(self) -> None:
        self._messages: dict[str, list[SessionMessage]] = {}
        self._lock = threading.Lock()

    def append(self, message: SessionMessage) -> SessionMessage:
        with self._lock:
            self._messages.setdefault(message.session_id, []).append(message)
        return message

    def history(self, session_id: str) -> list[SessionMessage]:
        with self._lock:
            return list(self._messages.get(session_id, []))


@dataclass
class Repositories:
    """The governed storage plane (`ADR-SCALATON-002 §3`, `§5`).

    One container for every ADR-SCALATON-002 dataset. The audit and dead-letter stores
    are composed in so `Deps.audit` / `Deps.dead_letter` and these repositories share the
    same instances.
    """

    audit: AuditStore
    dead_letter: DeadLetterStore
    bronze: BronzeEventRepository = field(default_factory=BronzeEventRepository)
    silver: SilverEventRepository = field(default_factory=SilverEventRepository)
    workflow_runs: WorkflowRunRepository = field(default_factory=WorkflowRunRepository)
    external_actions: ExternalActionRepository = field(default_factory=ExternalActionRepository)
    session_messages: SessionMessageRepository = field(default_factory=SessionMessageRepository)

    @classmethod
    def build(cls) -> "Repositories":
        return cls(audit=AuditStore(), dead_letter=DeadLetterStore())
