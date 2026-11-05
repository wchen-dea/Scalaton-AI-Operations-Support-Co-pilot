"""Browser-facing (BFF) console routes and the co-pilot SSE stream.

Serves the `/api/*` contract the frontend consumes (plan decision D5). Mutating routes
are a proposal/review surface and are not an authorization authority: they return
`blocked` because authoritative approval flows through Teams (plan decision D6). The SSE
frame shape matches `frontend/src/api/streamClient.ts` (`parseDataPayload`).
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..orchestration.service import WorkflowService
from ..schemas.wire import (
    ApprovalResult,
    ChangeRequestDraft,
    CopilotPrompt,
    IncidentDetail,
    IncidentListResponse,
    JiraDraft,
    JiraSubmitResult,
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
def copilot_stream(prompt: CopilotPrompt) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        words = mock_copilot_reply.split(" ")
        for index, word in enumerate(words):
            text = word if index == 0 else f" {word}"
            yield f"data: {json.dumps({'text': text, 'id': str(index)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
