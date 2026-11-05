"""Databricks AI Functions adapter (plan decision D4).

Wraps the SQL-callable AI functions (`ai_query`, `ai_classify`, `ai_extract`,
`ai_summarize`, `ai_mask`) against a SQL warehouse. Inputs carry only sanitized,
task-relevant context (NFR-002). The stub returns deterministic results so no SQL
warehouse is required.
"""

from __future__ import annotations

from typing import Protocol


class AIFunctionsAdapter(Protocol):
    def classify(self, *, text: str, labels: list[str]) -> str: ...
    def extract(self, *, text: str, fields: list[str]) -> dict[str, str]: ...
    def summarize(self, *, text: str, max_words: int = 60) -> str: ...
    def mask(self, *, text: str) -> str: ...


class StubAIFunctionsAdapter:
    def classify(self, *, text: str, labels: list[str]) -> str:
        return labels[0] if labels else "unknown"

    def extract(self, *, text: str, fields: list[str]) -> dict[str, str]:
        return {field: "" for field in fields}

    def summarize(self, *, text: str, max_words: int = 60) -> str:
        words = text.split()
        return " ".join(words[:max_words])

    def mask(self, *, text: str) -> str:
        return text
