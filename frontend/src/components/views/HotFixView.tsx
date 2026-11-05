import { useState } from 'react'
import { runTeamsAction } from '../../api/apiClient'
import { EmptyState } from '../StatusStates'

export function HotFixView({ correlationId }: { correlationId: string | null }) {
  const [message, setMessage] = useState('')

  if (!correlationId) {
    return <EmptyState title="No incident selected" hint="Open an incident from Automated Triage first." />
  }
  const selectedCorrelationId = correlationId

  async function run(action: 'run_data_quality_check' | 'get_runtime_configuration' | 'rerun_pipeline') {
    const result = await runTeamsAction(selectedCorrelationId, action)
    setMessage(result.reason ?? `Action ${action} accepted through Teams.`)
  }

  return (
    <div className="max-w-3xl space-y-4">
      <h2 className="text-lg font-semibold">Hot Fix Operations</h2>
      <p className="text-sm text-slate-400">
        Actions are proposed here; Teams identity checks and backend policy remain authoritative.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => run('run_data_quality_check')} className="rounded-md border border-slate-700 px-3 py-2 text-sm">Run data-quality check</button>
        <button type="button" onClick={() => run('get_runtime_configuration')} className="rounded-md border border-slate-700 px-3 py-2 text-sm">Get runtime configuration</button>
        <button type="button" onClick={() => run('rerun_pipeline')} className="rounded-md border border-slate-700 px-3 py-2 text-sm">Rerun pipeline</button>
      </div>
      {message && <p className="text-sm text-emerald-300">{message}</p>}
    </div>
  )
}