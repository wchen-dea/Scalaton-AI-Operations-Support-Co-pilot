<!-- markdownlint-disable-file -->
# RPI Changes: Scaffold the AI Ops Support System FastAPI + LangGraph backend

## Metadata

* Task ID: scaffold-backend
* Related plan: [.copilot-tracking/plans/2026-11-05/scaffold-backend-plan.md](../../plans/2026-11-05/scaffold-backend-plan.md)
* Implementation date: 2026-11-05

## Execution Status

* Status: Complete
* Declared invocation scope: full plan (P01-P07)
* Completed scope markers: P01 (P01-T01, P01-T02), P02 (P02-T01, P02-T02), P03 (P03-T01, P03-T02), P04 (P04-T01, P04-T02, P04-T03), P05 (P05-T01, P05-T02), P06 (P06-T01, P06-T02), P07 (P07-T01, P07-T02)
* All remaining active-plan markers: none
* Status basis: every task's requirements hold; the backend builds, runs under uvicorn binding `DATABRICKS_APP_PORT`, serves the frontend's `/api/*` contract, and passes 49 `pytest` tests with no live external dependencies.

## Execution Summary

Realized the approved `scaffold-backend` plan: a buildable, runnable Python/FastAPI + LangGraph backend under [backend/](../../../backend). It encodes the `tech-arch §4.2` incident workflow as a LangGraph state machine with a human-approval pause, the seven specified agents (Log, Knowledge, Research, Diagnosis, Communication, Escalation, Change), typed `design §5` and BFF contracts, an intelligence/MCP/Genie layer, external connectors, and the security/audit/reliability/observability primitives — all behind typed stub interfaces so the app runs with no live Databricks, MCP, or external dependency (D3). Microsoft Teams is the authoritative approval surface (D6); the browser console's mutating routes return `blocked`.

## Completed Work

### Backend project foundation, configuration, health, and static serving

* Related phase or task: P01 (P01-T01, P01-T02)
* Files:
  * [backend/pyproject.toml](../../../backend/pyproject.toml), [backend/requirements.txt](../../../backend/requirements.txt), [backend/.gitignore](../../../backend/.gitignore)
  * [backend/app/main.py](../../../backend/app/main.py), [backend/app/__main__.py](../../../backend/app/__main__.py), [backend/app/config.py](../../../backend/app/config.py)
  * [backend/app/api/health.py](../../../backend/app/api/health.py)
* Behavior or functionality changed: A new `uv`-managed project (D2) at `backend/` exposes `app.main:app`, binds `DATABRICKS_APP_PORT` via `python -m app` with a local fallback, reads all configuration from the environment (`tech-arch §10`) with no secrets in code, answers `/health/live` and `/health/ready`, and serves the built `frontend/dist` same-origin (skipping gracefully when the dist is absent). A pinned `requirements.txt` was generated for the Databricks App runtime.
* Validation: `uv run python -m app` served `/health/live`, `/health/ready`, and `/api/incidents` on the injected port; import check passed.

### Typed data contracts: design §5, BFF wire shapes, and internal models

* Related phase or task: P02 (P02-T01, P02-T02)
* Files:
  * [backend/app/schemas/events.py](../../../backend/app/schemas/events.py), [backend/app/schemas/wire.py](../../../backend/app/schemas/wire.py), [backend/app/schemas/internal.py](../../../backend/app/schemas/internal.py)
* Behavior or functionality changed: Pydantic models represent the authoritative `design §5` Incident event and Diagnosis result, the browser (BFF) shapes matching `frontend/src/types/wire.ts` exactly (snake_case), and the orchestrator's internal `WorkflowState`/`WorkflowRecord`/`EvidenceBundle`/`ApprovalRecord` models. A separate internal `WorkflowState` (nine states) and five-value BFF `IncidentStatus` are bridged by `status_for_state` (critique PC-004). Model output is validated against `DiagnosisResult` before leaving an agent.
* Validation: `test_schemas.py` (status mapping, source validation, roundtrip) passed.

### Intelligence and integration layer: adapters, MCP connection layer, Genie

* Related phase or task: P03 (P03-T01, P03-T02)
* Files:
  * [backend/app/adapters/model.py](../../../backend/app/adapters/model.py), [backend/app/adapters/vector_search.py](../../../backend/app/adapters/vector_search.py), [backend/app/adapters/diagnostics.py](../../../backend/app/adapters/diagnostics.py), [backend/app/adapters/ai_functions.py](../../../backend/app/adapters/ai_functions.py)
  * [backend/app/mcp/registry.py](../../../backend/app/mcp/registry.py), [backend/app/mcp/client.py](../../../backend/app/mcp/client.py), [backend/app/mcp/genie.py](../../../backend/app/mcp/genie.py)
* Behavior or functionality changed: Typed `Protocol` interfaces expose Mosaic AI model inference, Vector Search retrieval, Unity Catalog diagnostics, and Databricks AI Functions, each with a deterministic stub. An MCP connection layer registers the Databricks-managed MCP servers (Genie, Vector Search, UC functions) plus a config-driven external-MCP set (referenced by resource name, never inline URLs/tokens) and loads their tools for the agents (D4). A Genie integration returns answers with generated SQL/source references retained internally for audit (not streamed through the current SSE contract — PC-007).
* Validation: `test_integration.py` (registry includes managed + external servers, tool loading, Genie provenance, AI functions, vector search) passed.

### Connectors, security, audit, reliability, and observability primitives

* Related phase or task: P04 (P04-T01, P04-T02, P04-T03)
* Files:
  * [backend/app/connectors/base.py](../../../backend/app/connectors/base.py), [backend/app/connectors/servicenow.py](../../../backend/app/connectors/servicenow.py), [backend/app/connectors/jira.py](../../../backend/app/connectors/jira.py), [backend/app/connectors/teams.py](../../../backend/app/connectors/teams.py), [backend/app/connectors/skybot.py](../../../backend/app/connectors/skybot.py)
  * [backend/app/security/signatures.py](../../../backend/app/security/signatures.py), [backend/app/security/redaction.py](../../../backend/app/security/redaction.py), [backend/app/security/rbac.py](../../../backend/app/security/rbac.py), [backend/app/security/idempotency.py](../../../backend/app/security/idempotency.py), [backend/app/security/ratelimit.py](../../../backend/app/security/ratelimit.py)
  * [backend/app/audit/store.py](../../../backend/app/audit/store.py), [backend/app/reliability/retry.py](../../../backend/app/reliability/retry.py), [backend/app/reliability/deadletter.py](../../../backend/app/reliability/deadletter.py), [backend/app/reliability/replay.py](../../../backend/app/reliability/replay.py), [backend/app/observability/logging.py](../../../backend/app/observability/logging.py), [backend/app/observability/metrics.py](../../../backend/app/observability/metrics.py), [backend/app/observability/tracing.py](../../../backend/app/observability/tracing.py)
* Behavior or functionality changed: Connectors implement the `tech-arch §6` contract (schema validation, correlation/idempotency, bounded retries, normalized errors, audit per read/write), with writes gated by the external-write flag and idempotent by derived key. Security primitives provide webhook signature/timestamp/replay/allowlist verification, pre-model redaction, a Teams role re-check, idempotency-key derivation, and a per-source rate limiter (FR-016). An append-only audit store records payload hashes (never raw secrets), and reliability adds bounded retry/backoff, a dead-letter store, and an authorized/audited/idempotent replay interface (FR-017). Logging/metrics/tracing carry the correlation ID.
* Validation: `test_signatures.py`, `test_redaction.py`, `test_ratelimit.py`, `test_security.py` (unauthorized action, replay authorization/idempotency, secret non-leakage, prompt-injection-as-data) passed.

### LangGraph orchestrator and agent boundaries

* Related phase or task: P05 (P05-T01, P05-T02)
* Files:
  * [backend/app/orchestration/state.py](../../../backend/app/orchestration/state.py), [backend/app/orchestration/graph.py](../../../backend/app/orchestration/graph.py), [backend/app/orchestration/service.py](../../../backend/app/orchestration/service.py), [backend/app/orchestration/deps.py](../../../backend/app/orchestration/deps.py)
  * [backend/app/agents/](../../../backend/app/agents) (log, knowledge, research, diagnosis, communication, escalation, change)
* Behavior or functionality changed: A LangGraph `StateGraph` drives an incident through the `tech-arch §4.2` states (`received` through `awaiting_human_review`), isolating external writes in a dedicated node and interrupting before it so a human approval is required (`design §8`). The graph state is JSON-native for portable checkpoint serialization. Seven typed agents consume the intelligence/MCP adapters and communicate through internal models; the Research agent (the "AI research" ask) synthesizes Genie + Vector Search evidence. The workflow service runs the graph to the pause, stores records for BFF reads, and resumes only on an authorized Teams approval with external writes enabled.
* Validation: `test_workflow.py` (pause at approval boundary, no write before approval, resume-and-write when enabled, correlation-ID threading, idempotent write, dead-letter on partial failure, retry recover/exhaust) passed.

### FastAPI route surface: webhooks, Teams actions, BFF console, and SSE

* Related phase or task: P06 (P06-T01, P06-T02)
* Files:
  * [backend/app/api/webhooks.py](../../../backend/app/api/webhooks.py), [backend/app/api/actions.py](../../../backend/app/api/actions.py), [backend/app/api/console.py](../../../backend/app/api/console.py), [backend/app/api/deps.py](../../../backend/app/api/deps.py)
  * [backend/app/stubs/fixtures.py](../../../backend/app/stubs/fixtures.py)
* Behavior or functionality changed: Webhook routes (`/webhooks/servicenow|jira|skybot`) verify signature + rate limit + minimum schema, then acknowledge with `202` and process the workflow asynchronously (`tech-arch §4.1`). `/actions/teams` re-checks the operator role (Teams is authoritative) before approving a change request or creating a Jira bug. The BFF `/api/*` routes serve the incidents list/detail, Jira/CR drafts, and the co-pilot SSE stream (frames matching `frontend/src/api/streamClient.ts`), with mutating routes returning `blocked` (D6). Deterministic seed incidents populate the console without a webhook.
* Validation: `test_console_api.py` (health, seeded list, detail/drafts, blocked browser writes, SSE frames, signed-webhook acceptance + async processing, bad-signature 401, invalid-schema 422, rate-limit 429) passed; live-server curl confirmed the same.

### Tests, Databricks App manifest, and operator docs

* Related phase or task: P07 (P07-T01, P07-T02)
* Files:
  * [backend/tests/](../../../backend/tests) (`conftest.py`, `test_schemas.py`, `test_signatures.py`, `test_redaction.py`, `test_ratelimit.py`, `test_workflow.py`, `test_security.py`, `test_console_api.py`, `test_integration.py`)
  * [app.yaml](../../../app.yaml), [backend/README.md](../../../backend/README.md), [README.md](../../../README.md)
* Behavior or functionality changed: A 49-test `pytest` suite covers payload validation, signature verification, redaction, idempotency, rate limiting, state transitions, the approval boundary, retries, dead-letter/replay, mocked integration, and the security scenarios `design §9` requires (replay, unauthorized action, prompt injection, secret leakage) — all against stubs with no live dependency. A deployable [app.yaml](../../../app.yaml) runs the FastAPI backend (`python -m app`, binding `DATABRICKS_APP_PORT`), references resources via `valueFrom`, and keeps secrets out of code; the backend README and root README document install/run/test/deploy and the BFF contract.
* Validation: `uv run pytest` → 49 passed.

## Implementation-Time Plan Updates

* None. No requirement, scope, architecture, dependency, or evidence change arose during implementation; all work followed the approved plan and resolved decisions (D1-D6). No `Guidance:` blocks were required because each task's blocks already named what later tasks consumed.

## Business Alignment

* None (no BRD/PRD/ADR cited; the plan's Sources records `no relevant business sources found`).

## Validation Record

| Check | Scope | Status | Evidence or reason |
|-------|-------|--------|--------------------|
| `uv sync --extra dev` | backend deps | Passed | Installed FastAPI, Uvicorn, Pydantic v2, LangGraph 1.x, httpx, pytest. |
| `uv run pytest` | full suite | Passed | 49 passed in ~0.3s, no live dependencies. |
| `uv run python -m app` (uvicorn) | runtime | Passed | Bound `DATABRICKS_APP_PORT`; `curl` confirmed health, `/api/incidents` (3 seeded), SSE frames, and blocked browser write. |
| `import app.main`, `import app.__main__` | import health | Passed | No import or construction errors. |
| `uv export` → `requirements.txt` | packaging | Passed | Pinned core runtime requirements generated for the Databricks App runtime. |
| Live Databricks / MCP / Genie / connector integration tests | integrations | Skipped | Out of scope by D3 (scaffold uses stubs); deferred to Follow-Up Items. |

## Pre-Review Reconciliation

* Plan markers and task-local context: current — all 7 phases and 15 tasks checked `[x]`.
* Completed-work entries and handoff prose: current — one entry per phase with files and validation.
* Validation, blockers, remaining work, and follow-up items: current — all checks recorded; no blockers; follow-ups unchanged from the plan.
* Review readiness: ready — the full-plan scope is complete and validated.

## Blockers

* None.

## Remaining Work

* None within the declared scope. Future work is tracked under Follow-Up Items (live integrations, BFF confirmation, full agent reasoning, live integration/security tests, Asset Bundle).

## Follow-Up Items

* Canonical plan list: [.copilot-tracking/plans/2026-11-05/scaffold-backend-plan.md](../../plans/2026-11-05/scaffold-backend-plan.md), `## Follow-Up Items`
* Confirm the net-new BFF contract (D5) with the backend owner before freezing it.
* Replace the stub adapters/connectors/MCP/Genie with live implementations behind the existing interfaces (`uv sync --extra live`).
* Implement full agent reasoning and production workflow logic; add live integration/security tests; wire a governed Delta audit/dead-letter store and telemetry backend; add a `databricks.yml` Asset Bundle and complete deploy-stage verification.

## Return-to-Caller State

* Implementation execution status: Complete
* Declared scope and markers: full plan (P01-P07) — all 15 tasks and 7 phases checked; no remaining active-plan markers.
* Validation coverage: 49 `pytest` tests pass; uvicorn runtime and endpoints verified; packaging locked. Live-integration tests intentionally deferred (D3).
* Blockers: none.
* Current plan updates: none.
* Business alignment entries: none.
* Planning and critique state: plan Ready; `standard` critique complete with all findings disposed (PC-001 via D6; PC-002-PC-007 corrected).
* Follow-up items: live integrations, BFF confirmation, full agent reasoning, live tests, Asset Bundle.
* Review readiness or no-handoff reason: ready for `/rpi-review`.
* Continuation owner: user (standalone).
