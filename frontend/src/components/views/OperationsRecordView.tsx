import { useState } from 'react'
import { runTeamsAction } from '../../api/apiClient'
import { EmptyState } from '../StatusStates'

export function OperationsRecordView({ correlationId }: { correlationId: string | null }) {
  const [message, setMessage] = useState('')
  if (!correlationId) {
    return <EmptyState title="No incident selected" hint="Open an incident from Automated Triage first." />
  }
  const selectedCorrelationId = correlationId

  async function confirmSolution() {
    const result = await runTeamsAction(selectedCorrelationId, 'confirm_solution_and_update_tickets')
    setMessage(
      result.status === 'updated'
        ? `Updated ServiceNow ${result.servicenow_id ?? ''} and Jira ${result.jira_key ?? ''}.`
        : result.reason ?? 'Ticket updates were blocked.',
    )
  }

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="text-lg font-semibold">Record Message and Operations</h2>
      <p className="text-sm text-slate-400">
        The backend upserts raw and normalized events, workflow state, audit records, and external actions. Approved summaries are eligible for Vector Search refresh.
      </p>
      <div className="rounded-lg border border-slate-800 bg-panel p-4 text-sm text-slate-300">
        Correlation ID: <span className="font-mono">{correlationId}</span>
      </div>
      <button type="button" onClick={confirmSolution} className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white">
        Confirm solution and update tickets
      </button>
      {message && <p className="text-sm text-emerald-300">{message}</p>}
    </div>
  )
}