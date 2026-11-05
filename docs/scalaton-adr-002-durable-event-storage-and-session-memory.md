# ADR-SCALATON-002: Durable event storage and session memory

**Status:** Proposed for Release 2 implementation  
**Version:** 1.0  
**Date:** 2026-11-05  
**Owners:** Architecture and Engineering  
**Product:** Scalaton AI Operations Support Co-pilot  
**Business source:** BRD-SCALATON-001  
**Product source:** PRD-SCALATON-001  
**Related ADR:** ADR-SCALATON-001  

## 1. Context

Scalaton receives events from ServiceNow, Jira, Microsoft Teams, and Skybot. These events must support asynchronous processing, duplicate detection, workflow recovery, audit, authorized replay, and end-to-end traceability through a correlation ID.

Scalaton also needs session memory for active incident workflows and co-pilot conversations. Session state must survive application restarts and must not depend on process memory or browser storage. Long-term semantic memory is useful for approved incident summaries and remediation knowledge, but it is not a suitable event log or transactional system of record.

## 2. Decision

Use **Unity Catalog-governed Delta tables as the durable system of record** for inbound events, normalized events, workflow state, audit records, external actions, dead letters, and redacted session messages.

Use **Mosaic AI Vector Search as a derived semantic-memory index**, populated only from approved and redacted summaries or knowledge records. Vector Search is not authoritative and must be rebuildable from governed source tables.

Use application memory only as a short-lived cache. Do not use browser storage or an in-memory process as durable session state.

## 3. Storage model

| Data set | Storage | Required purpose |
|---|---|---|
| `bronze_inbound_events` | Unity Catalog Delta table | Immutable provider payload, receipt metadata, signature result, and source event ID |
| `silver_normalized_events` | Unity Catalog Delta table | Canonical event schema independent of provider format |
| `workflow_runs` | Unity Catalog Delta table | Current workflow status, correlation ID, incident references, and timestamps |
| `workflow_checkpoints` | Unity Catalog Delta table | Durable LangGraph checkpoints for restart and resume |
| `audit_events` | Unity Catalog Delta table | Model calls, decisions, approvals, failures, and state transitions |
| `external_actions` | Unity Catalog Delta table | Idempotency key, target system, request hash, response, and outcome |
| `dead_letter_events` | Unity Catalog Delta table | Permanently failed events awaiting authorized review and replay |
| `session_messages` | Unity Catalog Delta table | Redacted co-pilot messages and workflow conversation history |
| Mosaic AI Vector Search index | Derived index over governed Delta data | Searchable approved incident summaries, root causes, and remediation patterns |

## 4. Event-ingestion procedure

1. Receive the provider event through the FastAPI webhook boundary.
2. Validate signature, timestamp, source allowlist, minimum schema, and rate limits.
3. Assign or recover the `correlation_id` and calculate an idempotency key from source, event, target, and action context.
4. Append the original payload and receipt metadata to `bronze_inbound_events`; raw records are never overwritten.
5. Normalize the event into `silver_normalized_events`.
6. Start or resume the LangGraph workflow using the durable workflow record and checkpoint.
7. Record processing, retry, approval, connector, and failure outcomes in `audit_events`.
8. Place permanently failed events in `dead_letter_events` for authorized replay.

Duplicate events must be safely acknowledged without creating duplicate workflow actions or external records.

## 5. Session-memory model

### 5.1 Working memory

Store active workflow state and LangGraph checkpoints in Delta. Working memory includes workflow status, agent state, pending approval, source references, retry metadata, and the last processed event.

### 5.2 Conversation memory

Store redacted session messages in `session_messages` with at least:

- `session_id`
- `correlation_id`
- `actor_id` or service identity
- `role`
- `content_redacted`
- `created_at`
- `retention_until`

Only the minimum context required for the active workflow should be loaded into a model prompt.

### 5.3 Long-term semantic memory

Index approved, redacted summaries—not raw event streams—in Mosaic AI Vector Search. Examples include confirmed root causes, resolution outcomes, runbook references, and approved remediation patterns. The index must retain source references and be refreshable from Delta tables.

## 6. Alternatives considered

| Alternative | Reason not selected |
|---|---|
| Process memory as the source of truth | Lost on restart and unsafe for multi-instance deployment. |
| Browser local or session storage | Not authoritative, not suitable for sensitive data, and outside backend governance. |
| Vector Search as the event store | Optimized for retrieval, not ordering, idempotency, replay, or transactional audit. |
| One mutable JSON workflow document | Weakens lineage, concurrent-update handling, querying, retention, and auditability. |
| Separate unmanaged database as the primary store | Adds governance, network, identity, and operational complexity when Delta is already the governed platform store. |
| Redis-like cache as the primary store | Useful for latency but insufficient for durable audit, replay, and compliance. |

## 7. Consequences

### Positive

- Durable recovery across application restarts and deployments.
- Replayable, auditable, and idempotent event processing.
- One governed storage plane for event history, workflow state, and audit records.
- Clear separation between authoritative records and derived semantic memory.
- Easier retention, access control, lineage, and data-quality monitoring through Unity Catalog.

### Trade-offs

- Delta-backed checkpoints may have higher latency than an in-memory store.
- Table schemas, retention, compaction, and concurrent-write behavior require operational design.
- Vector Search refresh introduces eventual consistency for long-term memory.
- Redaction and approval rules must be enforced before records are indexed or sent to models.

## 8. Security, privacy, and retention

- Raw provider payloads must be access-controlled and retained according to source-system and enterprise policy.
- Secrets, tokens, credentials, and unnecessary personal data must be redacted before model calls, session storage, and semantic indexing.
- Unity Catalog permissions must be granted to the application service principal using least privilege.
- Session messages require explicit retention and deletion policies; semantic memory must not outlive its source authorization.
- Audit records and approval evidence must be append-only and protected from ordinary workflow actors.

## 9. Validation and operational requirements

- Test duplicate delivery, out-of-order events, restart recovery, concurrent updates, retries, timeouts, dead-lettering, and authorized replay.
- Verify that every accepted event has a correlation ID and that actions are idempotent.
- Verify that Vector Search records retain source references and can be rebuilt from Delta.
- Measure ingestion latency, checkpoint latency, replay success, dead-letter growth, session retrieval latency, and index freshness.
- Keep any cache non-authoritative and invalidate it when workflow state changes.

## 10. Follow-up decisions

- Final Unity Catalog catalog, schema, table, partitioning, clustering, and retention configuration.
- LangGraph checkpoint schema and concurrency strategy.
- Provider-specific event envelopes and canonical normalized-event schema.
- Session summarization, redaction, and token-budget policy.
- Vector Search embedding model, refresh schedule, access filters, and deletion propagation.
- Disaster recovery, backup, and cross-environment data-isolation requirements.
