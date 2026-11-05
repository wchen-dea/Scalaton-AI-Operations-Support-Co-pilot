# Scalaton — Product Requirements Document

**Document ID:** PRD-Scalaton-001  
**Status:** Draft for product and engineering review  
**Version:** 1.0  

## 1. Product definition

Scalaton is a human-in-the-loop AI operations console and workflow service. It receives operational events, gathers governed evidence, generates structured recommendations, and prepares cross-platform drafts for review.

## 2. Personas and primary journeys

### Operations analyst — triage

1. A signed ServiceNow, Skybot, or supported event is accepted.
2. Scalaton displays incident severity, affected service, timeline, evidence, likely causes, confidence, unknowns, and recommended next steps.
3. The analyst reviews the draft and may acknowledge or request an allowed check.

### Data/platform engineer — war room and escalation

1. Scalaton posts an incident card to the authorized Teams channel.
2. The engineer reviews evidence and performs permitted actions.
3. If remediation requires engineering work, the engineer requests a linked Jira issue.
4. The system shows the resulting Jira reference and audit trail.

### Engineering lead — change approval

1. After Jira reports validated QA, Scalaton drafts a ServiceNow change request.
2. The approval view shows the exact action, affected records, evidence, risk, and rollback information.
3. The engineering lead approves or rejects in Teams.
4. Only an authorized approval may submit the external change request.

## 3. Functional requirements

| ID | Requirement | Acceptance criterion |
|---|---|---|
| PR-001 | Receive and validate source webhooks. | Invalid signatures, stale timestamps, replays, and malformed payloads are rejected and audited. |
| PR-002 | Maintain incident workflow state. | A workflow progresses through receiving, validation, evidence collection, diagnosis, drafting, and human review without skipping approval gates. |
| PR-003 | Generate structured diagnosis. | Output contains summary, probable causes with confidence/evidence, recommended actions, unknowns, references, and timestamp. |
| PR-004 | Validate model output. | Invalid or incomplete output never reaches an external system. |
| PR-005 | Provide operator console. | Users can view Triage, War Room, Escalations, Change Requests, and Co-pilot surfaces. |
| PR-006 | Provide Teams approval cards. | Cards show proposal, affected records, evidence, risk, rollback, and current approval state. |
| PR-007 | Support authorized Jira escalation. | A confirmed action creates one idempotent linked Jira issue or returns an auditable error. |
| PR-008 | Draft ServiceNow change requests. | A draft includes code/change context, risk assessment, and validation evidence. |
| PR-009 | Enforce human approval. | No production-impacting write, incident closure, or configured external record creation occurs without explicit authorization. |
| PR-010 | Provide resilient processing. | Transient failures use bounded retries; permanent failures enter a reviewable dead-letter store. |
| PR-011 | Provide observability. | Logs, metrics, and traces include correlation ID, workflow state, latency, retries, model usage, and connector outcomes. |
| PR-012 | Protect sensitive information. | Secrets and unnecessary personal or credential data are redacted before model calls and logging. |

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

Possible terminal or exception states include `resolved_with_recommendation`, `rejected`, `failed`, and `dead_lettered`. State transitions must be authorized, auditable, and idempotent.

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

### Release 2 — controlled integrations

- Approved live adapters for Skybot, ServiceNow, Jira, Teams, Mosaic AI, Vector Search, and Unity Catalog.
- Environment-specific service principals, secrets, endpoints, and approval policies.
- Integration and security testing with representative sanitized data.

## 8. Acceptance and quality gates

Release acceptance requires:

1. A representative incident can be traced end-to-end by correlation ID.
2. Duplicate, replayed, malformed, timed-out, and partially failed workflows are handled safely.
3. Model output validation, redaction, authorization, and prompt-injection tests pass.
4. No external change is submitted without an auditable human approval.
5. Mocked integration tests cover all connector boundaries.
6. Live integrations are not enabled until owners approve schemas, permissions, retention, and operational runbooks.
