"""Governed storage plane for the ADR-SCALATON-002 datasets.

Exposes the `Repositories` container and typed row models. The scaffold uses in-memory
repositories; Unity Catalog Delta-backed implementations replace them later (Release 2).
"""

from __future__ import annotations

from .models import (
    BronzeInboundEvent,
    ExternalAction,
    SessionMessage,
    SilverNormalizedEvent,
    WorkflowRun,
)
from .repositories import (
    BronzeEventRepository,
    ExternalActionRepository,
    Repositories,
    SessionMessageRepository,
    SilverEventRepository,
    WorkflowRunRepository,
)

__all__ = [
    "BronzeInboundEvent",
    "SilverNormalizedEvent",
    "WorkflowRun",
    "ExternalAction",
    "SessionMessage",
    "BronzeEventRepository",
    "SilverEventRepository",
    "WorkflowRunRepository",
    "ExternalActionRepository",
    "SessionMessageRepository",
    "Repositories",
]
