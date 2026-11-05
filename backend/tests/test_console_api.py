"""API tests: BFF console endpoints, SSE stream, health, and webhook behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

from .conftest import make_incident, make_settings, signed_request


def _first_cid(client: TestClient) -> str:
    items = client.get("/api/incidents").json()["items"]
    assert items
    return items[0]["correlation_id"]


def test_health_endpoints(client):
    assert client.get("/health/live").json()["status"] == "alive"
    assert client.get("/health/ready").json()["status"] == "ready"


def test_list_incidents_returns_seeded_items(client):
    items = client.get("/api/incidents").json()["items"]
    assert len(items) == 3
    item = items[0]
    assert set(item) >= {"correlation_id", "incident_id", "source", "severity", "service", "summary", "status"}
    assert item["status"] == "awaiting_human_review"


def test_incident_detail_and_drafts(client):
    cid = _first_cid(client)
    detail = client.get(f"/api/incidents/{cid}").json()
    assert detail["diagnosis"]["correlation_id"] == cid
    assert detail["diagnosis"]["probable_causes"]
    jira = client.get(f"/api/escalations/{cid}/jira").json()
    assert jira["project"] == "DATAENG"
    cr = client.get(f"/api/change-requests/{cid}").json()
    assert cr["proposed_action"]
    assert "rollback_plan" in cr  # §8 approval-control field present


def test_unknown_incident_returns_404(client):
    assert client.get("/api/incidents/does-not-exist").status_code == 404


def test_browser_writes_are_blocked_teams_authoritative(client):
    cid = _first_cid(client)
    jira = client.post(f"/api/escalations/{cid}/jira").json()
    approve = client.post(f"/api/change-requests/{cid}/approve").json()
    assert jira["status"] == "blocked"
    assert approve["status"] == "blocked"
    assert "Teams" in jira["reason"]


def test_copilot_sse_stream_frames(client):
    resp = client.post("/api/copilot/stream", json={"prompt": "what happened?"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert 'data: {"text"' in body
    assert "data: [DONE]" in body


def test_webhook_accepts_signed_request_and_processes(monkeypatch):
    settings = make_settings()
    client = TestClient(create_app(settings))
    before = len(client.get("/api/incidents").json()["items"])
    resp = signed_request(client, "skybot", make_incident(event_id="evt-hook-1"), "secret", monkeypatch)
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"
    after = len(client.get("/api/incidents").json()["items"])
    assert after == before + 1


def test_webhook_rejects_bad_signature(client):
    incident = make_incident(event_id="evt-badsig")
    resp = client.post(
        "/webhooks/skybot",
        content=incident.model_dump_json().encode("utf-8"),
        headers={"x-signature": "deadbeef", "content-type": "application/json"},
    )
    assert resp.status_code == 401


def test_webhook_rejects_invalid_schema(client):
    resp = client.post(
        "/webhooks/skybot",
        content=b'{"not":"an incident"}',
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 422


def test_webhook_rate_limited(monkeypatch):
    settings = make_settings(webhook_rate_limit_per_minute=1)
    client = TestClient(create_app(settings))
    first = signed_request(client, "jira", make_incident(event_id="rl-1"), "secret", monkeypatch)
    second = signed_request(client, "jira", make_incident(event_id="rl-2"), "secret", monkeypatch)
    assert first.status_code == 202
    assert second.status_code == 429
