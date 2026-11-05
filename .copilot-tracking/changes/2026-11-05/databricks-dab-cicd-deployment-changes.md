<!-- markdownlint-disable-file -->
# RPI Changes: Databricks DAB deployment and GitHub Actions CI/CD

## Metadata

* Task ID: databricks-dab-cicd-deployment
* Related plan: [.copilot-tracking/plans/2026-11-05/databricks-dab-cicd-deployment-plan.md](../../plans/2026-11-05/databricks-dab-cicd-deployment-plan.md)
* Implementation date: 2026-11-05

## Execution Status

* Status: Complete
* Declared invocation scope: full plan
* Completed scope markers: P01, P01-T01, P01-T02, P02, P02-T01, P03, P03-T01, P03-T02, P04, P04-T01
* All remaining active-plan markers: none
* Status basis: every plan marker is checked with a changes entry and validation evidence; the bundle validates structurally, the workflows lint clean, and the CI build/test commands pass locally.

## Execution Summary

Added a Databricks Asset Bundle that deploys the existing App to `dev`/`qa`/`stg`/`prod` (separate workspaces) and a GitHub Actions pipeline that builds, tests, validates, and deploys with gated promotion and a production approval. No application behavior changed; external writes stay disabled in all environments.

## Completed Work

### Databricks Asset Bundle with four environment targets

* Related phase or task: P01 (P01-T01, P01-T02)
* Files:
  * [databricks.yml](../../../databricks.yml)
  * [resources/scalaton.app.yml](../../../resources/scalaton.app.yml)
* Behavior or functionality changed: The repository is now a deployable DAB. `databricks.yml` declares the `scalaton` bundle, `sync.include` for the git-ignored `frontend/dist/**`, `sync.exclude` bounding the root upload (CI, tracking, docs, caches, tests, dependency trees), environment variables, and four targets (`dev` development/default; `qa`/`stg`/`prod` production) with distinct `scalaton-<env>` app names and `secret_scope`. `resources/scalaton.app.yml` declares the app (`source_code_path: ..`) plus governed app resources — a SQL warehouse (`${var.warehouse_id}`, `CAN_USE`) and three `READ` webhook secrets from `${var.secret_scope}` — matching the CLI's app-resource schema.
* Validation: Passed (structural) — `databricks bundle validate -t dev`/`-t prod` resolve the bundle with no schema diagnostics; the only error is workspace authentication, which is unavailable in this environment. YAML parses for both files.

### Per-environment app configuration wired to secrets and resources

* Related phase or task: P02 (P02-T01)
* Files:
  * [app.yaml](../../../app.yaml)
* Behavior or functionality changed: The app manifest now injects `SQL_WAREHOUSE_ID` and the three `*_WEBHOOK_SECRET` values via `valueFrom` against the app resources, so per-environment IDs and secrets come from the bundle variables and secret scope rather than committed literals. `ENABLE_EXTERNAL_WRITES` is a static `false` in all environments (PRD §7 gate), and Release 2 Vector Search / Genie wiring is documented as ready-to-activate. No backend code changed — `Settings.from_env` already reads these names.
* Validation: Passed — `app.yaml` parses; env names include the activated `valueFrom` references.

### GitHub Actions build, validate, and deploy pipeline

* Related phase or task: P03 (P03-T01, P03-T02)
* Files:
  * [.github/workflows/deploy.yml](../../../.github/workflows/deploy.yml)
  * [.github/workflows/_bundle-deploy.yml](../../../.github/workflows/_bundle-deploy.yml)
* Behavior or functionality changed: A pipeline builds the frontend (`npm ci && npm run build && npm test`), tests the backend (`uv sync --extra dev && uv run pytest`), and uploads the built `frontend/dist`. On push to `main` it auto-deploys `dev`; `workflow_dispatch` promotes `qa`/`stg`/`prod` through a reusable job that runs in the matching GitHub Environment (OAuth M2M via `DATABRICKS_HOST`/`DATABRICKS_CLIENT_ID`/`DATABRICKS_CLIENT_SECRET`), downloads the validated build artifact, runs `bundle validate --strict`, `bundle deploy`, and `bundle run scalaton`. Promotion is constrained to `main`, and `prod` relies on GitHub Environment required reviewers for the human approval gate.
* Validation: Passed — `actionlint` reports no findings on both workflows; `npm test` (6 passed), `npm run build`, and `pytest` (55 passed) succeed locally.

### Deployment documentation

* Related phase or task: P04 (P04-T01)
* Files:
  * [docs/scalaton-deployment.md](../../../docs/scalaton-deployment.md)
  * [README.md](../../../README.md)
  * [docs/README.md](../../../docs/README.md)
* Behavior or functionality changed: A deployment guide documents the environment topology, per-environment prerequisites (service principal, secret scope keys, warehouse), GitHub Environment secrets, the promotion flow and production approval gate, local `bundle validate` usage, the 30-character app-name rule, and the external-write policy. The repository README and docs index link the guide and the new bundle/pipeline files.
* Validation: Passed — documentation review; links resolve to created files.

## Implementation-Time Plan Updates

### Bundle variables kept for provisioning contract

* Affected plan area or markers: P01-T01
* What changed: Declared `warehouse_id`, `genie_space`, `vector_search_index`, `uc_catalog`, `uc_schema` as bundle variables with empty defaults even though only `app_name`, `secret_scope`, and `warehouse_id` are referenced by the committed YAML.
* Why: They document the per-environment provisioning contract (critique PC-001) without forcing unsupported wiring; DABs tolerates declared-but-unused variables.
* Triggering evidence: CLI app-resource schema and the Release 1 stub stance (live Genie/Vector Search deferred).
* User answer or decision: none (local judgment)
* Reconciliation performed: P01-T01 Requirements already list these variable names; no requirement changed.
* Planning and critique state: current; no new critique needed.

## Business Alignment

* None

## Validation Record

| Check | Scope | Status | Evidence or reason |
|-------|-------|--------|--------------------|
| App-resource schema check | bundle | Passed | `databricks bundle schema` confirms `sql_warehouse {id, permission}` and `secret {scope, key, permission}` shapes used |
| `databricks bundle validate` (structural) | dev, prod | Passed | Bundle resolves with no schema diagnostics; only error is workspace auth (credentials unavailable here) |
| Live `bundle validate`/deploy | all targets | Unavailable | No workspace credentials/service principals in this environment; see FU1 prerequisites |
| `actionlint` | workflows | Passed | No findings on `deploy.yml` and `_bundle-deploy.yml` |
| Frontend build + test | frontend | Passed | `npm run build` succeeds; `vitest` 6 passed |
| Backend test suite | backend | Passed | `pytest` 55 passed |
| YAML parse | databricks.yml, app.yaml, workflows | Passed | All parse cleanly |

## Pre-Review Reconciliation

* Plan markers and task-local context: current (P01-P04 all checked)
* Completed-work entries and handoff prose: current
* Validation, blockers, remaining work, and follow-up items: current
* Review readiness: ready

## Blockers

* None

## Remaining Work

* None within declared scope. Live deploy requires the FU1 platform prerequisites.

## Follow-Up Items

* Canonical plan list: [.copilot-tracking/plans/2026-11-05/databricks-dab-cicd-deployment-plan.md](../../plans/2026-11-05/databricks-dab-cicd-deployment-plan.md), `## Follow-Up Items`
* FU1: platform-owner provisioning of workspaces, OAuth M2M service principals, secret scopes, warehouses, Genie spaces, Vector Search indexes, and the four GitHub Environments with their secrets — prerequisite for the first live deploy.
* FU2: governed change to enable external writes in `stg`/`prod` after the PRD §7 Release 2 gate.
* FU3 (hardening): pin `databricks/setup-cli@main` to a release tag or commit SHA.

## Return-to-Caller State

* Implementation execution status: Complete (full plan)
* Declared scope and markers: full plan; P01-P04 and all tasks checked; no remaining active markers
* Validation coverage: structural bundle validation, `actionlint`, and local build/test all pass; live workspace validation/deploy unavailable (FU1)
* Blockers: none
* Current plan updates: one implementation-only annotation (bundle variables kept for provisioning contract)
* Business alignment entries: none (deployment realizes PRD §7 / tech-arch §7–§10 without diverging from a cited requirement)
* Planning and critique state: plan ready; critique complete with all findings resolved
* Follow-up items: FU1 (platform provisioning), FU2 (external-writes gate), FU3 (pin CLI action)
* Review readiness or no-handoff reason: ready for `/rpi-review`
* Continuation owner: user (standalone invocation)
