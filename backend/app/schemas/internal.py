"""Internal typed models: the orchestrator's working state and agent messages.

These are distinct from the browser wire shapes. The internal `WorkflowState` enum
(nine `tech-arch §4.2` states) is deliberately separate from the five-value BFF
`IncidentStatus`; `status_for_state` maps between them (critique PC-004). Agents
communicate through these typed models, never free-form strings (`tech-arch §4.3`).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .events import DiagnosisResult, IncidentEvent
from .wire import (
    ChangeRequestDraft,
    IncidentDetail,
    IncidentListItem,
    IncidentStatus,
    JiraDraft,
)


class WorkflowState(str, Enum):
    """Canonical six-phase workflow states plus terminal states."""

    RECEIVED = "received"
    VALIDATING = "validating"
    COLLECTING_EVIDENCE = "collecting_evidence"
    DIAGNOSING = "diagnosing"
    DRAFTING = "drafting"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"
    HOT_FIX = "hot_fix"
    RECORDING_OPERATIONS = "recording_operations"
    CHANGE_REQUEST_AUTOMATION = "change_request_automation"
    EXECUTING_APPROVED_ACTION = "executing_approved_action"
    COMPLETED = "completed"
    FAILED = "failed"


# Active (pre-approval) states the console reports as "awaiting_human_review".
_ACTIVE_STATES = {
    WorkflowState.RECEIVED,
    WorkflowState.VALIDATING,
    WorkflowState.COLLECTING_EVIDENCE,
    WorkflowState.DIAGNOSING,
    WorkflowState.DRAFTING,
    WorkflowState.AWAITING_HUMAN_REVIEW,
}


def status_for_state(
    state: WorkflowState, resolved_with_recommendation: bool = False
) -> IncidentStatus:
    """Map an internal `WorkflowState` to the five-value BFF `IncidentStatus`.

    The internal state set is broader than the browser contract, so active states
    collapse to ``awaiting_human_review`` and a recommendation-only completion maps
    to ``resolved_with_recommendation`` (critique PC-004).
    """

    if state in _ACTIVE_STATES:
        return "awaiting_human_review"
    if state is WorkflowState.EXECUTING_APPROVED_ACTION:
        return "executing_approved_action"
    if state is WorkflowState.FAILED:
        return "failed"
    # COMPLETED
    return "resolved_with_recommendation" if resolved_with_recommendation else "completed"


class EvidenceBundle(BaseModel):
    """Typed evidence collected by the read-only agents."""

    log_diagnostics: list[str] = Field(default_factory=list)
    runbook_references: list[str] = Field(default_factory=list)
    historical_incidents: list[str] = Field(default_factory=list)
    research_notes: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)


class ApprovalRecord(BaseModel):
    """Audited approval of a production-impacting action (`design §8`)."""

    approver: str
    payload_hash: str
    approved_at: str
    external_record_id: str | None = None


class WorkflowRecord(BaseModel):
    """The stored working record for one incident workflow.

    Threads the correlation ID through evidence, diagnosis, drafts, and approval, and
    projects into the browser contract via `to_list_item` / `to_detail`.
    """

    correlation_id: str
    incident: IncidentEvent
    state: WorkflowState = WorkflowState.RECEIVED
    sanitized_context: dict = Field(default_factory=dict)
    evidence: EvidenceBundle = Field(default_factory=EvidenceBundle)
    diagnosis: DiagnosisResult | None = None
    jira_draft: JiraDraft | None = None
    change_request: ChangeRequestDraft | None = None
    approval: ApprovalRecord | None = None
    connector_results: dict = Field(default_factory=dict)
    resolved_with_recommendation: bool = False
    error: str | None = None

    def to_list_item(self) -> IncidentListItem:
        summary = self.diagnosis.summary if self.diagnosis else "Diagnosis pending"
        return IncidentListItem(
            correlation_id=self.correlation_id,
            incident_id=self.incident.incident_id,
            source=self.incident.source,
            severity=self.incident.severity,
            service=self.incident.service,
            summary=summary,
            status=status_for_state(self.state, self.resolved_with_recommendation),
        )

    def to_detail(self) -> IncidentDetail:
        if self.diagnosis is None:
            raise ValueError("Diagnosis not yet available for this incident")
        base = self.to_list_item()
        return IncidentDetail(**base.model_dump(), diagnosis=self.diagnosis)
