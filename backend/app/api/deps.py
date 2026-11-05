"""Shared FastAPI dependencies that expose app-scoped singletons to routes."""

from __future__ import annotations

from fastapi import Request

from ..config import Settings
from ..orchestration.service import WorkflowService
from ..security.ratelimit import RateLimiter


def get_service(request: Request) -> WorkflowService:
    return request.app.state.service


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter
