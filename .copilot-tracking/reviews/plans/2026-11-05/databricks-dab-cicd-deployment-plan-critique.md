<!-- markdownlint-disable-file -->
# RPI Plan Critique: Databricks DAB deployment and GitHub Actions CI/CD

**Date:** 2026-11-05
**Plan:** [.copilot-tracking/plans/2026-11-05/databricks-dab-cicd-deployment-plan.md](../../../plans/2026-11-05/databricks-dab-cicd-deployment-plan.md)
**Mode:** standard
**Execution status:** complete (findings produced by an independent critique pass; artifact persisted by the planner because the critique agent is read-only)
**Verdict:** Revise — all findings are planner-correctable without a user decision.

## Findings

| ID | Severity | Location | Summary | Route |
|----|----------|----------|---------|-------|
| PC-001 | Blocker | P02-T01, P01-T02, P03-T02 | Per-environment variables have no concrete path into the running `app.yaml`. | Planner direct |
| PC-002 | High | P01-T01, P02-T01 | External writes not unconditionally disabled despite the PRD §7 Release 2 gate. | Planner direct |
| PC-003 | Blocker | P01-T01 contract/details | `${DEV_HOST}`-style host interpolation in `databricks.yml` is invalid/misleading. | Planner direct |
| PC-004 | Medium | P01-T02, R2 | Root `source_code_path` upload is not bounded; may upload CI/docs/tracking/local files. | Planner direct |
| PC-005 | Medium | P03-T01 | Pipeline omits the available frontend test command and does not run the full backend suite explicitly. | Planner direct |
| PC-006 | High | P03-T02 | Manual `workflow_dispatch` promotion can deploy an arbitrary ref with no provenance. | Planner direct |

## PC-001 — Per-environment runtime wiring is incomplete (Blocker)

Bundle variable substitution applies to bundle/resource YAML, not to the uploaded `app.yaml`. The plan said scalar config "resolves per target through bundle variables" without a concrete mechanism, and one `valueFrom: incident-secrets` cannot represent three distinct webhook secret keys. Resolving evidence: Databricks Apps inject attached **resources** (warehouse, serving endpoint, secret) as env vars via `valueFrom`; plain per-environment scalars must come from a per-environment secret scope (or a per-target app source) because the uploaded `app.yaml` is static.

Resolving change (owner: planner): in P02-T01 specify that (a) resource-backed values (warehouse, Genie, Vector Search index) are declared as app `resources` and injected via distinct `valueFrom` names; (b) connector webhook secrets use three distinct `valueFrom` keys in one secret scope; (c) per-environment scalars (catalog, schema, external-writes flag, approval policy) are supplied from the environment's secret scope via `valueFrom`; (d) bundle-level `--var`/`BUNDLE_VAR_*` govern bundle YAML (app name, resource IDs), not app runtime env.

## PC-002 — External-write policy contradicts the PRD gate (High)

PRD-SCALATON-001 §7: "External writes remain disabled until this [Release 2] gate passes." The plan allowed governed `stg`/`prod` enablement, which also conflicts with the plan's own non-goals. Resolving change (owner: planner): set `enable_external_writes: "false"` in all four targets; remove in-scope enablement language; leave activation to FU2 as a post-gate governed change.

## PC-003 — Workspace host contract will not work (Blocker)

`${DEV_HOST}`/`${QA_HOST}` are not valid bundle substitutions and are not replaced by exporting `DATABRICKS_HOST`. Resolving change (owner: planner): remove `workspace.host` from the committed target contract; each CI job authenticates via its GitHub Environment `DATABRICKS_HOST` + OAuth client id/secret (the CLI reads these), and local developers select a CLI profile. Optionally commit literal per-target hosts if the team prefers; do not imply shell interpolation.

## PC-004 — Root upload is insufficiently bounded (Medium)

`source_code_path: ../` correctly reaches the repo root and `sync.include: frontend/dist/**` correctly re-includes the ignored build, but inclusion is additive and does not stop `.github`, `.copilot-tracking`, `docs`, `.env*`, `.databricks`, caches, tests, `.venv`, and `node_modules` from uploading. Resolving change (owner: planner): add explicit root-relative `sync.exclude` entries for those paths in P01-T02.

## PC-005 — Frontend tests not run (Medium)

`frontend/package.json` exposes `test` (`vitest run`); P03-T01 ran only `npm run build`. Resolving change (owner: planner): run `npm test` and the full backend `pytest` suite in the build-and-test job before any deploy.

## PC-006 — Promotion lacks revision provenance (High)

`workflow_dispatch` can run from any branch/tag; the plan did not constrain the promoted ref. Resolving change (owner: planner): require promotion to run against the default branch (or an explicit commit SHA from a successful dev run), and build/test that exact SHA before deploy so qa/stg/prod receive the same validated commit.

## Verified correct

* `source_code_path: ../` is correct from `resources/scalaton.app.yml` (path resolution).
* `frontend/dist` is git-ignored; force-including it after building is necessary.
* `databricks/setup-cli` with `DATABRICKS_HOST`/`DATABRICKS_CLIENT_ID`/`DATABRICKS_CLIENT_SECRET` is valid OAuth M2M auth.
* `dev: development` and `qa/stg/prod: production` modes are appropriate; production mode does not auto-namespace app names, so explicit names and a shared `root_path` remain necessary.
* GitHub Environment required reviewers provide the intended production approval gate.
