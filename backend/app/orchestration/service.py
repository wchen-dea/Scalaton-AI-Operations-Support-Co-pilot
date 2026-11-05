"""Workflow service: drives the LangGraph graph and serves the BFF reads/approvals.

The service owns the in-memory record store the browser (BFF) endpoints read from, so
those reads are independent of the graph's internals. It starts incidents (running to
the approval pause), exposes the drafts, and resumes the graph only on an authorized
Teams approval with external writes enabled (plan decisions D3, D6).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from ..audit.store import payload_hash
from ..config import Settings
from ..observability.logging import get_logger, set_correlation_id
from ..reliability.deadletter import DeadLetterEntry
from ..schemas.events import DiagnosisResult, IncidentEvent
from ..schemas.internal import ApprovalRecord, EvidenceBundle, WorkflowRecord, WorkflowState
from ..schemas.wire import ApprovalResult, ChangeRequestDraft, JiraDraft, JiraSubmitResult
from ..security.idempotency import derive_idempotency_key
from ..security.redaction import redact_text
from ..storage import (
    BronzeInboundEvent,
    ExternalAction,
    SessionMessage,
    SilverNormalizedEvent,
    WorkflowRun,
)
from .deps import Deps
from .graph import build_graph

_log = get_logger("service")

# Default conversation-memory retention window; a governed policy sets this later
# (ADR-SCALATON-002 §8, §10).
_SESSION_RETENTION_DAYS = 30


def _new_correlation_id() -> str:
    return f"cid-{uuid.uuid4().hex[:12]}"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowService:
    def __init__(self, settings: Settings, deps: Deps | None = None) -> None:
        self.settings = settings
        self.deps = deps or Deps.build(settings)
        self.graph = build_graph(self.deps)
        # Non-authoritative read cache; the durable record is `repos.workflow_runs`
        # (ADR-SCALATON-002 §9).
        self._records: dict[str, WorkflowRecord] = {}
        self._event_index: dict[str, str] = {}

    # --- lifecycle ---------------------------------------------------------
    def start_incident(self, incident: IncidentEvent) -> WorkflowRecord:
        # Duplicate events are safely acknowledged without starting a second workflow
        # (ADR-SCALATON-002 §4).
        existing_cid = self._event_index.get(incident.event_id)
        if existing_cid is not None and existing_cid in self._records:
            self.deps.audit.record_event(
                event_type="incident.duplicate",
                actor="webhook",
                correlation_id=existing_cid,
                source_id=incident.event_id,
                outcome="duplicate",
            )
            return self._records[existing_cid]

        cid = _new_correlation_id()
        set_correlation_id(cid)
        self._event_index[incident.event_id] = cid
        # Bronze: immutable raw provider payload and receipt metadata (ADR §3, §4.4).
        self.deps.repos.bronze.append(
            BronzeInboundEvent(
                event_id=incident.event_id,
                source=incident.source,
                correlation_id=cid,
                signature_result="verified",
                payload=incident.model_dump(),
            )
        )
        # Silver: canonical normalized event independent of provider format (ADR §3, §4.5).
        self.deps.repos.silver.upsert(
            SilverNormalizedEvent(
                event_id=incident.event_id,
                source=incident.source,
                correlation_id=cid,
                incident_id=incident.incident_id,
                severity=incident.severity,
                service=incident.service,
                occurred_at=incident.occurred_at,
            )
        )
        self.deps.audit.record_event(
            event_type="incident.received",
            actor="webhook",
            correlation_id=cid,
            source_id=incident.event_id,
            payload=incident.model_dump(),
        )
        initial = {
            "correlation_id": cid,
            "incident": incident.model_dump(),
            "state": WorkflowState.RECEIVED.value,
            "approved": False,
            "connector_results": {},
            "evidence": {},
        }
        try:
            result = self.graph.invoke(initial, self._config(cid))
        except Exception as exc:  # noqa: BLE001 - dead-letter any unexpected failure
            _log.exception("Workflow failed for %s", incident.incident_id)
            self.deps.dead_letter.add(
                DeadLetterEntry(
                    event_id=incident.event_id,
                    source=incident.source,
                    correlation_id=cid,
                    reason=str(exc),
                    payload=incident.model_dump(),
                )
            )
            self.deps.audit.record_event(
                event_type="workflow.failed",
                actor="orchestrator",
                correlation_id=cid,
                source_id=incident.event_id,
                outcome="failed",
            )
            record = WorkflowRecord(
                correlation_id=cid, incident=incident, state=WorkflowState.FAILED, error=str(exc)
            )
            self._records[cid] = record
            self._persist_run(record)
            return record
        record = self._record_from_state(cid, incident, result)
        self._records[cid] = record
        self._persist_run(record)
        return record

    def approve_change_request(self, correlation_id: str, approver: str) -> ApprovalResult:
        """Resume the graph past the approval pause to perform the gated external writes.

        Authoritative approval flows through Teams (plan decision D6); role re-checks
        happen at the route. External writes must be enabled, else the action is blocked.
        """

        record = self._records.get(correlation_id)
        if record is None:
            return ApprovalResult(status="blocked", reason="Unknown incident")
        if not self.settings.enable_external_writes:
            return ApprovalResult(
                status="blocked", reason="External writes are disabled in this environment."
            )
        cfg = self._config(correlation_id)
        approval = {
            "approver": approver,
            "approved_at": _utcnow(),
            "payload_hash": payload_hash(
                record.change_request.model_dump() if record.change_request else {}
            ),
        }
        self.graph.update_state(cfg, {"approved": True, "approval": approval})
        result = self.graph.invoke(None, cfg)
        updated = self._record_from_state(correlation_id, record.incident, result)
        updated.approval = ApprovalRecord(
            approver=approver,
            payload_hash=approval["payload_hash"],
            approved_at=approval["approved_at"],
            external_record_id=updated.connector_results.get("servicenow_change_id"),
        )
        self._records[correlation_id] = updated
        self._persist_run(updated)
        servicenow_id = updated.connector_results.get("servicenow_change_id")
        self.deps.repos.external_actions.record(
            ExternalAction(
                idempotency_key=derive_idempotency_key(
                    source_event_id=record.incident.event_id,
                    target_system="servicenow",
                    target_record=record.incident.incident_id,
                    action_type="submit_change_request",
                ),
                correlation_id=correlation_id,
                target_system="servicenow",
                action_type="submit_change_request",
                request_hash=approval["payload_hash"],
                outcome="submitted",
                external_record_id=servicenow_id,
            )
        )
        return ApprovalResult(status="submitted", servicenow_id=servicenow_id)

    def submit_jira(self, correlation_id: str, actor: str) -> JiraSubmitResult:
        """Create the proposed Jira bug (gated). Authoritative action flows via Teams (D6)."""

        record = self._records.get(correlation_id)
        if record is None:
            return JiraSubmitResult(status="blocked", reason="Unknown incident")
        if not self.settings.enable_external_writes:
            return JiraSubmitResult(
                status="blocked", reason="External writes are disabled in this environment."
            )
        res = self.deps.jira.write(
            correlation_id=correlation_id,
            source_event_id=record.incident.event_id,
            target_record=record.incident.incident_id,
            action_type="create_bug",
        )
        if not res.ok:
            return JiraSubmitResult(status="blocked", reason=res.blocked_reason or "Write blocked")
        self.deps.repos.external_actions.record(
            ExternalAction(
                idempotency_key=derive_idempotency_key(
                    source_event_id=record.incident.event_id,
                    target_system="jira",
                    target_record=record.incident.incident_id,
                    action_type="create_bug",
                ),
                correlation_id=correlation_id,
                target_system="jira",
                action_type="create_bug",
                request_hash=payload_hash(
                    record.jira_draft.model_dump() if record.jira_draft else {}
                ),
                outcome="created",
                external_record_id=res.external_id,
            )
        )
        return JiraSubmitResult(status="created", jira_key=res.external_id, url=res.data.get("url"))

    # --- BFF reads ---------------------------------------------------------
    def list_records(self) -> list[WorkflowRecord]:
        return list(self._records.values())

    def get_record(self, correlation_id: str) -> WorkflowRecord | None:
        return self._records.get(correlation_id)

    def get_jira_draft(self, correlation_id: str) -> JiraDraft | None:
        record = self._records.get(correlation_id)
        return record.jira_draft if record else None

    def get_change_request(self, correlation_id: str) -> ChangeRequestDraft | None:
        record = self._records.get(correlation_id)
        return record.change_request if record else None

    # --- session memory (ADR-SCALATON-002 §5.2) ----------------------------
    def record_session_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        actor_id: str,
        correlation_id: str | None = None,
    ) -> SessionMessage:
        """Persist one redacted conversation message to durable session memory.

        Content is redacted before storage so raw secrets and credentials are never
        persisted (`ADR-SCALATON-002 §8`, NFR-002).
        """

        now = datetime.now(timezone.utc)
        retention_until = (now + timedelta(days=_SESSION_RETENTION_DAYS)).isoformat()
        return self.deps.repos.session_messages.append(
            SessionMessage(
                session_id=session_id,
                correlation_id=correlation_id,
                actor_id=actor_id,
                role=role,
                content_redacted=redact_text(content),
                created_at=now.isoformat(),
                retention_until=retention_until,
            )
        )

    def session_history(self, session_id: str) -> list[SessionMessage]:
        return self.deps.repos.session_messages.history(session_id)

    # --- helpers -----------------------------------------------------------
    def _config(self, correlation_id: str) -> dict:
        return {"configurable": {"thread_id": correlation_id}}

    def _persist_run(self, record: WorkflowRecord) -> WorkflowRun:
        """Upsert the durable workflow run (ADR-SCALATON-002 §3, §5.1)."""

        return self.deps.repos.workflow_runs.upsert(
            WorkflowRun(
                correlation_id=record.correlation_id,
                incident_id=record.incident.incident_id,
                source=record.incident.source,
                severity=record.incident.severity,
                service=record.incident.service,
                status=record.state.value,
                updated_at=_utcnow(),
                error=record.error,
            )
        )

    def _record_from_state(self, cid: str, incident: IncidentEvent, state: dict) -> WorkflowRecord:
        diagnosis = state.get("diagnosis")
        jira_draft = state.get("jira_draft")
        change_request = state.get("change_request")
        return WorkflowRecord(
            correlation_id=cid,
            incident=incident,
            state=WorkflowState(state.get("state", WorkflowState.FAILED.value)),
            sanitized_context=state.get("sanitized_context", {}),
            evidence=EvidenceBundle.model_validate(state.get("evidence") or {}),
            diagnosis=DiagnosisResult.model_validate(diagnosis) if diagnosis else None,
            jira_draft=JiraDraft.model_validate(jira_draft) if jira_draft else None,
            change_request=(
                ChangeRequestDraft.model_validate(change_request) if change_request else None
            ),
            connector_results=state.get("connector_results", {}),
            resolved_with_recommendation=state.get("resolved_with_recommendation", False),
            error=state.get("error"),
        )
