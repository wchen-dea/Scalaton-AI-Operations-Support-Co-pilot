/**
 * Wire-contract types — the single module mirroring the backend response schema.
 *
 * Domain entity shapes are derived from docs/scalaton-design-specification.md §5
 * (Incident event, Diagnosis result). The console-facing (BFF) shapes are
 * net-new and illustrative, pending backend-owner confirmation (plan decision D4).
 *
 * Data crossing the wire is `unknown` until narrowed with the guards below; the
 * app never assumes a payload shape (no `any`).
 */

// --- design-specification.md §5 contracts ---

export type IncidentSource = 'skybot' | 'servicenow' | 'jira'

export interface IncidentEvent {
  event_id: string
  source: IncidentSource
  incident_id: string
  severity: string
  service: string
  occurred_at: string
  payload: Record<string, unknown>
  signature: string
}

export interface ProbableCause {
  description: string
  confidence: number
  evidence: string[]
}

export interface DiagnosisResult {
  correlation_id: string
  summary: string
  probable_causes: ProbableCause[]
  recommended_actions: string[]
  unknowns: string[]
  source_references: string[]
  generated_at: string
}

// --- console-facing (BFF) shapes — net-new, see plan D4 ---

/** Incident workflow status (design §4.1.7, tech-arch §4.2 states). */
export type IncidentStatus =
  | 'awaiting_human_review'
  | 'resolved_with_recommendation'
  | 'executing_approved_action'
  | 'completed'
  | 'failed'

export interface IncidentListItem {
  correlation_id: string
  incident_id: string
  source: IncidentSource
  severity: string
  service: string
  summary: string
  status: IncidentStatus
}

export interface IncidentDetail extends IncidentListItem {
  diagnosis: DiagnosisResult
}

/** Proposed Jira issue fields mapped from incident context (design §4.3.2). */
export interface JiraDraft {
  correlation_id: string
  project: string
  issue_type: string
  summary: string
  description: string
  severity: string
  incident_link: string
}

/**
 * Drafted change request: §4.4.3 draft contents plus the §8 approval-control
 * fields the UI must show (exact proposed action, affected records, evidence,
 * risk, and rollback).
 */
export interface ChangeRequestDraft {
  correlation_id: string
  proposed_action: string
  code_change_summary: string
  risk_assessment: string
  test_evidence: string[]
  rollback_plan: string
  affected_records: string[]
  evidence: string[]
  linked_records: string[]
}

/** Long-running operation handle and poll result (tech-arch §4.1 async pattern). */
export interface OperationHandle {
  task_id: string
}

export interface OperationStatus {
  task_id: string
  status: 'running' | 'done' | 'error'
  result?: unknown
  error?: string
}

// --- narrowing guards for untrusted wire data ---

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((v) => typeof v === 'string')
}

export function isDiagnosisResult(value: unknown): value is DiagnosisResult {
  if (!isRecord(value)) return false
  return (
    typeof value.correlation_id === 'string' &&
    typeof value.summary === 'string' &&
    Array.isArray(value.probable_causes) &&
    isStringArray(value.recommended_actions) &&
    isStringArray(value.unknowns) &&
    isStringArray(value.source_references)
  )
}

export function isIncidentListItem(value: unknown): value is IncidentListItem {
  if (!isRecord(value)) return false
  return (
    typeof value.correlation_id === 'string' &&
    typeof value.incident_id === 'string' &&
    typeof value.source === 'string' &&
    typeof value.summary === 'string'
  )
}
