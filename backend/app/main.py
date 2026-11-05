"""FastAPI application factory.

Wires configuration, the workflow service (with its seeded stub data), the route groups
(health, webhooks, Teams actions, and the BFF console), and same-origin static serving
of the built frontend. Binds `DATABRICKS_APP_PORT` at runtime (`__main__` below).
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import actions, console, health, webhooks
from .config import Settings, get_settings
from .observability.logging import configure_logging, get_logger
from .orchestration.service import WorkflowService
from .security.ratelimit import RateLimiter
from .stubs.fixtures import seed_records

_log = get_logger("main")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    app = FastAPI(
        title="Agentic AI Operations Support System",
        version="0.1.0",
        description="FastAPI + LangGraph backend (scaffold).",
    )

    service = WorkflowService(settings)
    seed_records(service)

    app.state.settings = settings
    app.state.service = service
    app.state.rate_limiter = RateLimiter(settings.webhook_rate_limit_per_minute)

    app.include_router(health.router)
    app.include_router(webhooks.router)
    app.include_router(actions.router)
    app.include_router(console.router)

    _mount_frontend(app, settings)
    _log.info("Application initialized (external_writes=%s)", settings.enable_external_writes)
    return app


def _mount_frontend(app: FastAPI, settings: Settings) -> None:
    dist = Path(settings.frontend_dist)
    if dist.is_dir():
        # Served same-origin so the SPA and /api/* share an origin (no loosened CORS).
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")
        _log.info("Serving frontend assets from %s", dist)
    else:
        _log.warning("Frontend dist not found at %s; API runs without static assets", dist)


app = create_app()


if __name__ == "__main__":  # pragma: no cover - local run convenience
    import uvicorn

    port = int(os.environ.get("DATABRICKS_APP_PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
