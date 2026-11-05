"""Browser-facing (BFF) wire shapes.

These match `frontend/src/types/wire.ts` and the calls in
`frontend/src/api/apiClient.ts` exactly (snake_case field names) so the contract is
drop-in for the frontend. They are net-new relative to the specs (plan decision D5),
pending backend-owner confirmation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .events import DiagnosisResult, IncidentSource

# Only these five values are valid on the browser contract (frontend `IncidentStatus`).
IncidentStatus = Literal[
    "awaiting_human_review",
    "resolved_with_recommendation",
    "executing_approved_action",
    "completed",
    "failed",
]


class IncidentListItem(BaseModel):
    correlation_id: str
    incident_id: str
    source: IncidentSource
    severity: str
    service: str
    summary: str
    status: IncidentStatus


class IncidentDetail(IncidentListItem):
    diagnosis: DiagnosisResult


class IncidentListResponse(BaseModel):
    items: list[IncidentListItem] = Field(default_factory=list)


class JiraDraft(BaseModel):
    """Proposed Jira issue fields mapped from incident context (`design §4.3.2`)."""

    correlation_id: str
    project: str
    issue_type: str
    summary: str
    description: str
    severity: str
    incident_link: str


class ChangeRequestDraft(BaseModel):
    """Drafted change request: `§4.4.3` contents plus the `§8` approval-control fields."""

    correlation_id: str
    proposed_action: str
    code_change_summary: str
    risk_assessment: str
    test_evidence: list[str] = Field(default_factory=list)
    rollback_plan: str
    affected_records: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    linked_records: list[str] = Field(default_factory=list)


class JiraSubmitResult(BaseModel):
    status: Literal["created", "blocked"]
    jira_key: str | None = None
    url: str | None = None
    reason: str | None = None


class ApprovalResult(BaseModel):
    status: Literal["submitted", "blocked"]
    servicenow_id: str | None = None
    reason: str | None = None


class OperationHandle(BaseModel):
    task_id: str


class OperationStatus(BaseModel):
    task_id: str
    status: Literal["running", "done", "error"]
    result: Any | None = None
    error: str | None = None


class CopilotPrompt(BaseModel):
    prompt: str
    session_id: str | None = None
    correlation_id: str | None = None


class SessionMessageView(BaseModel):
    session_id: str
    correlation_id: str | None = None
    actor_id: str
    role: str
    content_redacted: str
    created_at: str
    retention_until: str | None = None


class CopilotSessionResponse(BaseModel):
    session_id: str
    messages: list[SessionMessageView]
