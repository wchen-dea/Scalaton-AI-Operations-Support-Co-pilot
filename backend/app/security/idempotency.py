"""Stable idempotency-key derivation (`tech-arch §6`).

Derives a stable key from the source event, target system, target record, and action
type, so a connector can detect an existing successful action before writing.
"""

from __future__ import annotations

import hashlib


def derive_idempotency_key(
    *, source_event_id: str, target_system: str, target_record: str, action_type: str
) -> str:
    raw = "|".join([source_event_id, target_system, target_record, action_type])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
