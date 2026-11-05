"""Escalation Agent — maps incident context into proposed Jira fields (`design §4.3.2`)."""

from __future__ import annotations

from ..schemas.events import DiagnosisResult, IncidentEvent
from ..schemas.wire import JiraDraft


class EscalationAgent:
    def map_jira(self, *, incident: IncidentEvent, diagnosis: DiagnosisResult) -> JiraDraft:
        return JiraDraft(
            correlation_id=diagnosis.correlation_id,
            project="DATAENG",
            issue_type="Bug",
            summary=f"[{incident.service}] {diagnosis.summary}",
            description=(
                f"Incident {incident.incident_id} (source {incident.source}).\n"
                f"{diagnosis.summary}\n\nRecommended actions:\n- "
                + "\n- ".join(diagnosis.recommended_actions)
            ),
            severity=incident.severity,
            incident_link=f"servicenow://incident/{incident.incident_id}",
        )
