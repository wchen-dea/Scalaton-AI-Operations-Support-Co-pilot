/**
 * Mock fixtures shaped to the design-specification.md §5 contracts and the
 * net-new console (BFF) shapes (plan D4). Used when VITE_API_MODE=mock so the
 * app runs end to end without a backend.
 */
import type {
  ChangeRequestDraft,
  DiagnosisResult,
  IncidentDetail,
  IncidentListItem,
  JiraDraft,
} from '../types/wire'

export const mockIncidents: IncidentListItem[] = [
  {
    correlation_id: 'corr-1001',
    incident_id: 'INC0012345',
    source: 'servicenow',
    severity: 'High',
    service: 'orders-etl',
    summary: 'Nightly orders pipeline failed on schema drift in orders_raw.',
    status: 'awaiting_human_review',
  },
  {
    correlation_id: 'corr-1002',
    incident_id: 'INC0012346',
    source: 'skybot',
    severity: 'Medium',
    service: 'inventory-sync',
    summary: 'Inventory sync job latency above SLO for 3 consecutive runs.',
    status: 'resolved_with_recommendation',
  },
]

const mockDiagnosis: Record<string, DiagnosisResult> = {
  'corr-1001': {
    correlation_id: 'corr-1001',
    summary:
      'orders_raw gained an unexpected column; the downstream cast failed and aborted the write.',
    probable_causes: [
      {
        description: 'Upstream source added `promo_code` without a contract update.',
        confidence: 0.82,
        evidence: ['spark_trace#AnalysisException', 'runbook#schema-drift-123'],
      },
    ],
    recommended_actions: [
      'Pin the read schema or add `promo_code` to the contract.',
      'Re-run the pipeline for the failed window.',
    ],
    unknowns: ['Whether the new column is permanent or a one-off export bug.'],
    source_references: ['runbook#schema-drift-123', 'INC0011002'],
    generated_at: '2026-11-04T09:12:00Z',
  },
  'corr-1002': {
    correlation_id: 'corr-1002',
    summary: 'Latency regression correlates with a smaller cluster after a config change.',
    probable_causes: [
      {
        description: 'Autoscaling max workers reduced in last deploy.',
        confidence: 0.64,
        evidence: ['system.compute#cluster-resize'],
      },
    ],
    recommended_actions: ['Restore prior autoscaling bounds and monitor one cycle.'],
    unknowns: ['Whether data volume also grew in the same period.'],
    source_references: ['runbook#latency-slo-7'],
    generated_at: '2026-11-04T08:40:00Z',
  },
}

export function mockIncidentDetail(correlationId: string): IncidentDetail | undefined {
  const item = mockIncidents.find((i) => i.correlation_id === correlationId)
  const diagnosis = mockDiagnosis[correlationId]
  if (!item || !diagnosis) return undefined
  return { ...item, diagnosis }
}

export function mockJiraDraft(correlationId: string): JiraDraft {
  return {
    correlation_id: correlationId,
    project: 'DATAENG',
    issue_type: 'Bug',
    summary: 'Schema drift in orders_raw breaks nightly orders pipeline',
    description:
      'Automated draft from incident context. Upstream added an unexpected column; the downstream cast failed.',
    severity: 'High',
    incident_link: 'INC0012345',
  }
}

export function mockChangeRequest(correlationId: string): ChangeRequestDraft {
  return {
    correlation_id: correlationId,
    proposed_action: 'Deploy contract update adding `promo_code` to orders_raw read schema.',
    code_change_summary: 'PR #412: add nullable `promo_code` to the orders_raw schema contract.',
    risk_assessment: 'Low — additive, nullable column; no downstream type changes.',
    test_evidence: ['CI pipeline #889 passed', 'Backfill dry-run validated 2 partitions'],
    rollback_plan: 'Revert PR #412 and re-pin the previous schema contract version.',
    affected_records: ['orders_raw', 'orders_curated'],
    evidence: ['spark_trace#AnalysisException', 'runbook#schema-drift-123'],
    linked_records: ['INC0012345', 'DATAENG-5567'],
  }
}

/** Mock co-pilot reply, chunked into deltas for the SSE path. */
export const mockCopilotReply =
  'Based on the orders-etl incident, the nightly pipeline failed because orders_raw ' +
  'gained an unexpected promo_code column. Recommended next step: update the schema ' +
  'contract or pin the read schema, then re-run the failed window.'
