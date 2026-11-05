"""Unit tests: webhook signature verification, replay, freshness, allowlist (`design §6`)."""

from __future__ import annotations

import time

import pytest

from app.security.signatures import (
    WebhookVerificationError,
    _ReplayGuard,
    compute_signature,
    verify_webhook,
)

ALLOWED = ("skybot", "servicenow", "jira")
SECRET = "test-secret"
BODY = b'{"event_id":"e1"}'


def _verify(**overrides):
    params = dict(
        source="skybot",
        event_id="e1",
        body=BODY,
        signature=compute_signature(SECRET, BODY),
        secret=SECRET,
        timestamp=None,
        allowed_sources=ALLOWED,
        max_skew_s=300,
        replay_guard=_ReplayGuard(),
    )
    params.update(overrides)
    verify_webhook(**params)


def test_valid_signature_passes():
    _verify()  # no exception


def test_bad_signature_rejected():
    with pytest.raises(WebhookVerificationError):
        _verify(signature="deadbeef")


def test_disallowed_source_rejected():
    with pytest.raises(WebhookVerificationError):
        _verify(source="pagerduty")


def test_missing_secret_rejected():
    with pytest.raises(WebhookVerificationError):
        _verify(secret="")


def test_stale_timestamp_rejected():
    with pytest.raises(WebhookVerificationError):
        _verify(timestamp=time.time() - 10_000, max_skew_s=300)


def test_replay_rejected():
    guard = _ReplayGuard()
    _verify(replay_guard=guard)
    with pytest.raises(WebhookVerificationError):
        _verify(replay_guard=guard)  # same event_id again
