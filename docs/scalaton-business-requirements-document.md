# Scalaton — Business Requirements Document

**Document ID:** BRD-Scalaton-001  
**Status:** Draft for stakeholder review  
**Version:** 1.0  
**Product:** Scalaton AI Operations Support Co-pilot  

## 1. Executive summary

Scalaton is an AI-enabled operations support co-pilot deployed as a native Databricks App. It helps operations and engineering teams investigate incidents, retrieve relevant runbooks and historical cases, coordinate response in Microsoft Teams, and prepare ServiceNow and Jira records.

Scalaton automates analysis and drafting while preserving human control over operationally significant actions. It does not autonomously deploy code, change production state, close incidents, or submit change requests.

## 2. Business problem

Incident response currently requires manual movement among Skybot, ServiceNow, Databricks execution data, runbooks, Jira, and Microsoft Teams. This creates:

- Slow diagnosis and longer incident resolution time.
- Repeated copy-pasting of logs, evidence, and incident context.
- Inconsistent troubleshooting and escalation quality.
- Limited traceability from an alert through diagnosis, approval, remediation, and change management.
- Risk of unauthorized or insufficiently reviewed operational changes.

## 3. Objectives and measurable outcomes

| Objective | Business measure | Initial target |
|---|---|---|
| Accelerate triage | Median time from accepted incident to first useful diagnosis | Baseline, then 30% reduction |
| Improve diagnostic quality | Diagnoses containing evidence, confidence, unknowns, and next steps | ≥95% of valid workflows |
| Reduce administrative effort | Manual effort to prepare ServiceNow/Jira/Teams updates | Baseline, then 50% reduction |
| Improve governance | Production-impacting writes with recorded human approval | 100% |
| Improve traceability | Workflows traceable end-to-end by correlation ID | 100% of accepted workflows |
| Protect enterprise data | Unauthorized access or secret leakage incidents | 0 |

Targets must be baselined and approved before production launch.

## 4. Stakeholders and users

| Stakeholder | Need |
|---|---|
| Operations analyst | Rapid incident context, evidence, and recommended next steps |
| Data/platform engineer | Reliable diagnostics and linked Jira escalation |
| Engineering lead | Risk-aware change request and approval information |
| Service management team | Consistent ServiceNow updates and auditability |
| Incident manager | Teams war-room coordination and status visibility |
| Security/compliance team | Least privilege, data perimeter, approval, and audit controls |
| Executive sponsor | Reduced operational cost and improved service reliability |

## 5. Business scope

### In scope

- Receive signed incident and status events from Skybot, ServiceNow, and Jira.
- Analyze permitted Databricks execution and workflow data.
- Retrieve governed runbooks and historical incidents.
- Produce structured diagnostic summaries and recommended actions.
- Draft ServiceNow work notes and change requests.
- Post contextual Teams war-room cards.
- Create linked Jira issues after authorized operator action.
- Record approvals, external writes, failures, and workflow history.

### Out of scope

- Autonomous production deployment or rollback.
- Replacing ServiceNow, Jira, or Teams as systems of record.
- Unrestricted transactional-data access.
- Automatic incident closure or material incident changes without approval.
- Fully live external integrations in the current scaffold.

## 6. Business requirements

| ID | Requirement | Priority |
|---|---|---|
| BR-001 | The system shall accept authenticated incidents from approved sources. | Must |
| BR-002 | The system shall assign and propagate a unique correlation ID for each workflow. | Must |
| BR-003 | The system shall provide evidence-based diagnostic drafts using approved enterprise data and knowledge. | Must |
| BR-004 | The system shall clearly distinguish AI-generated drafts from approved actions. | Must |
| BR-005 | The system shall require explicit authorization before external or production-impacting writes. | Must |
| BR-006 | The system shall support Teams as the authoritative approval surface. | Must |
| BR-007 | The system shall create linked Jira escalation records when authorized. | Should |
| BR-008 | The system shall draft ServiceNow change requests after validated Jira remediation. | Should |
| BR-009 | The system shall retain immutable audit evidence for decisions and actions. | Must |
| BR-010 | The system shall fail safely through bounded retries, idempotency, and reviewable dead letters. | Must |

## 7. Business risks and mitigations

| Risk | Mitigation |
|---|---|
| Incorrect or incomplete AI diagnosis | Schema validation, evidence display, confidence, unknowns, and human review |
| Prompt injection in logs or runbooks | Treat retrieved content as untrusted; sanitize and constrain prompts |
| Unauthorized external action | Provider authentication, connector authorization, Teams approval, and backend re-checks |
| Duplicate webhook or action processing | Event/action idempotency and correlation tracking |
| Sensitive data exposure | Redaction, least privilege, secret management, private connectivity, and audit logging |
| Integration outage | Timeouts, bounded retries, dead-letter storage, and manual replay |

## 8. AI system development lifecycle mapping

| AI SDLC phase | Primary document | Gate |
|---|---|---|
| Problem alignment and feasibility | BRD | Business value, data availability, risk, and funding approved |
| Product design and data strategy | PRD | User flows, AI behavior, quality thresholds, and fallback behavior approved |
| Architecture and modeling | ADR | Technical choices, security controls, and operational consequences accepted |
| Integration and deployment | PRD + ADR | Mocked acceptance tests pass; live integrations are separately validated |
| Operations and improvement | PRD + ADR updates | Drift, quality, latency, failures, and approval metrics reviewed |

## 9. Approval criteria

Stakeholders may approve the BRD when objectives, scope, risks, success measures, and compliance constraints are accepted. Approval authorizes product definition; it does not authorize production external writes.
