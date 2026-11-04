/**
 * The operational lifecycle sections, derived from design-specification.md §4.1-§4.4
 * plus the Co-pilot chat (the conversational surface over the LangGraph orchestrator,
 * technology-architecture.md §4.2). This union is the single source of truth so the
 * navigation and the rendered views cannot drift.
 */
export type SectionId =
  | 'triage'
  | 'war-room'
  | 'escalations'
  | 'change-requests'
  | 'copilot'

export interface SectionDef {
  readonly id: SectionId
  readonly label: string
  readonly description: string
}

export const SECTIONS: readonly SectionDef[] = [
  {
    id: 'triage',
    label: 'Triage',
    description: 'Incoming incidents with AI diagnostic summaries',
  },
  {
    id: 'war-room',
    label: 'War Room',
    description: 'Incident detail, diagnosis, and permitted operator checks',
  },
  {
    id: 'escalations',
    label: 'Escalations',
    description: 'Proposed Jira issues mapped from incident context',
  },
  {
    id: 'change-requests',
    label: 'Change Requests',
    description: 'Drafted change requests awaiting explicit approval',
  },
  {
    id: 'copilot',
    label: 'Co-pilot',
    description: 'Conversational assistant over the orchestrator',
  },
] as const

export const DEFAULT_SECTION: SectionId = 'triage'
