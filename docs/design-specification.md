# Agentic AI Operations Support System — Design Specification

## 1. Purpose

This document defines the target design for an AI operations support co-pilot deployed as a native Databricks App. The system automates incident triage and cross-platform support workflows while keeping human approval for operationally significant actions.

## 2. Goals and non-goals

### Goals

- Receive infrastructure and application incidents from Skybot and ServiceNow.
- Diagnose failures using execution logs, Unity Catalog metadata, and indexed runbooks.
- Draft structured updates for ServiceNow incidents and Microsoft Teams war rooms.
- Create linked Jira issues when engineering remediation is required.
- Draft ServiceNow change requests after Jira validation and request explicit approval.
- Keep data, model calls, credentials, and audit records inside the enterprise perimeter where possible.

### Non-goals

- Automatically deploying code or production changes.
- Replacing ServiceNow, Jira, or Microsoft Teams as the system of record.
- Granting the agent unrestricted access to transactional data or operational systems.
- Treating model output as an approved change without human confirmation.

## 3. High-level architecture

| Component | Technology | Responsibility |
| --- | --- | --- |
| Application host | Databricks Apps with FastAPI | Exposes webhooks, chat/action endpoints, and health checks. |
| Orchestrator | LangGraph on Python | Maintains workflow state, routes tasks, and enforces approval pauses. |
| AI layer | Mosaic AI Foundation Model APIs | Performs log analysis, classification, extraction, and draft generation. |
| Knowledge base | Mosaic AI Vector Search over Delta tables | Retrieves related incidents, runbooks, and remediation guidance. |
| Governance data | Unity Catalog system tables | Provides governed workflow and execution metadata. |
| External connectors | REST APIs and JWT/OAuth webhooks | Integrates with Skybot, ServiceNow, Jira, and Microsoft Teams. |
| Secret storage | Databricks Secrets | Stores API credentials, signing keys, and webhook secrets. |

The application must use a correlation ID for every incident workflow. The ID is propagated to model calls, connector requests, audit events, and user-facing messages.

## 4. Core workflows

### 4.1 Incident triage

1. ServiceNow sends a signed incident webhook containing the incident ID, severity, affected service, and source event.
2. The application validates the request, creates a correlation ID, and records an audit event.
3. The log agent retrieves permitted Spark and workflow diagnostics.
4. The knowledge agent retrieves relevant runbooks and historical incidents from Vector Search.
5. The orchestrator asks the model to produce a structured diagnosis:
   - symptoms and timeline;
   - likely cause and confidence;
   - supporting evidence;
   - recommended next steps;
   - unknowns and required human checks.
6. The application writes a concise, clearly labelled draft to ServiceNow work notes.
7. The workflow status becomes `awaiting_human_review` or `resolved_with_recommendation`; it must not silently close an incident.

### 4.2 Teams war room

1. The application posts an Adaptive Card containing incident context, diagnosis, evidence, and confidence.
2. Authorized operators can request permitted data-quality checks or acknowledge the diagnosis.
3. Each action is authorized, idempotent, logged, and reflected in the card.
4. Destructive or production-changing actions are excluded from the initial action set.

### 4.3 Jira escalation

1. An authorized operator selects **Create Jira Bug**.
2. The application displays or validates the mapped project, issue type, summary, description, severity, and incident link.
3. The connector creates or reuses an issue using an idempotency key derived from the incident and action ID.
4. The Jira key and URL are written back to ServiceNow and Teams.

### 4.4 Change request drafting

1. A Jira webhook reports that the remediation has passed QA.
2. The application verifies the webhook and correlates it with the original incident.
3. The change agent drafts a ServiceNow change request containing the code-change summary, risk assessment, test evidence, rollback plan, and linked records.
4. The draft is presented in Teams to an authorized engineering lead.
5. Only an explicit approval may submit the change request. The approval identity, timestamp, payload hash, and resulting ServiceNow ID are audited.

## 5. Data contracts

### Incident event

```json
{
  "event_id": "string",
  "source": "skybot|servicenow|jira",
  "incident_id": "string",
  "severity": "string",
  "service": "string",
  "occurred_at": "ISO-8601 timestamp",
  "payload": {},
  "signature": "string"
}
```

### Diagnosis result

```json
{
  "correlation_id": "string",
  "summary": "string",
  "probable_causes": [
    {"description": "string", "confidence": 0.0, "evidence": ["string"]}
  ],
  "recommended_actions": ["string"],
  "unknowns": ["string"],
  "source_references": ["string"],
  "generated_at": "ISO-8601 timestamp"
}
```

Model output must be schema-validated before it is sent to any external system. Invalid or incomplete output is retained as an internal error and requires human handling.

## 6. Security and governance

- Authenticate inbound webhooks with signature validation, timestamp checks, replay protection, and allowlisted sources.
- Use a Databricks App service principal with least-privilege Unity Catalog permissions.
- Default system-table access to read-only; grant transactional-table access only when explicitly required and approved.
- Retrieve credentials at runtime from Databricks Secrets; never commit secrets or include them in prompts or logs.
- Redact tokens, credentials, personal data, and unnecessary incident payload fields before model calls.
- Enforce connector-specific authorization for every user action.
- Store immutable audit records for inbound events, model decisions, external writes, approvals, and failures.
- Use private connectivity such as AWS PrivateLink where required by the enterprise network boundary.

## 7. Reliability and operations

- Make webhook processing idempotent using `event_id` and action IDs.
- Apply bounded retries with exponential backoff for transient connector and model errors.
- Send permanently failed events to a reviewable dead-letter store.
- Apply timeouts to model, Vector Search, and external API calls.
- Expose health and readiness endpoints without revealing secrets or incident data.
- Track latency, success rate, retry count, model usage, approval wait time, and connector failures.
- Support manual replay only from an authorized operational interface.

## 8. Human-in-the-loop requirements

The application may analyze, summarize, and draft. It must pause for explicit human approval before:

- submitting a ServiceNow change request;
- changing production state;
- closing or materially changing an incident;
- creating external records when the configured policy requires confirmation.

Approval controls must show the exact proposed action, affected records, evidence, risk, and rollback information.

## 9. Testing and acceptance criteria

- Unit tests cover payload validation, signature verification, redaction, state transitions, and idempotency.
- Integration tests use mocked ServiceNow, Jira, Teams, Skybot, Vector Search, and model endpoints.
- Security tests cover replay attacks, unauthorized actions, prompt injection in retrieved documents, and secret leakage.
- Workflow tests verify retry, timeout, duplicate-event, partial-failure, and approval paths.
- Acceptance requires that a representative incident can be traced end-to-end using its correlation ID and that no external change is submitted without an auditable approval.

## 10. Open implementation decisions

- Final webhook schemas and authentication mechanisms for each source.
- Required Unity Catalog catalogs, schemas, volumes, and service-principal grants.
- Vector Search embedding model, index refresh strategy, and retention policy.
- Supported model endpoints, token budgets, and response-time targets.
- Teams identity-to-role mapping and approval policy.
- ServiceNow and Jira field mappings, retry policy, and record retention requirements.