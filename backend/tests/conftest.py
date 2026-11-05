"""Shared test fixtures and helpers."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.orchestration.service import WorkflowService
from app.schemas.events import IncidentEvent
from app.security.signatures import compute_signature


def make_settings(**overrides) -> Settings:
    base = dict(
        app_port=8000,
        frontend_dist="/nonexistent-dist",
        enable_external_writes=False,
        use_live_integrations=False,
        model_endpoint="stub-model",
        model_timeout_s=5.0,
        vector_search_index="idx",
        uc_catalog="system",
        uc_schema="workflow",
        sql_warehouse_id="",
        retry_max_attempts=3,
        retry_base_delay_s=0.0,
        request_timeout_s=5.0,
        webhook_rate_limit_per_minute=60,
        teams_channel="ops",
        approval_policy="teams",
        webhook_allowed_sources=("skybot", "servicenow", "jira"),
        webhook_timestamp_skew_s=300,
        genie_space="genie",
        external_mcp_servers=(),
    )
    base.update(overrides)
    return Settings(**base)


def make_incident(**overrides) -> IncidentEvent:
    data = dict(
        event_id="evt-test-1",
        source="skybot",
        incident_id="INC9001",
        severity="high",
        service="test-service",
        occurred_at="2026-11-05T00:00:00Z",
        payload={"error": "boom"},
        signature="sig",
    )
    data.update(overrides)
    return IncidentEvent(**data)


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def service(settings) -> WorkflowService:
    return WorkflowService(settings)


@pytest.fixture
def client(settings) -> TestClient:
    app = create_app(settings)
    return TestClient(app)


def signed_request(client: TestClient, source: str, incident: IncidentEvent, secret: str, monkeypatch):
    monkeypatch.setenv(f"{source.upper()}_WEBHOOK_SECRET", secret)
    body = incident.model_dump_json().encode("utf-8")
    signature = compute_signature(secret, body)
    return client.post(
        f"/webhooks/{source}",
        content=body,
        headers={"x-signature": signature, "content-type": "application/json"},
    )
