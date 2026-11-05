<!-- markdownlint-disable-file -->
# RPI Plan Critique: Scaffold Backend

**Task:** Scaffold Python/FastAPI + LangGraph backend
**Plan:** [.copilot-tracking/plans/2026-11-05/scaffold-backend-plan.md](../../../plans/2026-11-05/scaffold-backend-plan.md)
**Depth:** standard
**Date:** 2026-11-05
**Execution:** Complete (independent `rubber-duck` subagent, read-only; artifact persisted by the planning parent)

**Verdict: Revise — 1 blocking, 5 major, 1 minor**

## Findings

| ID | Severity | Plan location | Concern |
|---|---|---|---|
| PC-001 | blocking | P04-T02, P06-T02 | Browser mutation routes lack a defined authentication, authorization, and approval-payload-binding contract. |
| PC-002 | major | P07-T01, Follow-Up Items | Required mocked integration, security, and failure-path tests (`design §9`) are incorrectly deferred. |
| PC-003 | major | P05-T01/T02, P06-T01/T02, P07-T01 | Task-level dependencies omit components the tasks explicitly consume. |
| PC-004 | major | P02-T01/T02 | Internal workflow states conflict with the frontend's narrower `IncidentStatus` contract. |
| PC-005 | major | P04-T02, P06-T01 | Required webhook rate limiting (`tech-arch §3`, `§6`) is absent despite configuration coverage. |
| PC-006 | major | P04-T03 | Authorized manual replay required by `design §7` is absent. |
| PC-007 | minor | P03-T02, P06-T02 | Claimed Genie provenance visibility cannot pass through the existing SSE contract. |

## Finding details

### PC-001 — Browser writes lack an authorization and approval-binding contract (blocking)
- Evidence: `design §6` requires connector-specific authorization for every user action; `§8` requires approval identity and the exact proposed action. `frontend/src/api/apiClient.ts` sends bodyless POSTs for Jira creation and change approval. The plan defines only a Teams role re-check; P06-T02 gates browser writes using only the feature flag and the LangGraph approval node.
- Why it matters: When external writes are enabled, the plan does not establish how the browser principal is authenticated, authorized, associated with the approval, or bound to the exact draft payload. A caller could resume a privileged write using only a correlation ID.
- Smallest change: Either (1) browser mutation routes always return `blocked`, with authoritative approvals accepted only through `/actions/teams`; or (2) add trusted user-identity extraction, backend policy checks, draft version/payload-hash verification, action-ID/idempotency, and approval auditing to P02/P04/P06 and their tests.
- Decision route: User/backend-owner decision required, then planner.

### PC-002 — Mandatory tests are incorrectly deferred (major)
- Evidence: `design §9` requires mocked integration tests and replay, unauthorized-action, prompt-injection, secret-leakage, retry, timeout, duplicate-event, partial-failure, and approval-path tests. P07-T01 defers most of these to "once live endpoints exist," although `§9` calls for mocked endpoints.
- Why it matters: The scaffold could pass while its central safety and failure-handling claims remain unverified.
- Smallest change: Add these scenarios to P07-T01 using the planned stubs/mocks, including no-write-before-approval and correlation-ID end-to-end assertions.
- Decision route: Direct planner correction.

### PC-003 — Task DAG omits required predecessors (major)
- Evidence: P05-T01 defines external-write nodes but omits P04-T01 connectors; P05-T02 defines communication/escalation agents but omits P04-T01; P06-T01 records audit events but omits P04-T03; P06-T02 performs connector writes and approval auditing but omits P04-T01/P04-T03; P07-T01 claims end-to-end coverage but omits P04-T01/P04-T03/P05-T02.
- Why it matters: Independent task execution can begin before required interfaces exist, causing rework.
- Smallest change: Add the missing direct task dependencies (or state that phase dependencies impose a barrier over all tasks in the phase).
- Decision route: Direct planner correction.

### PC-004 — Workflow and BFF status enums are incompatible (major)
- Evidence: `frontend/src/types/wire.ts` permits only five `IncidentStatus` values (including `resolved_with_recommendation`). P02-T02 says the nine internal LangGraph states should form a canonical enum shared with the BFF; several internal states are absent from the frontend contract, while `resolved_with_recommendation` is absent from the internal list.
- Why it matters: Sharing one enum would violate the frontend contract or misreport active states.
- Smallest change: Define separate `WorkflowState` and `IncidentStatus` models and an explicit mapping; decide whether active states are hidden, mapped, or added to the frontend contract.
- Decision route: Direct separation (no frontend change required); backend-owner only if the frontend contract must change.

### PC-005 — Webhook rate limiting is not implemented (major)
- Evidence: `tech-arch §3` and `§6` require request limits/rate limiting at the inbound boundary. The plan configures rate-limit settings but defines no limiter, route behavior, metrics, or tests.
- Why it matters: Webhook flooding can exhaust the app or amplify workflow processing.
- Smallest change: Add a configurable per-source limiter seam to P04-T02, enforce it in P06-T01, and test rejection and telemetry.
- Decision route: Direct planner correction.

### PC-006 — Authorized manual replay is missing (major)
- Evidence: `design §7` requires manual replay only through an authorized operational interface. The plan provides dead-letter storage but no replay authorization, idempotency, or audit seam.
- Why it matters: Failed events cannot be recovered safely, or may later be replayed through an unsafe ad hoc mechanism.
- Smallest change: Add an authorized, audited, idempotent replay service interface and stub tests to P04-T03 (a public route is unnecessary for the scaffold).
- Decision route: Direct planner correction.

### PC-007 — Genie provenance cannot reach the current frontend (minor)
- Evidence: P03-T02 says generated SQL and source references remain visible to the console. `frontend/src/api/streamClient.ts` preserves only text deltas, errors, truncation, and completion, discarding provenance fields.
- Why it matters: The plan promises a console capability the supplied BFF contract does not support.
- Smallest change: Retain provenance internally and scope the console-display claim as a future frontend contract change outside this scaffold.
- Decision route: Direct planner correction.

## Summary
Revise: PC-001 blocking; PC-002–PC-006 major; PC-007 minor. Highest priority is deciding and specifying the authorization model for browser-triggered external writes (PC-001).
