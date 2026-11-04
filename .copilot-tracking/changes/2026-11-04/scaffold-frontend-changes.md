<!-- markdownlint-disable-file -->
# RPI Changes: Scaffold the AI Ops Support System frontend

## Metadata

* Task ID: scaffold-frontend
* Related plan: [.copilot-tracking/plans/2026-11-04/scaffold-frontend-plan.md](../../plans/2026-11-04/scaffold-frontend-plan.md)
* Implementation date: 2026-11-04

## Execution Status

* Status: Complete
* Declared invocation scope: full plan
* Completed scope markers: P01 (P01-T01, P01-T02), P02 (P02-T01, P02-T02), P03 (P03-T01, P03-T02), P04 (P04-T01, P04-T02, P04-T03), P05 (P05-T01, P05-T02)
* All remaining active-plan markers: none
* Status basis: every in-scope `Pxx` and `Pxx-Txx` is checked with a changes-record entry; build, unit tests, lint, and a preview-serve check all pass.

## Execution Summary

Scaffolded a TypeScript + Vite + React + Tailwind frontend at `frontend/`, grounded on the `docs/` specifications. It provides an app shell with lifecycle navigation (Triage, War Room, Escalations, Change Requests, Co-pilot), a typed transport/data layer (wire types from design-spec §5, a pure/tested SSE reducer, and an env-selected mock layer), placeholder domain views that express the human-in-the-loop proposal/approval pattern (including the §8 approval fields), a streaming co-pilot chat, and Databricks App build/deploy wiring (same-origin dev proxy, build-not-commit output policy, manifest template, and operator docs). The app builds and runs in mock mode without a backend.

## Completed Work

One entry per completed plan item, under a descriptive heading.

### Frontend project foundation and toolchain

* Related phase or task: P01-T01
* Files:
  * [frontend/package.json](../../../frontend/package.json)
  * [frontend/vite.config.ts](../../../frontend/vite.config.ts)
  * [frontend/tailwind.config.js](../../../frontend/tailwind.config.js)
  * [frontend/postcss.config.js](../../../frontend/postcss.config.js)
  * [frontend/src/index.css](../../../frontend/src/index.css)
  * [frontend/index.html](../../../frontend/index.html)
* Behavior or functionality changed: A buildable Vite + React 19 + TypeScript app now exists at `frontend/` with Tailwind CSS + PostCSS + autoprefixer active and a Vitest-backed `test` script. `package.json` exposes `dev`, `build`, `preview`, `test`, and `test:watch`. The Vite config adds a dev-server `/api` proxy (live mode) and Vitest `test` settings. The demo template content and unused assets were removed.
* Validation: `npm run build` passed (`tsc -b && vite build`, 16 modules, Tailwind CSS emitted); `npm audit` reports 0 vulnerabilities after upgrading Vitest to the non-vulnerable 4.x major.

### Directory layout and environment-config module

* Related phase or task: P01-T02
* Files:
  * [frontend/src/config/env.ts](../../../frontend/src/config/env.ts)
  * [frontend/.env.example](../../../frontend/.env.example)
  * `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/utils/`, `frontend/src/api/`, `frontend/src/types/`, `frontend/src/mocks/`, `frontend/public/`
* Behavior or functionality changed: The project exposes the reference layout (`components/`, `hooks/`, `utils/`, plus `api/`, `config/`, `types/`, `mocks/`, `public/`). A single `src/config/env.ts` is the only reader of `import.meta.env`; it exposes a typed `env` object with a single `apiBaseUrl` (all endpoints derive from it), an `apiMode` (`mock|live`, default `mock`), and an `enableExternalWrites` flag (default off). `.env.example` mirrors every variable with defaults, seeded from technology-architecture §10 frontend-relevant categories.
* Validation: covered by the P01 build; no module other than `env.ts` reads `import.meta.env`.

### Application shell and lifecycle navigation

* Related phase or task: P02-T01, P02-T02
* Files:
  * [frontend/src/App.tsx](../../../frontend/src/App.tsx)
  * [frontend/src/components/AppShell.tsx](../../../frontend/src/components/AppShell.tsx)
  * [frontend/src/components/Navigation.tsx](../../../frontend/src/components/Navigation.tsx)
  * [frontend/src/components/StatusStates.tsx](../../../frontend/src/components/StatusStates.tsx)
  * [frontend/src/types/sections.ts](../../../frontend/src/types/sections.ts)
* Behavior or functionality changed: The app now renders a persistent shell (branded header, lifecycle navigation, main content region) and lets an operator switch between the five lifecycle sections — Triage, War Room, Escalations, Change Requests, and Co-pilot — with the active section held as React state (no router dependency). Section identity is a typed `SectionId` union with a single `SECTIONS` source of truth, so navigation and views cannot drift. Shared, visually distinguishable loading/error/empty state components are provided for reuse by section views. Section bodies currently render a placeholder pending P04.
* Validation: `npm run build` passed (20 modules; Tailwind CSS emitted).

### Transport and data layer (client, cache, wire types, mock layer)

* Related phase or task: P03-T01
* Files:
  * [frontend/src/types/wire.ts](../../../frontend/src/types/wire.ts)
  * [frontend/src/api/apiClient.ts](../../../frontend/src/api/apiClient.ts)
  * [frontend/src/mocks/fixtures.ts](../../../frontend/src/mocks/fixtures.ts)
* Behavior or functionality changed: All backend communication now flows through one `apiClient` module with typed endpoint functions and a short-TTL read cache; components never call `fetch`. Wire types mirror the design-spec §5 contracts (`IncidentEvent`, `DiagnosisResult`) with narrowing guards so wire data is `unknown` until validated (no `any`). The console-facing shapes (incident list/detail, Jira draft, change-request draft with §8 fields) are typed and labeled net-new (D4). A single `VITE_API_MODE` flag selects an in-memory mock layer (default) or the live backend reached same-origin via `env.apiBaseUrl`; mutating endpoints honor the external-writes feature flag and return a blocked result when writes are disabled.
* Validation: covered by the P03 build; mock mode returns §5-shaped fixtures.

### Pure SSE reducer and streaming client

* Related phase or task: P03-T02
* Files:
  * [frontend/src/api/sseReducer.ts](../../../frontend/src/api/sseReducer.ts)
  * [frontend/src/api/sseReducer.test.ts](../../../frontend/src/api/sseReducer.test.ts)
  * [frontend/src/api/streamClient.ts](../../../frontend/src/api/streamClient.ts)
* Behavior or functionality changed: The co-pilot stream is split into a pure reducer (events → chat state, no I/O) and a transport client. The reducer appends deltas, drops replays by seen event ID and by a trailing-text check, records error messages, and exposes distinct terminal states (`done`/`error`/`cancelled`/`truncated`). The stream client owns `fetch` + `getReader()` + `TextDecoder`, buffers the trailing partial line, tolerates unparseable frames, honors a single `AbortSignal` for timeout and cancel, and emits `cancelled`/`error` explicitly; a mock stream produces the same event shape locally.
* Validation: `npm test` passed (6 reducer unit tests: delta append, id-replay dedup, trailing-text dedup, terminal states, error message, `isTerminal`).

### Triage and War Room views

* Related phase or task: P04-T01
* Files:
  * [frontend/src/components/views/TriageView.tsx](../../../frontend/src/components/views/TriageView.tsx)
  * [frontend/src/components/views/WarRoomView.tsx](../../../frontend/src/components/views/WarRoomView.tsx)
  * [frontend/src/hooks/useAsync.ts](../../../frontend/src/hooks/useAsync.ts)
* Behavior or functionality changed: Triage renders the incident queue (incident ID, service, severity, AI summary, workflow status) and opening an incident lifts its correlation ID to the shell and navigates to the War Room. War Room renders the selected incident's §5 `Diagnosis result` (summary, probable causes with confidence and evidence, recommended actions, unknowns, source references) and non-destructive operator-check placeholders; destructive actions are excluded. Both consume data only through the `apiClient` via a shared `useAsync` hook and render the shell's loading/error/empty states.
* Validation: `npm run build` passed (33 modules); `npm run preview` served the app (HTTP 200).

### Escalation and Change Request approval views

* Related phase or task: P04-T02
* Files:
  * [frontend/src/components/views/EscalationView.tsx](../../../frontend/src/components/views/EscalationView.tsx)
  * [frontend/src/components/views/ChangeRequestView.tsx](../../../frontend/src/components/views/ChangeRequestView.tsx)
  * [frontend/src/components/ProposalBanner.tsx](../../../frontend/src/components/ProposalBanner.tsx)
* Behavior or functionality changed: Escalation renders the proposed Jira issue fields (§4.3.2) with a proposal banner and a "Create Jira Bug" control. Change Request renders the drafted CR (§4.4.3) and the §8 approval controls — proposed action, affected records, evidence, risk, and rollback — with an explicit "Approve and Submit" control. Both make the proposal/approval boundary explicit; submission honors the external-writes feature flag and surfaces a blocked message when writes are disabled (the default). Generated text renders as escaped React text; no `dangerouslySetInnerHTML` is used.
* Validation: covered by the P04 build and preview.

### Co-pilot chat view

* Related phase or task: P04-T03
* Files:
  * [frontend/src/components/views/CopilotChatView.tsx](../../../frontend/src/components/views/CopilotChatView.tsx)
* Behavior or functionality changed: The chat sends a prompt and renders streamed assistant deltas incrementally into an ARIA live region through the pure reducer and the SSE client. The current status and terminal states (done/error/cancelled/truncated) are visually distinguishable, and a cancel control triggers the shared `AbortController`. The view holds no transport or parsing logic. In mock mode it exercises the full streaming contract without a backend.
* Validation: covered by the P04 build and the reducer unit tests.

### Same-origin dev proxy and build-output policy

* Related phase or task: P05-T01
* Files:
  * [frontend/vite.config.ts](../../../frontend/vite.config.ts)
  * [frontend/.gitignore](../../../frontend/.gitignore)
* Behavior or functionality changed: The Vite dev server proxies `/api` to the backend origin (`VITE_DEV_PROXY_TARGET`) for live mode; production requests stay same-origin with no loosened CORS. The proxy and the mock layer are reconciled by the single `VITE_API_MODE` flag (default `mock`, so the dev server runs without a backend). The build output `dist/` is git-ignored: this repository builds the output in CI/deploy rather than committing it (the opposite of the dbxmetagen reference), and sources are edited then rebuilt — never hand-patched.
* Validation: `npm run build` produces `dist/`; `npm run preview` served it at HTTP 200.

### Databricks App manifest template and operator docs

* Related phase or task: P05-T02
* Files:
  * [app.yaml.example](../../../app.yaml.example)
  * [frontend/README.md](../../../frontend/README.md)
  * [README.md](../../../README.md)
* Behavior or functionality changed: A clearly-marked `app.yaml.example` documents the Databricks App manifest — port binding to `DATABRICKS_APP_PORT`, resource references via `valueFrom`, minimum OBO scopes, and Asset Bundle deployment — as a scaffold template. The frontend README documents install/dev/build/preview/test, the env-config contract, the data layer, the build-output policy, and deployment; the root README gains a repository-layout and frontend quick-start section. The manifest is intentionally not finalized because the Python/FastAPI backend it runs is out of scope (D3).
* Validation: `npm run build` and `npm test` pass; `npm run lint` exits 0 (one benign generic-hook warning in `useAsync`).

## Implementation-Time Plan Updates

### Databricks manifest finalization deferred to backend work

* Affected plan area or markers: P05-T02
* What changed: Produced `app.yaml.example` as a documented template rather than a finalized, deployable `app.yaml`, and gated manifest finalization (with the `databricks-apps-python` and `databricks-app-design` skills) on the FastAPI backend landing.
* Why: The manifest's `command` runs the backend, which is explicitly out of scope (D3). Finalizing a deployable manifest now would be premature and untestable. The databricks-apps invariants (port, `valueFrom`, resources, Asset Bundles) are captured in the template and docs so finalization is mechanical later.
* Triggering evidence: plan D3 (frontend-only); `dist` is git-ignored (build-not-commit).
* User answer or decision: none (consistent with confirmed D3).
* Reconciliation performed: recorded here; mirrored in the plan Follow-Up Items (backend/BFF).
* Planning and critique state: not needed.

### Toolchain versions newer than the plan's reference

* Affected plan area or markers: P01-T01
* What changed: The scaffold uses the current `npm create vite` `react-ts` template, which pins Vite 8, React 19.3, TypeScript 7, and oxlint, rather than the reference repo's Vite 6. Vitest 4 was selected over 3 to clear dev-only advisories.
* Why: The plan directed using the toolchain's own scaffolding; the current template major is newer than the dbxmetagen reference but satisfies the same intent (Vite + React + TS + Tailwind). Vitest 4 removes the only reported vulnerabilities.
* Triggering evidence: `create-vite@9.3.3` output; `npm audit` flagged `@vitest/mocker`/`tinypool` in Vitest 3, resolved in 4.
* User answer or decision: none (implementation-only annotation; no requirement or design change).
* Reconciliation performed: recorded here only; plan requirements remain satisfied.
* Planning and critique state: not needed.

## Business Alignment

* None. The `docs/` specifications are design/architecture documents, not BRD/PRD/ADR business sources with identifiers; tasks cite them by section (`§n`) rather than as business-source requirement IDs. No cited business-source requirement changed or diverged.

## Validation Record

| Check | Scope | Status | Evidence or reason |
|-------|-------|--------|--------------------|
| `npm run build` (`tsc -b && vite build`) | full frontend | Passed | 33 modules transformed; `dist/` emitted with Tailwind CSS |
| `npm test` (Vitest) | pure SSE reducer | Passed | 6/6 tests: delta append, id-replay dedup, trailing-text dedup, terminal states, error message, `isTerminal` |
| `npm run lint` (oxlint) | full frontend | Passed | Exit 0; one benign generic-hook `exhaustive-deps` warning in `useAsync` |
| `npm run preview` serve check | built app | Passed | HTTP 200, `<title>AI Ops Support System</title>` |
| `npm audit` | dependencies | Passed | 0 vulnerabilities after Vitest 4 upgrade |

## Pre-Review Reconciliation

* Plan markers and task-local context: current — all P01-P05 phase and task markers checked; task blocks unchanged except recorded annotations.
* Completed-work entries and handoff prose: current — one entry per completed task, tied to its marker.
* Validation, blockers, remaining work, and follow-up items: current — see Validation Record; no blockers; no in-scope remaining work; follow-ups mirrored below.
* Review readiness: ready for optional `/rpi-review`.

## Blockers

* None

## Remaining Work

* None within the declared full-plan scope. All downstream work (FastAPI backend/BFF, real integrations, full view features, integration/security/a11y tests) is in Follow-Up Items, outside this scaffold's scope.

## Follow-Up Items

* Canonical plan list: [.copilot-tracking/plans/2026-11-04/scaffold-frontend-plan.md](../../plans/2026-11-04/scaffold-frontend-plan.md), `## Follow-Up Items`
* Confirm the net-new BFF `/api/*` contract (plan D4) with the backend owner.
* Implement the FastAPI backend + LangGraph orchestrator behind the confirmed contract, then finalize `app.yaml` with the `databricks-apps-python` and `databricks-app-design` skills.
* Build out full view features (charts/graphs/onboarding) and real ServiceNow/Jira/Teams integrations.
* Add integration, security, and accessibility tests once live endpoints exist.

## Return-to-Caller State

* Implementation execution status: Complete (full-plan scope)
* Declared scope and markers: full plan; all markers P01-P05 completed; none remaining
* Validation coverage: build, 6 unit tests, lint, preview-serve, and audit all pass
* Blockers: none
* Current plan updates: two implementation-only annotations (newer toolchain versions; Databricks manifest finalization deferred to backend work) — no requirement/design changes
* Business alignment entries: none (specs are design/architecture sources, cited by section)
* Planning and critique state: plan Ready; standard critique complete with all findings disposed; D4 open (non-blocking)
* Follow-up items: BFF contract confirmation, FastAPI backend, full features/integrations, broader tests
* Review readiness or no-handoff reason: ready for optional `/rpi-review`
* Continuation owner: user (standalone)
