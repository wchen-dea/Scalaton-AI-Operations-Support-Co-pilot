/**
 * Change Request view: the drafted CR (design §4.4.3) plus the §8 approval
 * controls that must show the exact proposed action, affected records, evidence,
 * risk, and rollback. Only an explicit approval submits; the control honors the
 * external-writes feature flag.
 */
import { useState } from 'react'
import {
  approveChangeRequest,
  fetchChangeRequest,
  type ApprovalResult,
} from '../../api/apiClient'
import { useAsync } from '../../hooks/useAsync'
import type { ChangeRequestDraft } from '../../types/wire'
import { EmptyState, ErrorState, LoadingState } from '../StatusStates'
import { ProposalBanner } from '../ProposalBanner'

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-800 p-4">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      <div className="text-sm text-slate-200">{children}</div>
    </section>
  )
}

export function ChangeRequestView({ correlationId }: { correlationId: string | null }) {
  const draft = useAsync<ChangeRequestDraft>(
    () => {
      if (!correlationId) return Promise.reject(new Error('No incident selected'))
      return fetchChangeRequest(correlationId)
    },
    [correlationId],
  )
  const [result, setResult] = useState<ApprovalResult | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!correlationId) {
    return <EmptyState title="No incident selected" hint="Open an incident from Automated Triage first." />
  }
  if (draft.status === 'loading') return <LoadingState label="Loading change request…" />
  if (draft.status === 'error') return <ErrorState message={draft.error ?? ''} />
  if (!draft.data) return <EmptyState title="No change request draft" />

  const cr = draft.data

  async function onApprove() {
    if (!correlationId) return
    setSubmitting(true)
    try {
      setResult(await approveChangeRequest(correlationId))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl space-y-4">
      <ProposalBanner note="Drafted change request. Review the proposed action, risk, and rollback before approving." />

      <Block title="Proposed action">{cr.proposed_action}</Block>

      <div className="grid gap-4 md:grid-cols-2">
        <Block title="Code change summary">{cr.code_change_summary}</Block>
        <Block title="Risk assessment">{cr.risk_assessment}</Block>
        <Block title="Affected records">
          <ul className="list-disc pl-5">
            {cr.affected_records.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </Block>
        <Block title="Rollback plan">{cr.rollback_plan}</Block>
        <Block title="Evidence">
          <ul className="list-disc pl-5">
            {cr.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </Block>
        <Block title="Test evidence">
          <ul className="list-disc pl-5">
            {cr.test_evidence.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </Block>
      </div>

      <Block title="Linked records">{cr.linked_records.join(', ')}</Block>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onApprove}
          disabled={submitting}
          className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? 'Submitting…' : 'Approve and Submit'}
        </button>
        {result && (
          <span
            className={
              'text-sm ' + (result.status === 'submitted' ? 'text-emerald-300' : 'text-amber-300')
            }
          >
            {result.status === 'submitted'
              ? `Submitted ${result.servicenow_id}`
              : result.reason}
          </span>
        )}
      </div>
    </div>
  )
}
