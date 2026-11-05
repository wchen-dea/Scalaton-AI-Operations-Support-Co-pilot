"""Storage plane and session-memory tests (`ADR-SCALATON-002`).

Covers durable ingestion lineage, duplicate-event idempotency, the external-action
ledger, durable workflow-run status, and redacted co-pilot session memory.
"""

from __future__ import annotations

from app.orchestration.service import WorkflowService
from app.schemas.internal import WorkflowState
from app.security.redaction import redact_text

from .conftest import make_incident, make_settings


def test_start_incident_persists_bronze_silver_and_run(service):
    record = service.start_incident(make_incident(event_id="evt-lineage"))
    repos = service.deps.repos

    bronze = repos.bronze.get("evt-lineage")
    assert bronze is not None and bronze.correlation_id == record.correlation_id
    assert bronze.payload["incident_id"] == record.incident.incident_id

    silver = repos.silver.get("evt-lineage")
    assert silver is not None and silver.incident_id == record.incident.incident_id
    assert silver.correlation_id == record.correlation_id

    run = repos.workflow_runs.get(record.correlation_id)
    assert run is not None
    assert run.status == WorkflowState.AWAITING_HUMAN_REVIEW.value
    assert run.incident_id == record.incident.incident_id


def test_duplicate_event_is_acknowledged_without_second_run(service):
    first = service.start_incident(make_incident(event_id="evt-dup"))
    second = service.start_incident(make_incident(event_id="evt-dup"))

    assert first.correlation_id == second.correlation_id
    # Immutable bronze store holds exactly one record for the event.
    assert len(service.deps.repos.bronze.list()) == 1
    assert service.deps.audit.find(event_type="incident.duplicate")


def test_workflow_run_reaches_completed_after_approval():
    service = WorkflowService(make_settings(enable_external_writes=True))
    record = service.start_incident(make_incident(event_id="evt-complete"))
    service.approve_change_request(record.correlation_id, "lead@example.com")

    run = service.deps.repos.workflow_runs.get(record.correlation_id)
    assert run is not None and run.status == WorkflowState.COMPLETED.value


def test_external_action_ledger_records_servicenow_and_jira():
    service = WorkflowService(make_settings(enable_external_writes=True))
    record = service.start_incident(make_incident(event_id="evt-ledger"))

    service.approve_change_request(record.correlation_id, "lead@example.com")
    service.submit_jira(record.correlation_id, "lead@example.com")

    targets = {a.target_system: a for a in service.deps.repos.external_actions.list()}
    assert "servicenow" in targets and targets["servicenow"].outcome == "submitted"
    assert "jira" in targets and targets["jira"].outcome == "created"
    assert targets["jira"].idempotency_key  # derived, stable key present


def test_copilot_session_stores_redacted_messages(client):
    resp = client.post("/api/copilot/stream", json={"prompt": "my api_key=SECRET42 failed"})
    assert resp.status_code == 200
    session_id = resp.headers["x-session-id"]

    session = client.get(f"/api/copilot/sessions/{session_id}").json()
    roles = [m["role"] for m in session["messages"]]
    assert roles == ["user", "assistant"]
    user_msg = session["messages"][0]
    assert "SECRET42" not in user_msg["content_redacted"]
    assert "[REDACTED]" in user_msg["content_redacted"]
    assert user_msg["retention_until"]


def test_redact_text_masks_secrets_and_preserves_benign():
    assert "hunter2" not in redact_text("password: hunter2")
    assert "[REDACTED]" in redact_text("password: hunter2")
    assert redact_text("pipeline failed with schema drift") == "pipeline failed with schema drift"
