/**
 * War Room view: the selected incident's diagnosis context (design §4.2, §5
 * Diagnosis result) with permitted, non-destructive operator action affordances.
 * Destructive/production-changing actions are intentionally excluded (§4.2.4);
 * Teams-side role re-checks remain authoritative (§8).
 */
import { fetchIncidentDetail } from '../../api/apiClient'
import { useAsync } from '../../hooks/useAsync'
import type { IncidentDetail } from '../../types/wire'
import { EmptyState, ErrorState, LoadingState } from '../StatusStates'

interface WarRoomViewProps {
  correlationId: string | null
}

export function WarRoomView({ correlationId }: WarRoomViewProps) {
  const detail = useAsync<IncidentDetail>(
    () => {
      if (!correlationId) return Promise.reject(new Error('No incident selected'))
      return fetchIncidentDetail(correlationId)
    },
    [correlationId],
  )

  if (!correlationId) {
    return <EmptyState title="No incident selected" hint="Open an incident from Automated Triage." />
  }
  if (detail.status === 'loading') return <LoadingState label="Loading incident…" />
  if (detail.status === 'error') return <ErrorState message={detail.error ?? ''} />
  if (!detail.data) return <EmptyState title="Incident unavailable" />

  const { diagnosis } = detail.data

  return (
    <div className="space-y-5">
      <div className="rounded-lg border border-slate-800 bg-panel p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{detail.data.service}</h2>
          <span className="font-mono text-xs text-slate-400">{detail.data.correlation_id}</span>
        </div>
        <p className="mt-2 text-slate-300">{diagnosis.summary}</p>
      </div>

      <section className="rounded-lg border border-slate-800 p-5">
        <h3 className="mb-3 text-sm font-semibold text-slate-200">Probable causes</h3>
        <ul className="space-y-3">
          {diagnosis.probable_causes.map((cause, i) => (
            <li key={i} className="rounded-md bg-panel/60 p-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-200">{cause.description}</span>
                <span className="text-slate-400">confidence {(cause.confidence * 100).toFixed(0)}%</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">Evidence: {cause.evidence.join(', ')}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-800 p-5">
          <h3 className="mb-2 text-sm font-semibold text-slate-200">Recommended actions</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
            {diagnosis.recommended_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-slate-800 p-5">
          <h3 className="mb-2 text-sm font-semibold text-slate-200">Unknowns / human checks</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
            {diagnosis.unknowns.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-lg border border-slate-800 p-5">
        <h3 className="mb-3 text-sm font-semibold text-slate-200">Operator checks</h3>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled
            title="Scaffold placeholder — wired in feature work"
            className="cursor-not-allowed rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-400"
          >
            Run data-quality check
          </button>
          <button
            type="button"
            disabled
            title="Scaffold placeholder — wired in feature work"
            className="cursor-not-allowed rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-400"
          >
            Acknowledge diagnosis
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Source references: {diagnosis.source_references.join(', ')}
        </p>
      </section>
    </div>
  )
}
