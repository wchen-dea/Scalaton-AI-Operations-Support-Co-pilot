"""Typed data contracts for the backend.

* `events`: the authoritative `design §5` contracts (Incident event, Diagnosis result).
* `wire`: the browser-facing (BFF) shapes the frontend consumes (plan decision D5).
* `internal`: the orchestrator's working state and typed agent models.
"""

from . import events, internal, wire

__all__ = ["events", "wire", "internal"]
