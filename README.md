# Scalaton AI Operations Support Co-pilot

Scalaton is an intelligent, automated AI Operations Support Co-pilot deployed as a native Databricks App. It operates inside the enterprise data perimeter and bridges infrastructure alerting (Skybot), enterprise service management (ServiceNow), engineering project management (Jira), and cross-functional team communications (Microsoft Teams).

By automating log analysis, runbook indexing, and cross-platform document drafting, this architecture shifts support staff from manual diagnostics to human-in-the-loop approvals.

## Repository layout

- [`frontend/`](frontend) — the operator console: a TypeScript + Vite + React single-page app (see [frontend/README.md](frontend/README.md)). Modeled on the [dbxmetagen](https://github.com/databricks-industry-solutions/dbxmetagen) dashboard and grounded in [`docs/`](docs).
- [`backend/`](backend) — the Python + FastAPI + LangGraph backend scaffold (see [backend/README.md](backend/README.md)). Serves the frontend's `/api/*` contract and the built `frontend/dist`, and encodes the incident workflow as a LangGraph multi-agent orchestration. Every Databricks, MCP, Genie, and connector integration sits behind a typed stub interface, so it runs with no live dependencies.
- [`docs/`](docs) — the [AI SDLC documentation index](docs/README.md), design specification, technology architecture, and governed [BRD](docs/scalaton-business-requirements-document.md), [PRD](docs/scalaton-product-requirements-document.md), and [ADR](docs/scalaton-adr-001-governed-human-in-the-loop-architecture.md).
- [`app.yaml`](app.yaml) — the deployable Databricks App manifest (runs the FastAPI backend, which serves the built frontend). [`app.yaml.example`](app.yaml.example) remains as the annotated template.
- [`databricks.yml`](databricks.yml) and [`resources/`](resources) — the Databricks Asset Bundle that deploys the app to `dev`/`qa`/`stg`/`prod`. See the [deployment guide](docs/scalaton-deployment.md).
- [`.github/workflows/`](.github/workflows) — the GitHub Actions pipeline that builds, tests, validates, and deploys the bundle with gated promotion and a production approval.

### Frontend quick start

```bash
cd frontend
npm install
npm run dev     # runs in mock mode — no backend required
```

The frontend presents the operational lifecycle (Triage → War Room → Escalation → Change Request) plus a streaming Co-pilot chat. Every AI output is a proposal awaiting explicit human approval; Microsoft Teams is the authoritative approval surface.

### Backend quick start

```bash
cd backend
uv sync --extra dev        # install dependencies
uv run python -m app       # run locally (binds DATABRICKS_APP_PORT, default 8000)
uv run pytest              # run the test suite
```

The backend runs with no live external dependencies: it seeds deterministic, spec-shaped incidents so the frontend can run in `live` mode against it same-origin. Microsoft Teams remains the authoritative approval surface; the browser console's mutating routes return `blocked`.

## Reference Architecture Topology

The architecture leverages a containerized FastAPI application running inside Databricks Apps, powered entirely by secure, native Databricks Foundation Model APIs (Mosaic AI).

| Component | Technology / Foundation Stack | Operational Purpose |
| --- | --- | --- |
| Orchestrator Brain | LangGraph Engine running on Python (FastAPI host) | Maintains session context, interprets chat text, and triggers agent actions. |
| AI Core Models | Meta Llama 3.3 70B / Mistral Large via Mosaic AI Cortex | Executes advanced SQL querying, log diagnostics, and text-to-JSON generation. |
| Knowledge Base | Mosaic AI Vector Search over Delta Tables | Hosts vector embeddings of historical ServiceNow tickets and engineering runbooks. |
| Data Governance | Unity Catalog system tables (`system.workflows`, etc.) | Natively parses execution history and lineage without data leaving the perimeter. |
| External Connectors | Secure outbound REST APIs and JWT/OAuth webhooks | Handles bidirectional syncing across ServiceNow, Jira, and MS Teams. |

## End-to-End Operational Lifecycle

### Phase 1: Automated Triage

Skybot triggers a pipeline failure and instantiates a ServiceNow incident. ServiceNow automatically sends a webhook payload to the Databricks App. The app invokes its Log Agent to fetch Spark traces, queries the Vector Search database for historical matching runbooks, and adds structured diagnostic payloads directly into the ServiceNow work notes before human assignment.

### Phase 2: War Room Mobilization

The Databricks App pushes an interactive Adaptive Card into a dedicated Microsoft Teams channel shared by IT operators, data engineers, and BI analysts. The card highlights exact schema drift variations and gives operators interactive buttons to run on-demand data quality checks natively from within Teams.

### Phase 3: Jira Escalation

When a Level 2/3 data engineer determines a permanent code fix is needed, they click **Create Jira Bug** inside Teams. The app automatically maps the contextual failure data into a linked Jira ticket, preventing any manual copy-pasting of error stacks.

### Phase 4: Change Request Automation

Once the code passes automated pipeline tests and is flagged **Passed QA** in Jira, Jira webhooks notify the Databricks App. The system drafts a comprehensive ServiceNow Change Request (CR) containing the code diff, risk assessment, and validation logs, prompting the engineering lead in Teams with a simple **Approve and Submit** button.

## Security and Perimeter Governance

Building this application on the Databricks App framework governs security through the following layers:

1. **Network isolation** — The application runs completely isolated inside your enterprise AWS VPC. It communicates through AWS PrivateLink to interact safely with on-premise or restricted firewall versions of Jira or ServiceNow.
2. **Service Principal RBAC** — The app assumes a managed Service Principal identity in Unity Catalog. It is explicitly limited to read-only access for system tables (`system.workflows`, `system.compute`) and cannot access raw transactional tables unless explicitly granted.
3. **Credential guarding** — No hardcoded API keys exist. All secrets, tokens, and webhooks are processed via the Databricks Secrets utility at run execution.
