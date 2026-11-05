"""Diagnosis Agent — converts evidence into a structured diagnosis via Mosaic AI."""

from __future__ import annotations

from ..adapters.model import ModelAdapter
from ..schemas.events import DiagnosisResult
from ..schemas.internal import EvidenceBundle


class DiagnosisAgent:
    def __init__(self, model: ModelAdapter) -> None:
        self._model = model

    def diagnose(
        self, *, correlation_id: str, sanitized_context: dict, evidence: EvidenceBundle
    ) -> DiagnosisResult:
        diagnosis = self._model.generate_diagnosis(
            correlation_id=correlation_id,
            sanitized_context=sanitized_context,
            evidence=evidence,
        )
        # Model output must be schema-valid before it can leave the agent (`design §5`).
        return DiagnosisResult.model_validate(diagnosis.model_dump())
