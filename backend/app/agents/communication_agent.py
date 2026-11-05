"""Communication Agent — drafts ServiceNow notes and Teams cards from validated results."""

from __future__ import annotations

from ..schemas.events import DiagnosisResult


class CommunicationAgent:
    def draft_work_note(self, *, diagnosis: DiagnosisResult) -> str:
        causes = "; ".join(
            f"{c.description} (confidence {c.confidence:.0%})" for c in diagnosis.probable_causes
        )
        actions = "; ".join(diagnosis.recommended_actions)
        return (
            f"[AI diagnosis — proposal awaiting human review]\n"
            f"Summary: {diagnosis.summary}\n"
            f"Probable causes: {causes}\n"
            f"Recommended actions: {actions}"
        )
