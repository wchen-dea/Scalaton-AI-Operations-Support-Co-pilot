"""Unit tests: redaction and idempotency-key derivation."""

from __future__ import annotations

from app.security.idempotency import derive_idempotency_key
from app.security.redaction import redact


def test_redaction_masks_sensitive_keys():
    data = {"token": "abc", "password": "p", "note": "ok", "nested": {"api_key": "x", "service": "svc"}}
    out = redact(data)
    assert out["token"] == "[REDACTED]"
    assert out["password"] == "[REDACTED]"
    assert out["note"] == "ok"
    assert out["nested"]["api_key"] == "[REDACTED]"
    assert out["nested"]["service"] == "svc"


def test_redaction_is_non_destructive():
    data = {"token": "abc"}
    redact(data)
    assert data["token"] == "abc"  # original untouched


def test_idempotency_key_is_stable_and_distinct():
    a = derive_idempotency_key(
        source_event_id="e1", target_system="jira", target_record="INC1", action_type="create_bug"
    )
    b = derive_idempotency_key(
        source_event_id="e1", target_system="jira", target_record="INC1", action_type="create_bug"
    )
    c = derive_idempotency_key(
        source_event_id="e1", target_system="jira", target_record="INC2", action_type="create_bug"
    )
    assert a == b
    assert a != c
