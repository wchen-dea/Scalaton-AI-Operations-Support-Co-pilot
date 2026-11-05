<!-- markdownlint-disable-file -->
# RPI Plan Critique: Scaffold the Scalaton AI Operations Support Co-pilot frontend

## Metadata

* Task ID: scaffold-frontend
* Critique date: 2026-11-04
* Plan: .copilot-tracking/plans/2026-11-04/scaffold-frontend-plan.md
* Critique execution: Complete
* Critique depth: standard
* Depth provenance: default (no explicit user direction for deep)
* Critique type: initial
* Earlier critique: not applicable

## Inputs and Criterion Boundary

* Task context and caller requirements: Independent STANDARD readiness critique of the frontend scaffold plan. Assess against supplied evidence; do not re-plan; honor resolved decisions D1 (TSX + Vite + React + Tailwind), D2 (top-level `frontend/`), D3 (frontend-only: documented contract + mock data + dev proxy) as authoritative.
* Research and evidence considered: README.md; docs/scalaton-design-specification.md; docs/scalaton-technology-architecture.md; .copilot/instructions/react-typescript-streaming-frontend.instructions.md; .copilot/instructions/databricks-apps.instructions.md; repository file listing (git-tracked set: README.md, docs/scalaton-design-specification.md, docs/scalaton-technology-architecture.md); dbxmetagen reference patterns as described in the plan's Sources.
* Decisions, dependencies, task Goals, and task Requirements considered: D1-D3 (confirmed); FR-001..FR-010; NFR-001..NFR-005; phases P01-P05 and their tasks; plan Dependencies (illustrative API contract); Risks table.
* Assessment boundary: The critique covers the full supplied plan boundary (foundation, shell/navigation, transport/data layer, domain views, Databricks App wiring) against the actual repository evidence. It can conclude whether the plan's evidence base, contracts, and acceptance coverage are credible for implementation. It does not evaluate the dbxmetagen reference internals beyond what the plan quotes, and it does not re-open D1-D3.

## Coverage Assessment

| Requirement, research, phase, or task ID | Coverage | Evidence or concern |
|------------------------------------------|----------|---------------------|
| D1 / D2 / D3 | Covered | Confirmed user direction; not re-litigated. |
| P01-T01 (toolchain) | Partial | Vite/React/TSX/Tailwind grounded, but no test runner provisioned despite NFR-005 unit-test lock (PC-005). |
| P01-T02 (layout + env config) | Partial | Single-env-config rule sound, but config categories ignore tech-arch §10's enumerated set (PC-008). |
| P02-T01 / P02-T02 (shell + nav) | Covered | Five sections map to README lifecycle + co-pilot; References path is broken (PC-001). |
| P03-T01 (API client / wire types) | Missing | Wire types grounded on an invented contract; authoritative design-spec §5 schemas unused and real route surface contradicted (PC-002). |
| P03-T02 (SSE client) | Covered | SSE guarantees mirror the standing instruction verbatim; sound. |
| P04-T01 / P04-T02 (domain + approval views) | Partial | Approval affordance omits design-spec §8 required fields (evidence/risk/rollback); References path broken (PC-001, PC-003). |
| P04-T03 (co-pilot chat) | Partial | Streaming contract sound, but "mock stream" mechanism unspecified and in tension with dev proxy (PC-006). |
| P05-T01 (dev proxy + build) | Partial | Same-origin/dev-proxy correct; frontend-only proxy targets a non-existent backend with no mock reconciliation (PC-006). |
| P05-T02 (app definition) | Partial | Port/resource invariants captured; bespoke-Vite vs. AppKit default not reconciled (PC-007). |
| Dependencies (API contract) | Missing | Presented as "the documented backend contract"; actual documented contracts live in docs/ and differ (PC-001, PC-002). |
| Sources section | Missing | Factually states the repo contains "only README.md, the architecture .docx, and its converted Markdown" — false (PC-001). |

## Verdict

* Verdict: Revise
* Rationale: The plan's domain reasoning (lifecycle IA, SSE discipline, Databricks invariants) is sound, but it is grounded on an incorrect evidence base: it cites a non-existent architecture file, misstates the repository contents, and invents an API/wire contract while ignoring the authoritative data contracts, HITL requirements, and acceptance criteria that already exist in docs/scalaton-design-specification.md and docs/scalaton-technology-architecture.md. Those gaps materially affect P03 wire types (a core, no-`any` deliverable) and the P04 approval surfaces, so the plan needs revision before implementation.

## Findings

<!-- rpi:critique id=PC-001 -->
### PC-001 [blocking]: Plan is grounded on a non-existent architecture file and a false repository-contents claim

* Related IDs: Sources, Dependencies, P02-T02, P04-T01, P04-T02 References
* Evidence: The plan references `AI_Ops_Support_System_Architecture/AI_Ops_Support_System_Architecture.md` throughout (P02-T02, P04-T01, P04-T02 References; Sources). That path does not exist. `git ls-files` returns only `README.md`, `docs/scalaton-design-specification.md`, `docs/scalaton-technology-architecture.md`; `find . -iname '*architecture*'` returns only `docs/scalaton-technology-architecture.md`. The plan's Sources further asserts the repo "contains only `README.md`, the architecture `.docx`, and its converted Markdown" — there is no `.docx` and two distinct spec documents exist under `docs/`.
* Concern: The plan's primary architecture evidence links are all broken, and the stated source inventory is factually wrong, indicating the plan was drafted against a stale snapshot rather than the current repository. Downstream reasoning that claims to be "evidence-backed" from the architecture is not traceable to a real artifact.
* Impact: Every architecture-anchored task points at a dead reference; a reviewer or implementer cannot verify the IA, contracts, or acceptance claims. It also conceals that richer, authoritative specs (data contracts, HITL rules, acceptance criteria) were available and unused (see PC-002, PC-003).
* Smallest useful change: Re-point all architecture References to `docs/scalaton-design-specification.md` and `docs/scalaton-technology-architecture.md`, correct the Sources inventory, and re-ground P02/P03/P04 claims on those files.
* Action owner: planning parent
* Exact resolving evidence: Plan References/Sources cite `docs/scalaton-design-specification.md` and `docs/scalaton-technology-architecture.md` with valid workspace-relative links; no reference resolves to a non-existent path.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-002 -->
### PC-002 [blocking]: The "documented API contract" is invented and contradicts the real spec contracts and backend route surface

* Related IDs: Dependencies, P03-T01, D3, FR-005, NFR-002
* Evidence: The plan's Dependencies block defines an illustrative browser REST surface (`GET /api/incidents`, `GET /api/incidents/{id}`, `POST /api/operations`, `POST /api/escalations/jira`, `GET /api/change-requests/{id}`, `POST /api/copilot/stream`). The repository already documents authoritative data contracts — `docs/scalaton-design-specification.md` §5 (`Incident event`, `Diagnosis result` with `summary`, `probable_causes[]`, `recommended_actions[]`, `unknowns[]`, `source_references[]`) — and `docs/scalaton-technology-architecture.md` §4.1 defines the actual FastAPI route groups (`/webhooks/servicenow`, `/webhooks/jira`, `/webhooks/skybot`, `/actions/teams`, `/health/live`, `/health/ready`). The documented backend is webhook/action-oriented, not a browser-facing read/approve API.
* Concern: D3's frontend-only approach hinges on a "documented API contract" the data layer targets, and NFR-002/FR-005 require typed wire contracts with no `any`. The plan builds those on types it invented (`Incident`, `IncidentDetail`, `ChangeRequestDraft`) rather than the in-repo schemas, and the browser endpoints it lists do not exist in the documented backend surface — they are a net-new backend-for-frontend layer the plan never acknowledges as net-new.
* Impact: P03 wire types will mismatch the real `Diagnosis result`/`Incident event` schemas the Triage/War Room/approval views must render, guaranteeing rework; and the plan silently introduces an un-decided new API surface that diverges from the webhook/Teams architecture, which may need backend-owner agreement.
* Smallest useful change: Derive P03 wire types and the Dependencies contract from `docs/scalaton-design-specification.md` §5 schemas; explicitly label the browser read/approve/stream endpoints as a new frontend-facing (BFF) surface distinct from the documented webhook backend, and flag that surface for backend-owner confirmation.
* Action owner: planning parent (grounding types) + user/backend-owner (confirming the net-new browser API surface)
* Exact resolving evidence: P03-T01/Dependencies cite the §5 schemas as the basis for wire types, and the plan states the browser-facing endpoints are a new BFF surface pending backend-owner confirmation rather than "the documented backend contract."
* Decision route: direct planner correction for type grounding; significant/divergent user decision for introducing the new browser-facing API surface

<!-- rpi:critique id=PC-003 -->
### PC-003 [major]: Approval views under-specified against the spec's human-in-the-loop requirements and acceptance criteria

* Related IDs: P04-T02, FR-008, NFR (validation lock)
* Evidence: `docs/scalaton-design-specification.md` §8 requires approval controls to show "the exact proposed action, affected records, evidence, risk, and rollback information," and §9 requires that "no external change is submitted without an auditable approval." The plan's P04-T02 lists only "code diff, risk assessment, validation logs" for the Change Request and a generic proposal indication for Jira escalation; it omits affected-records, evidence, and rollback, and does not tie FR-008 to the §9 acceptance criterion.
* Concern: The defining product property (human-in-the-loop approval) has concrete required fields and an acceptance test in the supplied spec that the plan does not fully reflect, so the scaffolded approval surface may not express the mandated decision context.
* Impact: Placeholder approval views risk being redesigned once §8/§9 are applied; acceptance traceability for the core approval flow is missing.
* Smallest useful change: Expand P04-T02 requirements to render the §8 field set (proposed action, affected records, evidence, risk, rollback) and reference §9 acceptance (auditable approval) as the view's acceptance basis.
* Action owner: planning parent
* Exact resolving evidence: P04-T02 enumerates the §8 required approval fields and cites §9 acceptance; FR-008 maps to them.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-004 -->
### PC-004 [major]: The web-SPA operator surface is presented as evidence-backed, but the specs place the human interface in Microsoft Teams

* Related IDs: Executive Summary, P02, P04, Risks table
* Evidence: README Phases 2-4 and `docs/scalaton-design-specification.md` §4.2 describe the operator interaction surface as Microsoft Teams Adaptive Cards (war-room card with on-demand actions, "Create Jira Bug" in Teams, "Approve and Submit" in Teams). Neither spec describes a web operator console. The plan's Executive Summary and Confidence notes call the target-domain IA "evidence-backed," and the Risks table does not record that the web surface itself is net-new relative to the documented design.
* Concern: The lifecycle phases are evidenced, but the web-tab surface rendering those phases is an inference by analogy to dbxmetagen, not something the specs describe. Conflating the two overstates evidence grounding.
* Impact: Stakeholders may assume the SPA surface is specified when it is a new product decision; if the Teams-based interaction model remains authoritative, parts of the SPA scope could be redundant or need realignment.
* Smallest useful change: Add a Risks/assumptions entry stating the web operator surface is net-new versus the documented Teams-based HITL design (authorized by the user's scaffold request), and soften "evidence-backed IA" to distinguish evidenced phases from the inferred web surface.
* Action owner: planning parent
* Exact resolving evidence: Plan records the SPA surface as a net-new assumption beyond the Teams-based spec, with user authorization noted.
* Decision route: direct planner correction (user already authorized scaffolding a frontend)

<!-- rpi:critique id=PC-005 -->
### PC-005 [major]: No test runner is provisioned despite the NFR-005 pure-reducer unit-test requirement and validation lock

* Related IDs: P01-T01, P03-T02, NFR-005, Artifact Self-Check (validation lock)
* Evidence: NFR-005 and P03-T02 require the stream reducer to be "unit-testable in isolation," and the Critique Disposition's validation lock names "passing reducer unit tests" as validation evidence. P01-T01 provisions only `dev`/`build`/`preview` scripts and the Vite/React/Tailwind toolchain; no task installs or configures a test runner (e.g., Vitest), and no task adds a `test` script.
* Concern: The stated validation evidence for the plan cannot be produced because no testing capability is scaffolded.
* Impact: The acceptance signal for the plan's only unit-tested deliverable is unachievable as written, leaving NFR-005 unverifiable.
* Smallest useful change: Add a test-runner setup (Vitest or equivalent, justified per NFR-004) and a `test` script to P01-T01 or P03, so the pure reducer can be unit-tested.
* Action owner: planning parent
* Exact resolving evidence: A task provisions a test runner and `test` script; P03-T02 cites it as the reducer's unit-test harness.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-006 -->
### PC-006 [major]: Mock-data/mock-stream mechanism is unspecified and unreconciled with the frontend-only dev proxy

* Related IDs: D3, P03, P04-T03, P05-T01, FR-007, FR-008
* Evidence: D3 is frontend-only with "mock data + Vite dev proxy." P04-T01/T02 render "against mock data," P04-T03 runs "against a stub/mock stream in dev," while P05-T01 configures Vite `server.proxy` to route the API prefix "to the backend origin." Under D3 that backend does not exist, and the plan never specifies how mocks are served (in-transport mock module, MSW, or a small local mock server the proxy targets) or how the app toggles mock vs. live.
* Concern: A dev proxy needs a reachable origin; with no backend, the proxy is inert and the "mock data"/"mock SSE stream" source is undefined. FR-007 and FR-008 depend on a demonstrable mock path.
* Impact: Without a defined mock mechanism, the scaffold cannot render domain views or stream chat in dev, so the frontend-only deliverable is not demonstrable and FR-007/FR-008 are not buildable as described.
* Smallest useful change: Specify the mock strategy (e.g., a mock layer in/behind the transport module or MSW, including a mock SSE source) and state how it coexists with the dev proxy (proxy inert until the backend exists; mock layer serves in the interim; a single toggle switches them).
* Action owner: planning parent
* Exact resolving evidence: P03/P05 name the mock mechanism and the mock-vs-live toggle, and reconcile it with the dev proxy for D3.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-007 -->
### PC-007 [minor]: Bespoke-Vite choice not reconciled with the Databricks Apps AppKit default

* Related IDs: P05-T02, NFR-001
* Evidence: `.copilot/instructions/databricks-apps.instructions.md` names `databricks-apps` (AppKit: Node + TypeScript + React) as "the default for a new app" and warns that scaffolding before consulting the skill forces a rewrite. D1 authorizes a bespoke Vite + React + Tailwind app modeled on dbxmetagen, which is not AppKit. The plan loads the skill at P05-T02 but does not record the deliberate divergence from the AppKit default or its effect on `app.yaml`/`source_code_path`/build-output expectations.
* Concern: Not a re-litigation of D1 (the stack is confirmed), but the app-definition task should explicitly acknowledge the bespoke-Vite divergence so the manifest matches a non-AppKit build rather than AppKit assumptions.
* Impact: Risk of manifest/build-output mismatch at P05-T02 if AppKit scaffolding assumptions are applied to a bespoke Vite app.
* Smallest useful change: In P05-T02, note the deliberate divergence from the AppKit default and confirm the `source_code_path`/built-output and port wiring for a bespoke Vite build.
* Action owner: planning parent
* Exact resolving evidence: P05-T02 records the bespoke-Vite-vs-AppKit decision and the corresponding manifest expectations.
* Decision route: direct planner correction

<!-- rpi:critique id=PC-008 -->
### PC-008 [minor]: Environment-config module not grounded in the spec's required configuration categories

* Related IDs: P01-T02, FR-006, NFR-001
* Evidence: `docs/scalaton-technology-architecture.md` §10 enumerates required configuration categories (approved external base URLs, model endpoint names/timeouts, Vector Search index identifiers, Unity Catalog catalog/schema names, retry/rate-limit settings, Teams channel/approval-policy identifiers, feature flags with "external writes disabled by default in development and test"). P01-T02 scopes the env-config module to an API base URL only.
* Concern: The single env-config module and `.env.example` can be grounded in the real, frontend-relevant subset of §10 rather than just a base URL, improving fidelity without over-scoping backend config.
* Impact: Minor; a thin env module may need expansion once real config categories apply, but no implementation blocker.
* Smallest useful change: Reference §10 in P01-T02 and seed `.env.example` with the frontend-relevant categories (e.g., API base URL, feature flags such as mock-vs-live and external-writes-disabled defaults).
* Action owner: planning parent
* Exact resolving evidence: P01-T02 cites §10 and `.env.example` reflects the relevant categories.
* Decision route: direct planner correction

## Strengths and Residual Risk

* The SSE discipline (P03-T02) faithfully mirrors the standing streaming-frontend instruction (partial-line buffering, tolerance, de-duplication, single `AbortController`, explicit terminal states, ARIA live region) and the module-boundary separation (transport / pure reducer / env config / wire types) is correct and testable in principle.
* The Databricks App invariants (bind `DATABRICKS_APP_PORT`, `valueFrom` resources, same-origin + dev proxy over loosened CORS, generated build output) are correctly captured in P05 and NFR-001/NFR-003.
* The five-section IA (Triage, War Room, Escalation, Change Request, Co-pilot) maps cleanly to README's four phases plus the LangGraph chat surface; residual risk is the surface-grounding overstatement in PC-004, which the user's scaffold request authorizes once stated as an assumption.

## Questions or Blocking Evidence Gaps

* PC-002 raises one decision-critical question: introducing a browser-facing (BFF) API surface distinct from the documented webhook/Teams backend is a product/architecture choice the specs do not cover and may need backend-owner confirmation. The rest are direct planner corrections.

## Limitations

* The supplied task context pointed at `AI_Ops_Support_System_Architecture/AI_Ops_Support_System_Architecture.md`, which does not exist; this critique used the actual in-repo specs under `docs/` as the authoritative evidence. If a different canonical architecture source is intended, PC-001/PC-002 severity should be re-evaluated against it.
* dbxmetagen reference internals were assessed only as quoted in the plan's Sources; the external repo was not fetched.

| [.copilot-tracking/plans/2026-11-04/scaffold-frontend-plan.md](.copilot-tracking/plans/2026-11-04/scaffold-frontend-plan.md) | The implementation plan under critique |
| [docs/scalaton-design-specification.md](docs/scalaton-design-specification.md) | Authoritative data contracts (§5), HITL requirements (§8), acceptance criteria (§9) |
| [docs/scalaton-technology-architecture.md](docs/scalaton-technology-architecture.md) | FastAPI route surface (§4.1), deployment topology (§7), environment configuration (§10) |
| [README.md](README.md) | Project description and four-phase operational lifecycle |

## Next Steps

* Run `/rpi-plan` to revise the plan: disposition PC-001..PC-008, re-ground references on `docs/`, and resolve the PC-002 browser-API-surface decision (user/backend-owner input required). This is a standalone, user-owned RPI critique — no peer stage is invoked from here. Verdict: Revise.
