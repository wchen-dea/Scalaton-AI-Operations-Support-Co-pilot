"""LangGraph orchestrator: the `tech-arch §4.2` state machine with an approval pause.

The graph drives an incident through explicit states. External writes are isolated in a
dedicated `execute_approved_action` node, and the graph interrupts before that node so a
human approval (via Teams, the authoritative surface — plan decision D6) is required
before any production-impacting action. The correlation ID threads through every node.
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ..observability.logging import get_logger, set_correlation_id
from ..observability.tracing import span
from ..schemas.events import DiagnosisResult, IncidentEvent
from ..schemas.internal import EvidenceBundle, WorkflowState
from ..security.redaction import redact
from .deps import Deps
from .state import GraphState

_log = get_logger("graph")

EXTERNAL_WRITE_NODE = "execute_approved_action"


def build_graph(deps: Deps):
    """Compile the orchestration graph, interrupting before external writes."""

    from ..agents import (
        ChangeAgent,
        CommunicationAgent,
        DiagnosisAgent,
        EscalationAgent,
        KnowledgeAgent,
        LogAgent,
        ResearchAgent,
    )

    log_agent = LogAgent(deps.diagnostics)
    knowledge_agent = KnowledgeAgent(deps.vector_search)
    research_agent = ResearchAgent(vector_search=deps.vector_search, genie=deps.genie)
    diagnosis_agent = DiagnosisAgent(deps.model)
    communication_agent = CommunicationAgent()
    escalation_agent = EscalationAgent()
    change_agent = ChangeAgent()

    def _failed(state: GraphState) -> bool:
        return state.get("state") == WorkflowState.FAILED.value

    def validate(state: GraphState) -> dict:
        set_correlation_id(state["correlation_id"])
        if _failed(state):
            return {}
        incident = IncidentEvent.model_validate(state["incident"])
        with span("validate"):
            sanitized = {
                "incident_id": incident.incident_id,
                "source": incident.source,
                "severity": incident.severity,
                "service": incident.service,
                "payload": redact(incident.payload),
            }
        return {"sanitized_context": sanitized, "state": WorkflowState.VALIDATING.value}

    def collect_evidence(state: GraphState) -> dict:
        set_correlation_id(state["correlation_id"])
        if _failed(state):
            return {}
        incident = IncidentEvent.model_validate(state["incident"])
        with span("collect_evidence"):
            logs = log_agent.collect(incident)
            retrieval = knowledge_agent.retrieve(query=incident.service)
            research_notes, research_sources = research_agent.investigate(incident=incident)
        evidence = EvidenceBundle(
            log_diagnostics=logs,
            runbook_references=retrieval.runbook_references,
            historical_incidents=retrieval.historical_incidents,
            research_notes=research_notes,
            source_references=list(dict.fromkeys(retrieval.source_references + research_sources)),
        )
        return {"evidence": evidence.model_dump(), "state": WorkflowState.COLLECTING_EVIDENCE.value}

    def diagnose(state: GraphState) -> dict:
        set_correlation_id(state["correlation_id"])
        if _failed(state):
            return {}
        evidence = EvidenceBundle.model_validate(state.get("evidence") or {})
        with span("diagnose"):
            diagnosis = diagnosis_agent.diagnose(
                correlation_id=state["correlation_id"],
                sanitized_context=state.get("sanitized_context", {}),
                evidence=evidence,
            )
        return {"diagnosis": diagnosis.model_dump(), "state": WorkflowState.DIAGNOSING.value}

    def draft(state: GraphState) -> dict:
        set_correlation_id(state["correlation_id"])
        if _failed(state):
            return {}
        incident = IncidentEvent.model_validate(state["incident"])
        diagnosis = DiagnosisResult.model_validate(state["diagnosis"])
        with span("draft"):
            work_note = communication_agent.draft_work_note(diagnosis=diagnosis)
            jira_draft = escalation_agent.map_jira(incident=incident, diagnosis=diagnosis)
            change_request = change_agent.draft_change_request(
                incident=incident, diagnosis=diagnosis
            )
        deps.audit.record_event(
            event_type="diagnosis.drafted",
            actor="orchestrator",
            correlation_id=state["correlation_id"],
            source_id=incident.event_id,
            payload=diagnosis.model_dump(),
        )
        return {
            "work_note": work_note,
            "jira_draft": jira_draft.model_dump(),
            "change_request": change_request.model_dump(),
            "state": WorkflowState.AWAITING_HUMAN_REVIEW.value,
            "resolved_with_recommendation": True,
        }

    def execute_approved_action(state: GraphState) -> dict:
        set_correlation_id(state["correlation_id"])
        if _failed(state):
            return {}
        cid = state["correlation_id"]
        incident = IncidentEvent.model_validate(state["incident"])
        approval = state.get("approval") or {}
        connector_results = dict(state.get("connector_results", {}))
        with span("execute_approved_action"):
            jira_res = deps.jira.write(
                correlation_id=cid,
                source_event_id=incident.event_id,
                target_record=incident.incident_id,
                action_type="create_bug",
            )
            if jira_res.external_id:
                connector_results["jira_key"] = jira_res.external_id
                connector_results["jira_url"] = jira_res.data.get("url")
            sn_res = deps.servicenow.write(
                correlation_id=cid,
                source_event_id=incident.event_id,
                target_record=incident.incident_id,
                action_type="submit_change_request",
            )
            if sn_res.external_id:
                connector_results["servicenow_change_id"] = sn_res.external_id
        deps.audit.record_event(
            event_type="change_request.approved",
            actor=approval.get("approver", "unknown"),
            correlation_id=cid,
            external_record_id=connector_results.get("servicenow_change_id"),
            payload=approval,
        )
        return {
            "state": WorkflowState.COMPLETED.value,
            "connector_results": connector_results,
            "resolved_with_recommendation": False,
        }

    builder = StateGraph(GraphState)
    builder.add_node("validate", validate)
    builder.add_node("collect_evidence", collect_evidence)
    builder.add_node("diagnose", diagnose)
    builder.add_node("draft", draft)
    builder.add_node(EXTERNAL_WRITE_NODE, execute_approved_action)

    builder.add_edge(START, "validate")
    builder.add_edge("validate", "collect_evidence")
    builder.add_edge("collect_evidence", "diagnose")
    builder.add_edge("diagnose", "draft")
    builder.add_edge("draft", EXTERNAL_WRITE_NODE)
    builder.add_edge(EXTERNAL_WRITE_NODE, END)

    return builder.compile(
        checkpointer=MemorySaver(), interrupt_before=[EXTERNAL_WRITE_NODE]
    )


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
