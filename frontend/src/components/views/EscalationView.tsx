/**
 * Escalation view: the proposed Jira issue mapped from incident context
 * (design §4.3.2). The AI output is a proposal; submission is explicit and
 * honors the external-writes feature flag.
 */
import { useState } from 'react'
import { fetchJiraDraft, submitJiraBug, type JiraSubmitResult } from '../../api/apiClient'
import { useAsync } from '../../hooks/useAsync'
import type { JiraDraft } from '../../types/wire'
import { EmptyState, ErrorState, LoadingState } from '../StatusStates'
import { ProposalBanner } from '../ProposalBanner'

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm text-slate-200">{value}</dd>
    </div>
  )
}

export function EscalationView({ correlationId }: { correlationId: string | null }) {
  const draft = useAsync<JiraDraft>(
    () => {
      if (!correlationId) return Promise.reject(new Error('No incident selected'))
      return fetchJiraDraft(correlationId)
    },
    [correlationId],
  )
  const [result, setResult] = useState<JiraSubmitResult | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!correlationId) {
    return <EmptyState title="No incident selected" hint="Open an incident from Automated Triage first." />
  }
  if (draft.status === 'loading') return <LoadingState label="Loading Jira draft…" />
  if (draft.status === 'error') return <ErrorState message={draft.error ?? ''} />
  if (!draft.data) return <EmptyState title="No draft available" />

  async function onCreate() {
    if (!correlationId) return
    setSubmitting(true)
    try {
      setResult(await submitJiraBug(correlationId))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <ProposalBanner note="Proposed Jira issue mapped from the incident. Review the fields before creating." />
      <dl className="grid gap-4 rounded-lg border border-slate-800 bg-panel p-5 md:grid-cols-2">
        <Field label="Project" value={draft.data.project} />
        <Field label="Issue type" value={draft.data.issue_type} />
        <Field label="Severity" value={draft.data.severity} />
        <Field label="Incident" value={draft.data.incident_link} />
        <div className="md:col-span-2">
          <Field label="Summary" value={draft.data.summary} />
        </div>
        <div className="md:col-span-2">
          <Field label="Description" value={draft.data.description} />
        </div>
      </dl>

      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          onClick={onCreate}
          disabled={submitting}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? 'Creating…' : 'Create Jira Bug'}
        </button>
        {result && (
          <span
            className={
              'text-sm ' + (result.status === 'created' ? 'text-emerald-300' : 'text-amber-300')
            }
          >
            {result.status === 'created'
              ? `Created ${result.jira_key}`
              : result.reason}
          </span>
        )}
      </div>
    </div>
  )
}
