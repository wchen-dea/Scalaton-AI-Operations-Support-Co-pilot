"""Inbound webhook verification (`design §6`, `tech-arch §6`).

Performs HMAC-SHA256 signature validation, timestamp-freshness checks, replay
protection, and source allowlisting. A webhook is acknowledged only after authenticity
and minimum checks pass. Signing keys come from configuration/secrets, never hardcoded.
"""

from __future__ import annotations

import hashlib
import hmac
import threading
import time


class WebhookVerificationError(Exception):
    """Raised when an inbound webhook fails authenticity or freshness checks."""


def compute_signature(secret: str, body: bytes) -> str:
    """Compute the expected HMAC-SHA256 hex signature for a raw request body."""

    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


class _ReplayGuard:
    """Remembers recently seen event IDs to reject replays."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def seen(self, event_id: str) -> bool:
        with self._lock:
            if event_id in self._seen:
                return True
            self._seen.add(event_id)
            return False


_replay_guard = _ReplayGuard()


def verify_webhook(
    *,
    source: str,
    event_id: str,
    body: bytes,
    signature: str,
    secret: str,
    timestamp: float | None = None,
    allowed_sources: tuple[str, ...],
    max_skew_s: int = 300,
    now: float | None = None,
    replay_guard: _ReplayGuard | None = None,
) -> None:
    """Validate an inbound webhook; raise `WebhookVerificationError` on any failure."""

    guard = replay_guard or _replay_guard
    current = now if now is not None else time.time()

    if source not in allowed_sources:
        raise WebhookVerificationError(f"Source '{source}' is not allow-listed")

    if not secret:
        raise WebhookVerificationError("No signing secret configured for verification")

    expected = compute_signature(secret, body)
    if not hmac.compare_digest(expected, signature):
        raise WebhookVerificationError("Signature mismatch")

    if timestamp is not None and abs(current - timestamp) > max_skew_s:
        raise WebhookVerificationError("Timestamp outside the allowed freshness window")

    if guard.seen(event_id):
        raise WebhookVerificationError(f"Replay detected for event '{event_id}'")
