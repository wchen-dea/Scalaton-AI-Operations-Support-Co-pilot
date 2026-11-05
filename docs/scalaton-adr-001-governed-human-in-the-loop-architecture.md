# ADR-SCALATON-001: Governed human-in-the-loop architecture

**Status:** Accepted for scaffold and pilot design
**Version:** 1.1
**Date:** 2026-11-05
**Owners:** Architecture and Engineering
**Product:** Scalaton AI Operations Support Co-pilot
**Business source:** BRD-SCALATON-001
**Product source:** PRD-SCALATON-001

## Context

Scalaton must analyze operational incidents and prepare actions across Databricks, ServiceNow, Jira, and Microsoft Teams. It handles sensitive data and may produce recommendations that affect production operations. AI output is probabilistic, external systems are asynchronous, and inbound events may be duplicated or replayed.

The architecture must support experimentation and local development while ensuring that analysis and drafting cannot silently become an operational change. The repository currently provides a buildable scaffold with typed interfaces and deterministic stubs; live integrations are a controlled follow-up.

## Decision

Adopt a governed, adapter-based architecture with the following decisions:

1. Deploy the application as a Databricks App with a Python/FastAPI boundary.
2. Use LangGraph for typed, stateful multi-agent orchestration and explicit approval pauses.
3. Use Mosaic AI Foundation Model APIs for inference and Mosaic AI Vector Search over governed Delta-backed knowledge.
4. Use Unity Catalog for governed data access and audit storage; use Databricks Secrets for credentials and signing keys.
5. Encapsulate Skybot, ServiceNow, Jira, Teams, model, Vector Search, and diagnostics behind typed interfaces.
6. Use correlation IDs, versioned schemas, idempotency keys, bounded retries, timeouts, dead-letter storage, and authorized replay.
7. Make Microsoft Teams the authoritative approval surface. The browser console is a read/proposal surface and cannot independently perform mutating actions.
8. Disable external writes by default in development and test environments.
9. Validate and redact all model-bound and externally transmitted data before use.

## 3. Architecture traceability

| Concern | Decision | PRD trace |
|---|---|---|
| Event intake | Authenticated, schema-validated webhooks | PR-001 |
| Workflow control | LangGraph state machine with approval pause | PR-002, PR-009 |
| AI inference | Mosaic AI through typed model adapter | PR-003, PR-004 |
| Knowledge retrieval | Mosaic AI Vector Search over governed data | PR-003, PR-012 |
| Governance | Unity Catalog, Databricks Secrets, least privilege | PR-012 |
| External actions | Connector layer with authorization and idempotency | PR-007, PR-008, PR-009 |
| Approval | Teams is authoritative; backend re-checks authorization | PR-006, PR-009 |
| Reliability | Timeouts, retries, dead letters, and replay | PR-010 |
| Observability | Correlation ID, metrics, traces, and immutable audit | PR-011 |

## Alternatives considered

| Alternative | Reason not selected |
|---|---|
| Autonomous agent with direct production permissions | Unsafe for probabilistic output and incompatible with required human approval. |
| Standalone cloud-hosted AI service | Increases data-perimeter, credential, and governance complexity. |
| Direct point-to-point connector calls from agents | Couples agents to external contracts and weakens authorization, retry, and audit consistency. |
| Browser as approval authority | Client visibility is not authorization; backend and Teams identity checks are required. |
| Synchronous webhook processing | Long-running diagnosis could cause timeouts and duplicate delivery; asynchronous processing is safer. |
| Model output as untyped free text | Cannot reliably validate, audit, render, or safely transmit structured decisions. |

## Consequences

### Positive

- Human approval is a structural workflow boundary rather than a UI convention.
- Data access and external actions can be independently authorized and tested.
- Stubs allow local development and deterministic testing without live dependencies.
- Correlation IDs and immutable audit events support incident reconstruction.
- Adapter boundaries allow model or provider changes without rewriting orchestration.

### Negative and trade-offs

- Teams approval integration becomes a required operational dependency.
- Typed schemas and validation add implementation effort and may reject incomplete AI output.
- Databricks-specific deployment and governance require platform expertise.
- Approval pauses can increase resolution time when responders are unavailable.
- Live connector behavior remains a follow-up until provider contracts and credentials are finalized.

## Security and operational implications

- All inbound webhooks require signature validation, timestamp freshness checks, replay protection, and source allowlisting.
- Secrets must never be committed, logged, or included in prompts.
- Retrieved runbooks, tickets, logs, and webhook fields must be treated as untrusted content.
- Approval records must include approver identity, exact action payload hash, timestamp, and resulting external record.
- Production and non-production environments require separate configuration, secrets, service principals, and endpoints.

## Validation plan

- Unit-test schema validation, signature verification, redaction, state transitions, authorization, and idempotency.
- Run mocked integration tests for all external connectors, model inference, and retrieval.
- Test replay attacks, unauthorized actions, prompt injection, secret leakage, retries, timeouts, dead letters, and approval paths.
- Verify that a representative incident is traceable end-to-end by correlation ID.
- Enable live external writes only after product, security, and system owners approve the integration readiness checklist.

## Follow-up decisions

- Final webhook schemas and authentication mechanisms.
- Unity Catalog catalogs, schemas, volumes, and service-principal grants.
- Vector Search embedding model, refresh strategy, and retention.
- Supported model endpoints, token budgets, latency targets, and evaluation dataset.
- Teams identity-to-role mapping and approval policy.
- ServiceNow/Jira field mappings, retry policy, and retention requirements.
- Production persistence and asynchronous execution implementation.
