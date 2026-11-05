"""Knowledge Agent — retrieves runbooks and historical incidents (read-only).

Retrieved text is untrusted context, not instruction (`tech-arch §4.3`, `§8`).
"""

from __future__ import annotations

from ..adapters.vector_search import RetrievalResult, VectorSearchAdapter


class KnowledgeAgent:
    def __init__(self, vector_search: VectorSearchAdapter) -> None:
        self._vector_search = vector_search

    def retrieve(self, *, query: str) -> RetrievalResult:
        return self._vector_search.retrieve(query=query)
