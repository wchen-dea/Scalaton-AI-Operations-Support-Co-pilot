/**
 * The six operational lifecycle phases plus the Co-pilot support surface.
 */
export type SectionId =
  | 'automated-triage'
  | 'war-room-mobilization'
  | 'hot-fix'
  | 'jira-escalation'
  | 'record-operations'
  | 'change-request-automation'
  | 'copilot'

export interface SectionDef {
  readonly id: SectionId
  readonly label: string
  readonly description: string
}

export const SECTIONS: readonly SectionDef[] = [
  {
    id: 'automated-triage',
    label: '1. Automated Triage',
    description: 'ServiceNow webhook, Spark traces, runbook retrieval, and work notes',
  },
  {
    id: 'war-room-mobilization',
    label: '2. War Room',
    description: 'Teams Adaptive Card with root-cause analysis and evidence',
  },
  {
    id: 'hot-fix',
    label: '3. Hot Fix',
    description: 'Teams-authorized data-quality checks and runtime operations',
  },
  {
    id: 'jira-escalation',
    label: '4. Jira Escalation',
    description: 'Create a linked Jira bug from contextual incident evidence',
  },
  {
    id: 'record-operations',
    label: '5. Record Operations',
    description: 'Upsert event and workflow records and refresh semantic memory',
  },
  {
    id: 'change-request-automation',
    label: '6. Change Request',
    description: 'Draft and submit a QA-backed ServiceNow change request',
  },
  {
    id: 'copilot',
    label: 'Co-pilot',
    description: 'Conversational assistant over the orchestrator',
  },
] as const

export const DEFAULT_SECTION: SectionId = 'automated-triage'
