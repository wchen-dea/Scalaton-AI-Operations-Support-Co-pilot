/**
 * Triage view: the incident queue with AI diagnostic summaries (design §4.1).
 * Reads through the apiClient; selecting an incident lifts the correlation ID to
 * the shell and navigates to the War Room.
 */
import { fetchIncidents } from '../../api/apiClient'
import { useAsync } from '../../hooks/useAsync'
import type { IncidentListItem, IncidentStatus } from '../../types/wire'
import { EmptyState, ErrorState, LoadingState } from '../StatusStates'

const STATUS_LABEL: Record<IncidentStatus, string> = {
  awaiting_human_review: 'Awaiting review',
  resolved_with_recommendation: 'Resolved (recommendation)',
  executing_approved_action: 'Executing',
  completed: 'Completed',
  failed: 'Failed',
}

interface TriageViewProps {
  onOpenIncident: (correlationId: string) => void
}

export function TriageView({ onOpenIncident }: TriageViewProps) {
  const incidents = useAsync<IncidentListItem[]>(fetchIncidents, [])

  if (incidents.status === 'loading') return <LoadingState label="Loading incidents…" />
  if (incidents.status === 'error') return <ErrorState message={incidents.error ?? ''} />
  if (!incidents.data || incidents.data.length === 0) {
    return <EmptyState title="No incidents" hint="ServiceNow webhook incidents will appear here after external creation." />
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-panel text-slate-400">
          <tr>
            <th className="px-4 py-3 font-medium">Incident</th>
            <th className="px-4 py-3 font-medium">Service</th>
            <th className="px-4 py-3 font-medium">Severity</th>
            <th className="px-4 py-3 font-medium">AI summary</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {incidents.data.map((incident) => (
            <tr key={incident.correlation_id} className="border-t border-slate-800">
              <td className="px-4 py-3 font-mono text-xs text-slate-300">{incident.incident_id}</td>
              <td className="px-4 py-3">{incident.service}</td>
              <td className="px-4 py-3">{incident.severity}</td>
              <td className="px-4 py-3 text-slate-300">{incident.summary}</td>
              <td className="px-4 py-3 text-slate-400">{STATUS_LABEL[incident.status]}</td>
              <td className="px-4 py-3 text-right">
                <button
                  type="button"
                  onClick={() => onOpenIncident(incident.correlation_id)}
                  className="rounded-md border border-slate-700 px-3 py-1 text-xs text-accent hover:bg-panel"
                >
                  Open
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
