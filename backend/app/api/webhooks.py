"""Provider webhook routes (`tech-arch §4.1`, `§6`; `design §4.1`).

Each webhook authenticates (signature, timestamp, replay, allowlist), enforces the
per-source rate limiter, validates the minimum schema, then acknowledges and processes
the workflow asynchronously so long-running diagnosis never blocks the response.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse

from ..config import Settings
from ..observability.metrics import metrics
from ..orchestration.service import WorkflowService
from ..schemas.events import IncidentEvent
from ..security.ratelimit import RateLimiter
from ..security.signatures import WebhookVerificationError, verify_webhook
from .deps import get_rate_limiter, get_service, get_settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _secret_for(source: str) -> str:
    # Retrieved at runtime from the environment/secrets (`design §6`); never hardcoded.
    return os.environ.get(f"{source.upper()}_WEBHOOK_SECRET", "")


def _header_float(request: Request, name: str) -> float | None:
    raw = request.headers.get(name)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


async def _receive(
    source: str,
    request: Request,
    background: BackgroundTasks,
    settings: Settings,
    service: WorkflowService,
    rate_limiter: RateLimiter,
) -> JSONResponse:
    if source not in settings.webhook_allowed_sources:
        return JSONResponse(status_code=403, content={"detail": f"Source '{source}' not allowed"})

    if not rate_limiter.allow(source):
        metrics.increment("webhook.rate_limited")
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    raw = await request.body()
    try:
        incident = IncidentEvent.model_validate_json(raw)
    except Exception:  # noqa: BLE001 - minimum schema check before acknowledgement
        return JSONResponse(status_code=422, content={"detail": "Invalid incident payload"})

    try:
        verify_webhook(
            source=source,
            event_id=incident.event_id,
            body=raw,
            signature=request.headers.get("x-signature", ""),
            secret=_secret_for(source),
            timestamp=_header_float(request, "x-timestamp"),
            allowed_sources=settings.webhook_allowed_sources,
            max_skew_s=settings.webhook_timestamp_skew_s,
        )
    except WebhookVerificationError as exc:
        service.deps.audit.record_event(
            event_type="webhook.rejected",
            actor=f"webhook:{source}",
            source_id=incident.event_id,
            outcome="rejected",
        )
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    # Authenticated and schema-valid: acknowledge now, process asynchronously.
    background.add_task(service.start_incident, incident)
    return JSONResponse(status_code=202, content={"status": "accepted", "event_id": incident.event_id})


@router.post("/servicenow")
async def servicenow(
    request: Request,
    background: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WorkflowService = Depends(get_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> JSONResponse:
    return await _receive("servicenow", request, background, settings, service, rate_limiter)


@router.post("/jira")
async def jira(
    request: Request,
    background: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WorkflowService = Depends(get_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> JSONResponse:
    return await _receive("jira", request, background, settings, service, rate_limiter)


@router.post("/skybot")
async def skybot(
    request: Request,
    background: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    service: WorkflowService = Depends(get_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> JSONResponse:
    return await _receive("skybot", request, background, settings, service, rate_limiter)
