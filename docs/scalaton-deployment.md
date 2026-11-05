# Scalaton — Deployment Guide (Databricks Asset Bundle + GitHub Actions)

This guide describes how Scalaton is deployed to four Databricks workspaces — `dev`,
`qa`, `stg`, and `prod` — using a Databricks Asset Bundle (DAB) and a GitHub Actions
pipeline. It governs `tech-arch §7` (separate configuration, secrets, and service
principals per environment) and `§10` (environment configuration), and honors
PRD-SCALATON-001 §7 (external writes stay disabled until the Release 2 gate).

## What is deployed

The Databricks App defined in [`../app.yaml`](../app.yaml) — the FastAPI backend that
also serves the built `frontend/dist`. The bundle files are:

- [`../databricks.yml`](../databricks.yml) — bundle name, sync rules, variables, and the
  four targets.
- [`../resources/scalaton.app.yml`](../resources/scalaton.app.yml) — the app resource
  (`source_code_path: ..`) and the governed app resources (SQL warehouse and the three
  connector webhook secrets) the app reads through `valueFrom` in `app.yaml`.

## Environment topology

Each environment is a **separate Databricks workspace** with its own host, OAuth
machine-to-machine (M2M) service principal, and secret scope. App names are
workspace-global and limited to 30 characters (lowercase letters, digits, hyphens), so
each target uses a distinct, stable name:

| Target | Bundle mode | App name | External writes |
|--------|-------------|----------|-----------------|
| `dev`  | development | `scalaton-dev`  | disabled |
| `qa`   | production  | `scalaton-qa`   | disabled |
| `stg`  | production  | `scalaton-stg`  | disabled |
| `prod` | production  | `scalaton-prod` | disabled (until the Release 2 gate) |

## Per-environment prerequisites (platform owner)

Provision these in each workspace before the first deploy:

- An OAuth M2M **service principal** with permission to deploy the bundle and manage the
  app, plus least-privilege Unity Catalog access.
- A **secret scope** named `scalaton-<env>` holding the connector webhook secrets with
  these keys: `servicenow_webhook_secret`, `jira_webhook_secret`, `skybot_webhook_secret`.
- A **serverless SQL warehouse** (its ID is supplied through the `warehouse_id` bundle
  variable).
- Unity Catalog catalog/schema and, for Release 2, the Genie space and Vector Search
  index (stubbed in Release 1).

Values that differ per environment (warehouse ID, catalog/schema, secret scope) are
supplied through bundle variables and secret references — never committed. Set non-default
bundle variables per target in `databricks.yml` or via `--var`/`BUNDLE_VAR_*` /
`.databricks/bundle/<target>/variable-overrides.json` (uncommitted).

## GitHub Environments and secrets

Create a GitHub Environment for each target (`dev`, `qa`, `stg`, `prod`). In each, set
these **environment secrets** for that workspace's service principal:

- `DATABRICKS_HOST`
- `DATABRICKS_CLIENT_ID`
- `DATABRICKS_CLIENT_SECRET`

Enable **required reviewers** on the `prod` environment so a human approves before the
production deploy runs.

## Pipeline and promotion flow

The pipeline is [`../.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) with
the reusable deploy job
[`../.github/workflows/_bundle-deploy.yml`](../.github/workflows/_bundle-deploy.yml):

1. **Build and test** (every run): `npm ci && npm run build && npm test` in `frontend`,
   and `uv sync --extra dev && uv run pytest` in `backend`. The built `frontend/dist` is
   uploaded as an artifact.
2. **Deploy dev** (automatic): on push to `main`, the pipeline deploys the `dev` target.
3. **Promote** (manual): run the workflow via **Run workflow** (`workflow_dispatch`) from
   `main` and choose `qa`, `stg`, or `prod`. The chosen environment's protection rules
   apply; `prod` requires an approval.

Each deploy job downloads the validated build artifact, runs
`databricks bundle validate --strict --target <env>`, `databricks bundle deploy --target
<env>`, and then `databricks bundle run scalaton --target <env>` to start and verify the
app. Promotions are constrained to the `main` branch so every environment receives the
same validated commit.

## Local validation

With a configured CLI profile for a target's workspace:

```bash
databricks bundle validate --strict --target dev
```

After `bundle validate`, confirm each resolved `resources.apps.scalaton.name` is at most
30 characters and uses only lowercase letters, digits, and hyphens — `bundle validate`
does not reject every invalid app name.

## External-write policy

External writes are disabled in all four environments. Enabling them in `stg`/`prod` is a
later **governed change** performed only after the PRD-SCALATON-001 §7 Release 2 readiness
gate is approved; it is out of scope for this deployment setup.
