"""Health endpoints (`tech-arch §4.1`, `§9`).

`/health/live` reports process liveness; `/health/ready` reports dependency readiness.
Neither exposes credentials or incident content.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict:
    return {"status": "alive"}


@router.get("/health/ready")
def ready() -> dict:
    # Stub adapters are always ready; a live build checks dependency readiness here.
    return {"status": "ready"}
