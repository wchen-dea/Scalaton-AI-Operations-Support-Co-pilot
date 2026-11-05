"""Connector base implementing the `tech-arch §6` adapter contract.

Every external system has an adapter that: validates request/response schemas, attaches
correlation and idempotency headers, applies bounded retries only to safe transient
failures, normalizes provider errors into internal categories, and emits an audit event
for every external read and write. Destructive/production-changing writes are gated by
the external-write feature flag (off by default; `design §4.2.4`, NFR-007).
"""

from __future__ import annotations

from ..audit.store import AuditStore
from ..config import Settings
from ..observability.metrics import metrics
from ..security.idempotency import derive_idempotency_key


class ConnectorError(Exception):
    """A normalized connector error with an internal category."""

    def __init__(self, category: str, message: str) -> None:
        super().__init__(f"[{category}] {message}")
        self.category = category


class ConnectorResult:
    def __init__(self, *, ok: bool, external_id: str | None = None, data: dict | None = None,
                 blocked_reason: str | None = None) -> None:
        self.ok = ok
        self.external_id = external_id
        self.data = data or {}
        self.blocked_reason = blocked_reason


class Connector:
    """Base connector enforcing the §6 contract for one external system."""

    system = "generic"

    def __init__(self, settings: Settings, audit: AuditStore) -> None:
        self._settings = settings
        self._audit = audit

    # --- read path ---------------------------------------------------------
    def read(self, *, correlation_id: str, operation: str, **params: object) -> ConnectorResult:
        self._audit.record_event(
            event_type=f"{self.system}.read",
            actor=f"connector:{self.system}",
            correlation_id=correlation_id,
            payload={"operation": operation, **params},
        )
        return self._do_read(correlation_id=correlation_id, operation=operation, **params)

    # --- write path (idempotent, gated, audited) ---------------------------
    def write(
        self,
        *,
        correlation_id: str,
        source_event_id: str,
        target_record: str,
        action_type: str,
        **params: object,
    ) -> ConnectorResult:
        if not self._settings.enable_external_writes:
            self._audit.record_event(
                event_type=f"{self.system}.write.blocked",
                actor=f"connector:{self.system}",
                correlation_id=correlation_id,
                outcome="blocked",
            )
            return ConnectorResult(
                ok=False, blocked_reason="External writes are disabled in this environment."
            )

        key = derive_idempotency_key(
            source_event_id=source_event_id,
            target_system=self.system,
            target_record=target_record,
            action_type=action_type,
        )
        # Idempotency: a prior successful write for this key is not repeated.
        existing = [
            e
            for e in self._audit.find(correlation_id=correlation_id)
            if e.event_type == f"{self.system}.write.ok" and e.external_record_id
        ]
        if existing:
            return ConnectorResult(ok=True, external_id=existing[0].external_record_id)

        result = self._do_write(
            correlation_id=correlation_id, action_type=action_type, idempotency_key=key, **params
        )
        metrics.increment(f"connector.{self.system}.write")
        self._audit.record_event(
            event_type=f"{self.system}.write.ok",
            actor=f"connector:{self.system}",
            correlation_id=correlation_id,
            source_id=source_event_id,
            external_record_id=result.external_id,
            payload={"action_type": action_type},
        )
        return result

    # --- provider-specific hooks (overridden by stubs/live impls) ----------
    def _do_read(self, *, correlation_id: str, operation: str, **params: object) -> ConnectorResult:
        raise NotImplementedError

    def _do_write(self, *, correlation_id: str, action_type: str, idempotency_key: str,
                  **params: object) -> ConnectorResult:
        raise NotImplementedError
