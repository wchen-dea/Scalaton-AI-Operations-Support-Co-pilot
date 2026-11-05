"""Authorized, audited, idempotent dead-letter replay (`design §7`; FR-017).

Replay is available only through this operational interface (not a public route). It
checks authorization, prevents duplicate replay using the idempotency key, and records
an audit event for every attempt.
"""

from __future__ import annotations

from typing import Callable

from ..audit.store import AuditStore
from ..security.idempotency import derive_idempotency_key
from .deadletter import DeadLetterEntry, DeadLetterStore


class ReplayAuthorizationError(Exception):
    """Raised when a replay request is not authorized."""


class ReplayService:
    def __init__(
        self,
        *,
        dead_letter: DeadLetterStore,
        audit: AuditStore,
        authorizer: Callable[[str], bool],
        handler: Callable[[DeadLetterEntry], None],
    ) -> None:
        self._dead_letter = dead_letter
        self._audit = audit
        self._authorizer = authorizer
        self._handler = handler
        self._replayed_keys: set[str] = set()

    def replay(self, event_id: str, actor: str) -> bool:
        """Replay one dead-lettered event. Returns True when it is handled.

        Raises `ReplayAuthorizationError` for an unauthorized actor; is idempotent for
        a repeated replay of the same event; and audits every attempt.
        """

        if not self._authorizer(actor):
            self._audit.record_event(
                event_type="deadletter.replay.denied", actor=actor, source_id=event_id, outcome="denied"
            )
            raise ReplayAuthorizationError(f"Actor '{actor}' may not replay events")

        entry = self._dead_letter.get(event_id)
        if entry is None:
            self._audit.record_event(
                event_type="deadletter.replay.missing", actor=actor, source_id=event_id, outcome="missing"
            )
            return False

        key = derive_idempotency_key(
            source_event_id=entry.event_id,
            target_system="workflow",
            target_record=entry.correlation_id or entry.event_id,
            action_type="replay",
        )
        if key in self._replayed_keys or entry.replayed:
            self._audit.record_event(
                event_type="deadletter.replay.duplicate",
                actor=actor,
                correlation_id=entry.correlation_id,
                source_id=event_id,
                outcome="duplicate",
            )
            return False

        self._handler(entry)
        self._replayed_keys.add(key)
        self._dead_letter.mark_replayed(event_id)
        self._audit.record_event(
            event_type="deadletter.replay.ok",
            actor=actor,
            correlation_id=entry.correlation_id,
            source_id=event_id,
            outcome="ok",
        )
        return True
