"""Authoritative `design §5` data contracts.

These models mirror `docs/design-specification.md` §5 verbatim; they are system
contracts, not invented here. Model output is validated against `DiagnosisResult`
before it may leave an agent toward any external system.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

IncidentSource = Literal["skybot", "servicenow", "jira"]


class IncidentEvent(BaseModel):
    """`design §5` — Incident event (inbound)."""

    event_id: str
    source: IncidentSource
    incident_id: str
    severity: str
    service: str
    occurred_at: str
    payload: dict[str, Any] = Field(default_factory=dict)
    signature: str


class ProbableCause(BaseModel):
    """A single probable cause within a diagnosis."""

    description: str
    confidence: float
    evidence: list[str] = Field(default_factory=list)


class DiagnosisResult(BaseModel):
    """`design §5` — Diagnosis result."""

    correlation_id: str
    summary: str
    probable_causes: list[ProbableCause] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    generated_at: str
