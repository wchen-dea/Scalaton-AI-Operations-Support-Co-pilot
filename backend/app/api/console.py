"""Browser-facing (BFF) console routes and the co-pilot SSE stream.

Serves the `/api/*` contract the frontend consumes (plan decision D5). Mutating routes
are a proposal/review surface and are not an authorization authority: they return
`blocked` because authoritative approval flows through Teams (plan decision D6). The SSE
frame shape matches `frontend/src/api/streamClient.ts` (`parseDataPayload`).
"""

from __future__ import annotations

import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..orchestration.service import WorkflowService
from ..schemas.wire import (
    ApprovalResult,
    ChangeRequestDraft,
    CopilotPrompt,
    CopilotSessionResponse,
    IncidentDetail,
    IncidentListResponse,
    JiraDraft,
    JiraSubmitResult,
    SessionMessageView,
)
from ..stubs.fixtures import mock_copilot_reply
from .deps import get_service

router = APIRouter(prefix="/api", tags=["console"])

_TEAMS_ONLY = "Approvals and external writes are performed through Microsoft Teams."


@router.get("/incidents", response_model=IncidentListResponse)
def list_incidents(service: WorkflowService = Depends(get_service)) -> IncidentListResponse:
    return IncidentListResponse(items=[r.to_list_item() for r in service.list_records()])


@router.get("/incidents/{correlation_id}", response_model=IncidentDetail)
def get_incident(correlation_id: str, service: WorkflowService = Depends(get_service)) -> IncidentDetail:
    record = service.get_record(correlation_id)
    if record is None or record.diagnosis is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return record.to_detail()


@router.get("/escalations/{correlation_id}/jira", response_model=JiraDraft)
def get_jira_draft(correlation_id: str, service: WorkflowService = Depends(get_service)) -> JiraDraft:
    draft = service.get_jira_draft(correlation_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Jira draft not found")
    return draft


@router.post("/escalations/{correlation_id}/jira", response_model=JiraSubmitResult)
def submit_jira(correlation_id: str) -> JiraSubmitResult:
    # Browser is not an authorization authority (D6); authoritative action is via Teams.
    return JiraSubmitResult(status="blocked", reason=_TEAMS_ONLY)


@router.get("/change-requests/{correlation_id}", response_model=ChangeRequestDraft)
def get_change_request(
    correlation_id: str, service: WorkflowService = Depends(get_service)
) -> ChangeRequestDraft:
    draft = service.get_change_request(correlation_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Change request not found")
    return draft


@router.post("/change-requests/{correlation_id}/approve", response_model=ApprovalResult)
def approve_change_request(correlation_id: str) -> ApprovalResult:
    # Browser is not an authorization authority (D6); authoritative approval is via Teams.
    return ApprovalResult(status="blocked", reason=_TEAMS_ONLY)


@router.post("/copilot/stream")
def copilot_stream(
    prompt: CopilotPrompt, service: WorkflowService = Depends(get_service)
) -> StreamingResponse:
    # Session memory survives restarts and is backend-governed, never browser storage
    # (ADR-SCALATON-002 §5.2). Content is redacted before it is stored (§8).
    session_id = prompt.session_id or f"sess-{uuid.uuid4().hex[:12]}"
    service.record_session_message(
        session_id=session_id,
        role="user",
        content=prompt.prompt,
        actor_id="operator",
        correlation_id=prompt.correlation_id,
    )
    service.record_session_message(
        session_id=session_id,
        role="assistant",
        content=mock_copilot_reply,
        actor_id="copilot",
        correlation_id=prompt.correlation_id,
    )

    async def event_stream() -> AsyncIterator[str]:
        words = mock_copilot_reply.split(" ")
        for index, word in enumerate(words):
            text = word if index == 0 else f" {word}"
            yield f"data: {json.dumps({'text': text, 'id': str(index)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"x-session-id": session_id},
    )


@router.get("/copilot/sessions/{session_id}", response_model=CopilotSessionResponse)
def get_copilot_session(
    session_id: str, service: WorkflowService = Depends(get_service)
) -> CopilotSessionResponse:
    """Return the redacted conversation memory for a session (`ADR-SCALATON-002 §5.2`)."""

    messages = [SessionMessageView(**m.model_dump()) for m in service.session_history(session_id)]
    return CopilotSessionResponse(session_id=session_id, messages=messages)
