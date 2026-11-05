"""Redaction of sensitive data before model calls (`design §6`, NFR-002).

Removes tokens, credentials, personal data, and unnecessary payload fields so that
downstream agents and model prompts only ever see minimized, task-relevant context.
"""

from __future__ import annotations

import re
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


# Free-text redaction for conversation content (`ADR-SCALATON-002 §8`). Masks the common
# shapes of secrets, credentials, and personal data before a message is stored in
# `session_messages` or sent to a model. Conservative by design: it targets recognizable
# secret shapes rather than attempting full PII detection.
_TEXT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # key: value / key=value where the key names a sensitive field
    re.compile(
        r"(?i)\b(password|passwd|secret|token|access[_-]?token|refresh[_-]?token|api[_-]?key|"
        r"apikey|authorization|auth|credential|client[_-]?secret|signature|ssn)\b"
        r"\s*[:=]\s*\S+"
    ),
    # Bearer / Basic authorization headers
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    # Common provider key prefixes (OpenAI-style, AWS access key id)
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{12,}\b"),
    # Email addresses
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)

_REDACTED_TEXT = "[REDACTED]"


def redact_text(text: str) -> str:
    """Return ``text`` with recognizable secrets, credentials, and emails masked.

    Used before conversation content is persisted to session memory or sent to a model
    (`ADR-SCALATON-002 §8`, NFR-002).
    """

    if not text:
        return text

    redacted = text
    for pattern in _TEXT_PATTERNS:
        redacted = pattern.sub(_mask_match, redacted)
    return redacted


def _mask_match(match: re.Match[str]) -> str:
    """Mask a matched secret while keeping a sensitive key or auth scheme visible."""

    groups = match.groups()
    if groups and groups[0] is not None:
        return f"{groups[0]}: {_REDACTED_TEXT}"
    return _REDACTED_TEXT
