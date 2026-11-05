"""Genie integration (plan decision D4).

Issues natural-language questions and returns answers. Generated SQL and source
references are retained in the result for auditing and future surfacing, but are not
streamed through the current co-pilot SSE contract (critique PC-007). Reachable through
the managed Genie MCP server by default; the stub returns deterministic answers.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class GenieAnswer(BaseModel):
    answer: str
    generated_sql: str | None = None
    source_references: list[str] = Field(default_factory=list)


class GenieClient(Protocol):
    def ask(self, *, question: str) -> GenieAnswer: ...


class StubGenieClient:
    def ask(self, *, question: str) -> GenieAnswer:
        return GenieAnswer(
            answer=(
                "Based on recent runs, the most likely issue is schema drift in an "
                "upstream source table affecting the failing pipeline."
            ),
            generated_sql=(
                "SELECT * FROM system.workflows.job_run_timeline "
                "WHERE result_state = 'FAILED' ORDER BY period_end_time DESC LIMIT 20"
            ),
            source_references=["system.workflows.job_run_timeline"],
        )
