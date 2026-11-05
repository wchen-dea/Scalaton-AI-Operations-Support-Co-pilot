"""Teams action route (`tech-arch §4.1`, `§8`; plan decision D6).

Teams is the authoritative approval surface. This route re-checks the operator role at
the backend (card visibility is not authorization) before performing an action. In a
live deployment the roles come from the authenticated principal, not the request body.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..orchestration.service import WorkflowService
from ..security.rbac import authorize_teams_action
from .deps import get_service

router = APIRouter(prefix="/actions", tags=["actions"])


class TeamsAction(BaseModel):
    action: str
    correlation_id: str
    approver: str = "unknown"
    # Live deployments derive roles from the verified identity, not the client payload.
    roles: list[str] = Field(default_factory=list)


@router.post("/teams")
def teams_action(
    payload: TeamsAction, service: WorkflowService = Depends(get_service)
) -> dict:
    if not authorize_teams_action(payload.action, set(payload.roles)):
        return {"status": "forbidden", "reason": "Role not authorized for this action"}

    if payload.action == "approve_change_request":
        result = service.approve_change_request(payload.correlation_id, payload.approver)
        return {"status": result.status, "servicenow_id": result.servicenow_id, "reason": result.reason}

    if payload.action == "create_jira_bug":
        result = service.submit_jira(payload.correlation_id, payload.approver)
        return {
            "status": result.status,
            "jira_key": result.jira_key,
            "url": result.url,
            "reason": result.reason,
        }

    if payload.action in {"run_data_quality_check", "acknowledge_diagnosis"}:
        return {"status": "accepted", "action": payload.action}

    return {"status": "unsupported", "action": payload.action}
