"""Typed row models for the governed storage plane (`ADR-SCALATON-002 §3`, `§5`).

Each model mirrors the required fields of an ADR-SCALATON-002 dataset. Rows are kept
JSON-native so the later Unity Catalog Delta writer is mechanical. The scaffold persists
these through in-memory repositories; a governed Delta table replaces each one later.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class BronzeInboundEvent(BaseModel):
    """`ADR-SCALATON-002 §3` — immutable provider payload and receipt metadata."""

    event_id: str
    source: str
    correlation_id: str | None = None
    signature_result: str = "unverified"
    received_at: str = Field(default_factory=_utcnow)
    payload: dict = Field(default_factory=dict)


class SilverNormalizedEvent(BaseModel):
    """`ADR-SCALATON-002 §3` — canonical event schema independent of provider format."""

    event_id: str
    source: str
    correlation_id: str
    incident_id: str
    severity: str
    service: str
    occurred_at: str
    normalized_at: str = Field(default_factory=_utcnow)


class WorkflowRun(BaseModel):
    """`ADR-SCALATON-002 §3` — current workflow status, references, and timestamps."""

    correlation_id: str
    incident_id: str
    source: str
    severity: str
    service: str
    status: str
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)
    error: str | None = None


class ExternalAction(BaseModel):
    """`ADR-SCALATON-002 §3` — idempotency-keyed external write ledger entry."""

    idempotency_key: str
    correlation_id: str | None = None
    target_system: str
    action_type: str
    request_hash: str
    outcome: str
    external_record_id: str | None = None
    created_at: str = Field(default_factory=_utcnow)


class SessionMessage(BaseModel):
    """`ADR-SCALATON-002 §5.2` — redacted conversation-memory message.

    Content is redacted before it reaches this model; raw secrets and credentials are
    never stored (`ADR-SCALATON-002 §8`).
    """

    session_id: str
    correlation_id: str | None = None
    actor_id: str
    role: str
    content_redacted: str
    created_at: str = Field(default_factory=_utcnow)
    retention_until: str | None = None
