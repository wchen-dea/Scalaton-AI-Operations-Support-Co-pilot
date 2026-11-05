"""Workflow tests: state transitions, approval boundary, retries, idempotency, failure paths."""

from __future__ import annotations

from app.orchestration.service import WorkflowService
from app.reliability.retry import RetryError, retry_call
from app.schemas.internal import WorkflowState

from .conftest import make_incident, make_settings


def _write_oks(service: WorkflowService) -> list[str]:
    return [e.event_type for e in service.deps.audit.events() if e.event_type.endswith("write.ok")]


def test_workflow_pauses_at_approval_boundary(service):
    record = service.start_incident(make_incident())
    assert record.state is WorkflowState.AWAITING_HUMAN_REVIEW
    assert record.diagnosis is not None
    assert record.jira_draft is not None
    assert record.change_request is not None
    # No external write happened before approval.
    assert _write_oks(service) == []


def test_no_external_write_before_approval_even_with_writes_enabled():
    service = WorkflowService(make_settings(enable_external_writes=True))
    service.start_incident(make_incident())
    assert _write_oks(service) == []  # execute node not reached (interrupt)


def test_approval_resumes_and_writes_once_enabled():
    service = WorkflowService(make_settings(enable_external_writes=True))
    record = service.start_incident(make_incident())
    result = service.approve_change_request(record.correlation_id, "lead@example.com")
    assert result.status == "submitted"
    assert result.servicenow_id
    updated = service.get_record(record.correlation_id)
    assert updated.state is WorkflowState.COMPLETED
    assert set(_write_oks(service)) == {"jira.write.ok", "servicenow.write.ok"}


def test_approval_blocked_when_writes_disabled(service):
    record = service.start_incident(make_incident())
    result = service.approve_change_request(record.correlation_id, "lead@example.com")
    assert result.status == "blocked"
    assert service.get_record(record.correlation_id).state is WorkflowState.AWAITING_HUMAN_REVIEW


def test_correlation_id_threads_through_audit(service):
    record = service.start_incident(make_incident())
    cid = record.correlation_id
    audited = service.deps.audit.find(correlation_id=cid)
    assert audited  # received + drafted events carry the correlation id
    assert {"incident.received", "diagnosis.drafted"} <= {e.event_type for e in audited}


def test_duplicate_write_is_idempotent():
    service = WorkflowService(make_settings(enable_external_writes=True))
    record = service.start_incident(make_incident())
    service.approve_change_request(record.correlation_id, "lead@example.com")
    first = service.get_record(record.correlation_id).connector_results.get("jira_key")
    # A second Jira write for the same incident reuses the recorded external id.
    res = service.submit_jira(record.correlation_id, "lead@example.com")
    assert res.status == "created"
    assert res.jira_key == first


def test_partial_failure_is_dead_lettered(monkeypatch):
    service = WorkflowService(make_settings())

    def boom(incident):
        raise RuntimeError("diagnostics unavailable")

    # Force the log agent's adapter to fail so the workflow raises and dead-letters.
    monkeypatch.setattr(service.deps.diagnostics, "fetch", boom)
    incident = make_incident(event_id="evt-fail")
    record = service.start_incident(incident)
    assert record.state is WorkflowState.FAILED
    assert service.deps.dead_letter.get("evt-fail") is not None


def test_retry_call_recovers_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("transient")
        return "ok"

    assert retry_call(flaky, attempts=3, base_delay_s=0.0, sleep=lambda _s: None) == "ok"
    assert calls["n"] == 3


def test_retry_call_exhausts():
    def always_fail():
        raise ValueError("nope")

    try:
        retry_call(always_fail, attempts=2, base_delay_s=0.0, sleep=lambda _s: None)
        raise AssertionError("expected RetryError")
    except RetryError:
        pass
