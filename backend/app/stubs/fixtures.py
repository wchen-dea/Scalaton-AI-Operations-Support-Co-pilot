"""Deterministic, spec-shaped seed data (plan decision D3).

Seeds a few incidents through the workflow service so the frontend's Triage/War Room
lists are populated in `live` mode against the local backend, with no webhook or live
dependency. The co-pilot stream uses the mock reply below.
"""

from __future__ import annotations

from ..schemas.events import IncidentEvent

SEED_EVENTS: list[IncidentEvent] = [
    IncidentEvent(
        event_id="evt-0001",
        source="skybot",
        incident_id="INC0012345",
        severity="high",
        service="orders-ingest-pipeline",
        occurred_at="2026-11-05T06:10:00Z",
        payload={"error": "AnalysisException: cannot resolve 'order_ts'"},
        signature="seed",
    ),
    IncidentEvent(
        event_id="evt-0002",
        source="servicenow",
        incident_id="INC0012346",
        severity="medium",
        service="billing-aggregation-job",
        occurred_at="2026-11-05T06:25:00Z",
        payload={"error": "Executor OOM"},
        signature="seed",
    ),
    IncidentEvent(
        event_id="evt-0003",
        source="jira",
        incident_id="INC0012347",
        severity="low",
        service="customer-360-refresh",
        occurred_at="2026-11-05T06:40:00Z",
        payload={"error": "Timeout waiting for upstream table"},
        signature="seed",
    ),
]


mock_copilot_reply = (
    "Here is what I found: the failing pipeline shows schema drift in an upstream "
    "source table. I recommend validating the source schema against the expected "
    "contract and re-running the task. This is a proposal awaiting your approval."
)


def seed_records(service) -> None:
    """Run the seed incidents through the workflow to the approval pause."""

    for event in SEED_EVENTS:
        service.start_incident(event)
