"""Change Agent — drafts a change request and stops at the approval boundary (`design §4.4`, `§8`)."""

from __future__ import annotations

from ..schemas.events import DiagnosisResult, IncidentEvent
from ..schemas.wire import ChangeRequestDraft


class ChangeAgent:
    def draft_change_request(
        self, *, incident: IncidentEvent, diagnosis: DiagnosisResult, jira_key: str | None = None
    ) -> ChangeRequestDraft:
        return ChangeRequestDraft(
            correlation_id=diagnosis.correlation_id,
            proposed_action=f"Submit a ServiceNow change request to remediate {incident.service}",
            code_change_summary="Apply the validated schema fix and re-enable the pipeline.",
            risk_assessment="Medium — schema change affects one ingestion job; backward compatible.",
            test_evidence=["CI pipeline: PASSED", "Data quality checks: PASSED"],
            rollback_plan="Revert the schema change and restore the previous job definition.",
            affected_records=[incident.incident_id] + ([jira_key] if jira_key else []),
            evidence=diagnosis.source_references,
            linked_records=[f"servicenow://incident/{incident.incident_id}"]
            + ([f"jira://{jira_key}"] if jira_key else []),
        )
