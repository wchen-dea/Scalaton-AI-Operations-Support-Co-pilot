"""Append-only audit store (`design §6`, `tech-arch §5`)."""

from .store import AuditEvent, AuditStore

__all__ = ["AuditEvent", "AuditStore"]
