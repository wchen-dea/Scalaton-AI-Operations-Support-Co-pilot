"""The LangGraph graph state schema (`tech-arch §4.2`)."""

from __future__ import annotations

from typing import TypedDict


class GraphState(TypedDict, total=False):
    """Working state threaded through the orchestration graph.

    Carries the correlation ID and source event, sanitized context, retrieved evidence,
    the diagnosis and drafts, approval state, connector results, and error information
    (`tech-arch §4.2`). Values are JSON-native (dicts) so checkpoint serialization stays
    portable; typed models are reconstructed at the node boundaries.
    """

    correlation_id: str
    incident: dict
    sanitized_context: dict
    evidence: dict
    diagnosis: dict | None
    work_note: str | None
    jira_draft: dict | None
    change_request: dict | None
    operations_recorded: bool
    vector_refresh_requested: bool
    hot_fix_results: dict
    lifecycle_phase: str
    state: str
    approved: bool
    approval: dict | None
    connector_results: dict
    resolved_with_recommendation: bool
    error: str | None
