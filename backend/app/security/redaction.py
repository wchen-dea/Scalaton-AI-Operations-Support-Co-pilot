"""Redaction of sensitive data before model calls (`design §6`, NFR-002).

Removes tokens, credentials, personal data, and unnecessary payload fields so that
downstream agents and model prompts only ever see minimized, task-relevant context.
"""

from __future__ import annotations

from typing import Any

_SENSITIVE_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "signature",
    "ssn",
    "email",
    "phone",
    "credit_card",
}

_REDACTED = "[REDACTED]"


def _is_sensitive(key: str, extra: set[str]) -> bool:
    lowered = key.lower()
    if lowered in _SENSITIVE_KEYS or lowered in extra:
        return True
    return any(token in lowered for token in ("token", "secret", "password", "api_key"))


def redact(data: Any, extra_keys: set[str] | None = None) -> Any:
    """Return a deep copy of ``data`` with sensitive keys masked."""

    extra = {k.lower() for k in (extra_keys or set())}

    def _walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                k: (_REDACTED if _is_sensitive(k, extra) else _walk(v))
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [_walk(v) for v in value]
        return value

    return _walk(data)
