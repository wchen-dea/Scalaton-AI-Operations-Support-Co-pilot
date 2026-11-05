<!-- markdownlint-disable-file -->
# RPI Changes: Scalaton durable event storage and session memory

## Metadata

* Task ID: scalaton-durable-storage-session-memory
* Related plan: [.copilot-tracking/plans/2026-11-05/scalaton-durable-storage-session-memory-plan.md](../../plans/2026-11-05/scalaton-durable-storage-session-memory-plan.md)
* Implementation date: 2026-11-05

## Execution Status

* Status: Complete
* Declared invocation scope: full plan
* Completed scope markers: P01, P01-T01, P01-T02, P02, P02-T01, P02-T02, P03, P03-T01, P03-T02, P04, P04-T01
* All remaining active-plan markers: none
* Status basis: every plan marker is checked with a changes-record entry and validation evidence; full backend suite passes.

## Execution Summary

Closed the ADR-SCALATON-002 gap: a cohesive in-memory storage plane, ingestion lineage with idempotency and an external-action ledger, and redacted co-pilot session memory — all as Release 1 in-memory ports matching the existing "stub now, Delta later" scaffold stance. No live Delta or Vector Search integration was introduced.

## Completed Work

### Governed storage plane with ADR-SCALATON-002 datasets

* Related phase or task: P01 (P01-T01, P01-T02)
* Files:
  * [backend/app/storage/models.py](../../../backend/app/storage/models.py)
  * [backend/app/storage/repositories.py](../../../backend/app/storage/repositories.py)
  * [backend/app/storage/__init__.py](../../../backend/app/storage/__init__.py)
  * [backend/app/orchestration/deps.py](../../../backend/app/orchestration/deps.py)
* Behavior or functionality changed: The backend now exposes a cohesive `Repositories` storage plane with typed in-memory repositories for the ADR-SCALATON-002 §3/§5 datasets (`bronze_inbound_events`, `silver_normalized_events`, `workflow_runs`, `external_actions`, `session_messages`), composing the existing `AuditStore` and `DeadLetterStore` so `Deps.audit`/`Deps.dead_letter` and the plane share one instance each. Bronze is append-only/immutable with duplicate detection; workflow runs and external actions upsert idempotently; session messages store per-session ordered history. `Deps.build` constructs the plane as the single swap point for a later Delta-backed implementation.
* Validation: Passed — `pytest` 49 passed; `Deps.build` confirms `repos.audit is audit` and `repos.dead_letter is dead_letter`.

### Durable event ingestion lineage, idempotency, and external-action ledger

* Related phase or task: P02 (P02-T01, P02-T02)
* Files:
  * [backend/app/orchestration/service.py](../../../backend/app/orchestration/service.py)
* Behavior or functionality changed: `WorkflowService.start_incident` now appends an immutable `bronze_inbound_events` row, a canonical `silver_normalized_events` row, and upserts a durable `workflow_runs` row (status/references/timestamps) for every incident, including the terminal `failed` state. A repeated event ID is acknowledged idempotently (audited as `incident.duplicate`) and returns the existing workflow instead of starting a second run (ADR-SCALATON-002 §4). The in-memory `_records` map is now explicitly a non-authoritative read cache. Gated writes in `submit_jira` and `approve_change_request` record idempotency-keyed `external_actions` ledger rows (target system, action, request hash, outcome, external record ID).
* Validation: Passed — `pytest` 49 passed; smoke check confirms single bronze/silver row and shared record on duplicate delivery, workflow run persisted with status.

### Redacted co-pilot session memory and retrieval

* Related phase or task: P03 (P03-T01, P03-T02)
* Files:
  * [backend/app/security/redaction.py](../../../backend/app/security/redaction.py)
  * [backend/app/orchestration/service.py](../../../backend/app/orchestration/service.py)
  * [backend/app/schemas/wire.py](../../../backend/app/schemas/wire.py)
  * [backend/app/api/console.py](../../../backend/app/api/console.py)
* Behavior or functionality changed: The co-pilot now has durable, backend-governed conversation memory. `POST /api/copilot/stream` accepts an optional `session_id` and `correlation_id`, generates a stable `session_id` when absent (returned via the `x-session-id` response header), and persists a redacted user message and the redacted assistant reply to `session_messages` with `actor_id`, `role`, `created_at`, and a `retention_until` window — never browser storage (ADR-SCALATON-002 §5.2). A new `redact_text` primitive masks recognizable secrets, credentials, auth headers, provider key prefixes, and emails before storage (§8). `GET /api/copilot/sessions/{session_id}` returns the ordered redacted history. The streamed SSE frame shape is unchanged.
* Validation: Passed — `pytest` 55 passed; smoke check confirms user secret masked, assistant reply stored, retention set, and history retrievable.

### Storage, ingestion, and session-memory tests

* Related phase or task: P04 (P04-T01)
* Files:
  * [backend/tests/test_storage_session.py](../../../backend/tests/test_storage_session.py)
* Behavior or functionality changed: Added six tests proving bronze/silver/workflow-run persistence on `start_incident`, duplicate-event idempotency (single bronze row, shared record, `incident.duplicate` audit), durable workflow-run `completed` status after approval, the servicenow/jira `external_actions` ledger, redacted co-pilot session storage and retrieval, and the `redact_text` masking/preserving behavior.
* Validation: Passed — full backend suite `55 passed`; `ruff check` clean on all changed files.

## Implementation-Time Plan Updates

## Business Alignment

* None

## Validation Record

| Check | Scope | Status | Evidence or reason |
|-------|-------|--------|--------------------|
| `pytest` baseline | backend | Passed | 49 passed before changes |
| `pytest` full suite | backend | Passed | 55 passed (49 baseline + 6 new) |
| `ruff check` | changed files | Passed | all checks passed |
| Duplicate-delivery idempotency | storage/service | Passed | single bronze row, shared record, `incident.duplicate` audit |
| Redaction-before-store | session memory | Passed | secret masked in stored content; `retention_until` set |

## Pre-Review Reconciliation

* Plan markers and task-local context: current (all P01-P04 checked)
* Completed-work entries and handoff prose: current
* Validation, blockers, remaining work, and follow-up items: current
* Review readiness: ready

## Blockers

* None

## Remaining Work

* None within declared scope. Release 2 items tracked as follow-ups below.

## Follow-Up Items

* Canonical plan list: [.copilot-tracking/plans/2026-11-05/scalaton-durable-storage-session-memory-plan.md](../../plans/2026-11-05/scalaton-durable-storage-session-memory-plan.md), `## Follow-Up Items`
* FU1 (Release 2): live Unity Catalog Delta-backed `Repositories`, LangGraph durable checkpointer, and Vector Search semantic-memory refresh, behind the same ports.
* FU2 (outside immediate backend gap): frontend consumption of the `x-session-id` header and `GET /api/copilot/sessions/{session_id}` to render conversation memory.

## Return-to-Caller State

* Implementation execution status: Complete (full plan)
* Declared scope and markers: full plan; P01-P04 and all tasks checked; no remaining active markers
* Validation coverage: full backend suite `55 passed`; `ruff` clean on changed files
* Blockers: none
* Current plan updates: none beyond marker check-offs
* Business alignment entries: none (new in-memory ports realize ADR-SCALATON-002 Release 1 stance; no cited requirement behavior diverged)
* Planning and critique state: ready; critique optional and not run
* Follow-up items: FU1 (Release 2 live storage), FU2 (frontend session-memory consumption)
* Review readiness or no-handoff reason: ready for `/rpi-review`
* Continuation owner: user (standalone invocation)
