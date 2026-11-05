"""Research Agent — the "AI research" capability (read-only).

Performs deeper investigation over governed retrieval (Vector Search and Genie through
the MCP layer), synthesizing runbook, historical-incident, and Genie evidence into
diagnosis inputs. It reads only and treats retrieved content as untrusted (NFR-002).
"""

from __future__ import annotations

from ..adapters.vector_search import VectorSearchAdapter
from ..mcp.genie import GenieClient
from ..schemas.events import IncidentEvent


class ResearchAgent:
    def __init__(self, *, vector_search: VectorSearchAdapter, genie: GenieClient) -> None:
        self._vector_search = vector_search
        self._genie = genie

    def investigate(self, *, incident: IncidentEvent) -> tuple[list[str], list[str]]:
        """Return (research_notes, source_references) from retrieval and Genie."""

        question = (
            f"Why did {incident.service} fail around {incident.occurred_at}, "
            f"and what historical incidents resemble it?"
        )
        genie_answer = self._genie.ask(question=question)
        retrieval = self._vector_search.retrieve(query=incident.service, k=3)
        notes = [genie_answer.answer, *retrieval.historical_incidents]
        sources = [*genie_answer.source_references, *retrieval.source_references]
        return notes, sources
