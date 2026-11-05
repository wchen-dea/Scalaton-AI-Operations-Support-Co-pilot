# Scalaton — Product Requirements Document

**Document ID:** PRD-SCALATON-001
**Status:** Draft for product and engineering review
**Version:** 1.1
**Product:** Scalaton AI Operations Support Co-pilot
**Business source:** BRD-SCALATON-001
**Architecture source:** ADR-SCALATON-001

## 1. Product definition

Scalaton is a human-in-the-loop AI operations console and workflow service. It receives operational events, gathers governed evidence, generates structured recommendations, and prepares cross-platform drafts for review. The current repository is a deterministic scaffold; live external writes are disabled until the Release 2 readiness gate.

## 2. Personas and primary journeys

### Phase 1 — Automated Triage

1. Skybot and ServiceNow create the incident outside Scalaton.
2. Scalaton accepts the signed ServiceNow webhook, stores the raw payload, retrieves Spark traces and matching runbooks, and writes structured diagnostics to ServiceNow work notes.
3. The assigned operator reviews the draft before taking action.

### Phase 2 — War Room Mobilization

1. Scalaton posts an Adaptive Card to the authorized Teams channel.
2. The card highlights schema drift, runtime, or data issues with supporting evidence.

### Phase 3 — Hot Fix

1. The assigned operator uses Teams buttons to run data-quality checks, retrieve runtime configuration, or rerun the job.
2. Every action is authorized, idempotent, audited, and reflected in the workflow record.

### Phase 4 — Jira Escalation

1. A Level 2/3 data engineer selects **Create Jira Bug** in Teams.
2. Scalaton maps the contextual failure data into one linked Jira ticket without manual copy-pasting.

### Phase 5 — Record Message and Operations

1. Scalaton upserts raw/normalized events, workflow state, audit records, external actions, and redacted session context.
2. After the operator confirms the solution or fix in Teams, Scalaton updates the related ServiceNow incident and Jira ticket.
3. Ticket updates are idempotent, audited, gated by the external-write policy, and include the confirmed outcome and supporting references.
4. Approved summaries and remediation outcomes are eligible for Vector Search refresh.

### Phase 6 — Change Request Automation

1. Jira reports **Passed QA** through a webhook after automated pipeline tests pass.
2. Scalaton drafts a ServiceNow Change Request containing code diff, risk assessment, validation logs, rollback, and linked records.
3. An engineering lead reviews **Approve and Submit** in Teams.

### Engineering lead — change approval

1. After Jira reports validated QA, Scalaton drafts a ServiceNow change request.
2. The approval view shows the exact action, affected records, evidence, risk, and rollback information.
3. The engineering lead approves or rejects in Teams.
4. Only an authorized approval may submit the external change request.

## 3. Functional requirements

| ID | Requirement | Acceptance criterion | BRD trace |
|---|---|---|
| PR-001 | Receive and validate source webhooks. | Invalid signatures, stale timestamps, replays, and malformed payloads are rejected and audited. | BR-001 |
| PR-002 | Maintain incident workflow state and correlation ID. | Each workflow follows the defined states and preserves one correlation ID across agents, connectors, and audit events. | BR-002 |
| PR-003 | Generate structured diagnosis. | Output contains summary, probable causes with confidence/evidence, recommended actions, unknowns, references, and timestamp. | BR-003 |
| PR-004 | Validate model output. | Invalid or incomplete output never reaches an external system. | BR-003, BR-004 |
| PR-005 | Provide operator console. | Users can view Triage, War Room, Escalations, Change Requests, and Co-pilot surfaces; AI output is labeled as a draft. | BR-004 |
| PR-006 | Provide Teams war-room and approval cards. | Cards show proposal, affected records, evidence, risk, rollback, and current approval state. | BR-003, BR-004, BR-006 |
| PR-007 | Support authorized Jira escalation. | A confirmed action creates one idempotent linked Jira issue or returns an auditable error. | BR-005, BR-007 |
| PR-008 | Draft and submit ServiceNow change requests. | A draft includes change context, risk, validation evidence, and rollback; submission requires Teams approval. | BR-005, BR-006, BR-008 |
| PR-009 | Prevent unauthorized operational changes. | No production-impacting write, incident closure, or configured external record creation occurs without explicit authorization. | BR-005, BR-006 |
| PR-010 | Provide resilient processing. | Transient failures use bounded retries; permanent failures enter a reviewable dead-letter store; replay is authorized and audited. | BR-010 |
| PR-011 | Provide observability and auditability. | Logs, metrics, traces, and immutable audit events include correlation ID, state, latency, retries, model usage, approvals, and connector outcomes. | BR-002, BR-009 |
| PR-012 | Protect sensitive information. | Secrets and unnecessary personal or credential data are redacted before model calls and logging. | BR-003, BR-009 |
| PR-013 | Record confirmed solution operations across systems. | After Teams confirmation, the related ServiceNow incident and Jira ticket are updated once with an auditable, idempotent confirmed outcome. | BR-009, BR-010 |

## 4. Non-functional requirements

- **Security:** Signature verification, replay protection, source allowlisting, least-privilege RBAC, runtime secret retrieval, and backend authorization checks.
- **Reliability:** Idempotent event/action processing, timeouts, exponential backoff, dead-letter handling, and authorized replay.
- **Auditability:** Immutable records for inbound events, model decisions, approvals, external writes, and failures.
- **Performance:** Model, retrieval, webhook, and connector latency targets must be baselined during pilot; slow workflows must not block webhook acknowledgment.
- **Availability:** Liveness and readiness endpoints must be separate and must not expose incident data or secrets.
- **Usability:** AI output must be labeled as a draft and present evidence and uncertainty in an operator-readable format.
- **Accessibility:** Interactive status and streamed co-pilot output must be usable with keyboard navigation and assistive technology.

## 5. Product states

`received → validating → collecting_evidence → diagnosing → drafting → awaiting_human_review`

Terminal or exception states are `resolved_with_recommendation`, `rejected`, `failed`, and `dead_lettered`. State transitions must be authorized, auditable, and idempotent.

The workflow pauses at `awaiting_human_review`. Scalaton must not submit a change request, change production state, close or materially change an incident, or create a policy-controlled external record without explicit Teams approval and backend authorization.

## 6. Data and AI requirements

- Inputs may include incident metadata, approved logs, Unity Catalog workflow data, runbooks, and historical incidents.
- Retrieved content is untrusted input and must be protected against prompt injection.
- Model responses must be schema-validated before display as a formal diagnosis or transmission externally.
- The product must show source references, confidence, unknowns, and recommended human checks.
- The initial release uses Mosaic AI model APIs and Vector Search through typed adapters; the scaffold runs with deterministic stubs.

## 7. Release scope

### Release 1 — governed scaffold and workflow foundation

- React operator console and FastAPI backend.
- Typed workflow schemas and LangGraph orchestration.
- Mock/stub adapters for model, Vector Search, Unity Catalog, and external connectors.
- Validation, redaction, authorization, idempotency, audit, retry, and dead-letter controls.
- External writes disabled by default.

**Release 1 gate:** Unit, mocked integration, security, workflow, and approval-boundary tests pass.

### Release 2 — controlled integrations

- Approved live adapters for Skybot, ServiceNow, Jira, Teams, Mosaic AI, Vector Search, and Unity Catalog.
- Environment-specific service principals, secrets, endpoints, and approval policies.
- Integration and security testing with representative sanitized data.
- Approved field mappings, retention, on-call ownership, and rollback procedures.

**Release 2 gate:** Product, security, platform, and system owners approve integration readiness. External writes remain disabled until this gate passes.

## 8. Acceptance and quality gates

Release acceptance requires:

1. A representative incident can be traced end-to-end by correlation ID.
2. Duplicate, replayed, malformed, timed-out, and partially failed workflows are handled safely.
3. Model output validation, redaction, authorization, and prompt-injection tests pass.
4. No external change is submitted without an auditable human approval.
5. Mocked integration tests cover all connector boundaries.
6. Live integrations are not enabled until owners approve schemas, permissions, retention, and operational runbooks.
