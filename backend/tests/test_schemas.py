"""Unit tests: `design §5` contracts, BFF shapes, and status mapping (critique PC-004)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.events import DiagnosisResult, IncidentEvent
from app.schemas.internal import WorkflowState, status_for_state


def test_incident_event_requires_core_fields():
    with pytest.raises(ValidationError):
        IncidentEvent(event_id="e", source="skybot")  # type: ignore[call-arg]


def test_incident_event_rejects_unknown_source():
    with pytest.raises(ValidationError):
        IncidentEvent(
            event_id="e",
            source="pagerduty",  # not in the allowed set
            incident_id="i",
            severity="high",
            service="svc",
            occurred_at="2026-11-05T00:00:00Z",
            payload={},
            signature="s",
        )


def test_diagnosis_result_roundtrip():
    d = DiagnosisResult(correlation_id="c", summary="s", generated_at="2026-11-05T00:00:00Z")
    assert DiagnosisResult.model_validate(d.model_dump()) == d


def test_status_mapping_collapses_active_states():
    for state in (
        WorkflowState.RECEIVED,
        WorkflowState.VALIDATING,
        WorkflowState.COLLECTING_EVIDENCE,
        WorkflowState.DIAGNOSING,
        WorkflowState.DRAFTING,
        WorkflowState.AWAITING_HUMAN_REVIEW,
    ):
        assert status_for_state(state) == "awaiting_human_review"


def test_status_mapping_terminal_states():
    assert status_for_state(WorkflowState.EXECUTING_APPROVED_ACTION) == "executing_approved_action"
    assert status_for_state(WorkflowState.FAILED) == "failed"
    assert status_for_state(WorkflowState.COMPLETED) == "completed"
    assert (
        status_for_state(WorkflowState.COMPLETED, resolved_with_recommendation=True)
        == "resolved_with_recommendation"
    )
