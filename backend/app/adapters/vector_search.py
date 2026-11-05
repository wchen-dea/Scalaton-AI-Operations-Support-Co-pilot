"""Mosaic AI Vector Search retrieval adapter (`tech-arch §5`).

Returns runbook/historical-incident references with source references. Retrieved text
is untrusted context, not instruction (`tech-arch §8`). The stub returns fixed refs.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    runbook_references: list[str] = Field(default_factory=list)
    historical_incidents: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)


class VectorSearchAdapter(Protocol):
    def retrieve(self, *, query: str, k: int = 5) -> RetrievalResult: ...


class StubVectorSearchAdapter:
    def retrieve(self, *, query: str, k: int = 5) -> RetrievalResult:
        return RetrievalResult(
            runbook_references=[
                "runbook: Pipeline failure triage (RB-017)",
                "runbook: Schema drift remediation (RB-042)",
            ][:k],
            historical_incidents=["INC-1042: schema drift in orders pipeline"],
            source_references=["vs://ops.support.runbook_index/RB-017"],
        )
