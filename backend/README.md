# AI Ops Support System — Backend

A Python + FastAPI + LangGraph backend scaffold for the Agentic AI Operations Support
System. It serves the frontend's `/api/*` contract and the built `frontend/dist`, and
encodes the design's incident workflow as a LangGraph multi-agent orchestration.

It is a **scaffold**: every Databricks, MCP, Genie, and external-connector integration
sits behind a typed interface with a local stub, so the app builds, runs, and tests with
**no live external dependencies** (plan decision D3). Replacing a stub with a live
implementation is a follow-up.

## Stack

- Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- LangGraph for multi-agent orchestration (the `tech-arch §4.2` state machine)
- `uv` for dependency management

## Quick start

```bash
cd backend
uv sync --extra dev          # install dependencies
uv run python -m app         # run locally (binds DATABRICKS_APP_PORT, default 8000)
uv run pytest                # run the unit/integration test suite
```

With the server running, the frontend can run in `live` mode against it (same-origin
`/api`). In `mock` mode the frontend needs no backend.

## Layout

| Path | Responsibility |
| --- | --- |
| [`app/main.py`](app/main.py) | FastAPI app factory; wires routes and serves `frontend/dist`. |
| [`app/config.py`](app/config.py) | Single settings surface (`tech-arch §10`); no secrets in code. |
| [`app/schemas/`](app/schemas) | `design §5` contracts, BFF wire shapes, and internal models. |
| [`app/api/`](app/api) | Routes: webhooks, Teams actions, BFF `/api/*` + SSE, health. |
| [`app/orchestration/`](app/orchestration) | LangGraph graph, workflow service, dependency container. |
| [`app/agents/`](app/agents) | Log, Knowledge, Research, Diagnosis, Communication, Escalation, Change. |
| [`app/adapters/`](app/adapters) | Mosaic AI model, Vector Search, UC diagnostics, AI Functions (stubs). |
| [`app/mcp/`](app/mcp) | MCP connection layer (managed + external) and Genie integration. |
| [`app/connectors/`](app/connectors) | ServiceNow, Jira, Teams, Skybot on the `§6` adapter contract. |
| [`app/security/`](app/security) | Signatures, redaction, RBAC, idempotency, rate limiting. |
| [`app/audit/`](app/audit), [`app/reliability/`](app/reliability), [`app/observability/`](app/observability) | Audit store, retry/dead-letter/replay, logging/metrics/tracing. |
| [`tests/`](tests) | `pytest` unit and mocked-integration tests (`design §9`). |

## Workflow and approval boundary

An incident flows `received → validating → collecting_evidence → diagnosing → drafting →
awaiting_human_review` and pauses. **No production-impacting external write happens
before an explicit approval.** Microsoft Teams is the authoritative approval surface
(`design §8`, plan decision D6); the browser console is a proposal/review surface, so its
mutating `/api/*` routes return `blocked`. External writes are disabled by default.

## Configuration

All configuration comes from the environment / secret references (`tech-arch §10`); no
secrets are committed. Key flags: `ENABLE_EXTERNAL_WRITES` (default `false`),
`USE_LIVE_INTEGRATIONS` (default `false`), and the model/Vector Search/Unity Catalog/
rate-limit/Teams categories. Webhook signing secrets are read at runtime from
`{SOURCE}_WEBHOOK_SECRET`.

## The `/api/*` (BFF) contract

The backend serves the net-new browser contract the frontend targets (plan decision D5):
`GET /api/incidents`, `GET /api/incidents/{cid}`, `GET /api/escalations/{cid}/jira`,
`POST /api/escalations/{cid}/jira` (blocked — Teams authoritative),
`GET /api/change-requests/{cid}`, `POST /api/change-requests/{cid}/approve` (blocked),
and `POST /api/copilot/stream` (SSE). Confirm this contract with the backend owner before
freezing it.

## Deploy (Databricks App)

The app is served by this FastAPI backend. Deploy from the repository root (so both
`backend/` and `frontend/dist` are included) using [`../app.yaml`](../app.yaml): it runs
`python -m app` (which binds `DATABRICKS_APP_PORT`), references resources via `valueFrom`,
and keeps secrets out of code. When a `databricks.yml` is added, deploy through Asset
Bundles. Finalize the manifest with the `databricks-apps-python` and `databricks-app-design`
skills, and confirm the app is serving with `databricks apps logs <name>` before declaring
success (a deploy-stage activity, not part of this scaffold).

## Replacing stubs with live integrations

The `live` optional-dependency group lists the libraries needed when the stubs are
replaced (Databricks SDK, SQL connector, MCP client). Install with
`uv sync --extra live` and implement the live adapters behind the existing interfaces in
`app/adapters/`, `app/mcp/`, and `app/connectors/`.
