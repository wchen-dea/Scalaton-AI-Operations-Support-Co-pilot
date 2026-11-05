"""Mosaic AI model adapter (`design §3`, `tech-arch §11`).

Performs the diagnosis/classification/extraction/draft-generation calls. The stub
returns a schema-valid `DiagnosisResult` built deterministically from the sanitized
context so the orchestrator runs offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from ..schemas.events import DiagnosisResult, ProbableCause
from ..schemas.internal import EvidenceBundle


class ModelAdapter(Protocol):
    def generate_diagnosis(
        self, *, correlation_id: str, sanitized_context: dict, evidence: EvidenceBundle
    ) -> DiagnosisResult: ...


class StubModelAdapter:
    """Deterministic stub that synthesizes a diagnosis from the evidence."""

    def generate_diagnosis(
        self, *, correlation_id: str, sanitized_context: dict, evidence: EvidenceBundle
    ) -> DiagnosisResult:
        service = sanitized_context.get("service", "unknown-service")
        return DiagnosisResult(
            correlation_id=correlation_id,
            summary=f"Automated diagnosis for {service}: likely pipeline failure with schema drift.",
            probable_causes=[
                ProbableCause(
                    description="Upstream schema drift in a source table",
                    confidence=0.72,
                    evidence=evidence.log_diagnostics[:2] or ["log: column type mismatch"],
                ),
                ProbableCause(
                    description="Transient compute/resource exhaustion",
                    confidence=0.41,
                    evidence=evidence.historical_incidents[:1] or ["similar incident INC-1042"],
                ),
            ],
            recommended_actions=[
                "Validate the source schema against the expected contract",
                "Re-run the failed task after confirming resource availability",
            ],
            unknowns=["Whether the drift originated upstream of the ingestion job"],
            source_references=evidence.source_references or evidence.runbook_references,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
