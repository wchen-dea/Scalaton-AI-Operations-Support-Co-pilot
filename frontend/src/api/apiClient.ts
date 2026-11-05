/**
 * Transport + cache module — the ONLY place the app performs HTTP. Components and
 * hooks import these typed functions instead of calling `fetch` directly.
 *
 * A single `VITE_API_MODE` flag (via src/config/env.ts) selects the mock layer
 * (default) or the live backend reached same-origin through `env.apiBaseUrl`.
 * Reads are cached with short TTLs; mutating endpoints honor the external-writes
 * feature flag (tech-arch §10: external writes off by default in dev/test).
 */
import { env } from '../config/env'
import {
  mockChangeRequest,
  mockIncidentDetail,
  mockIncidents,
  mockJiraDraft,
} from '../mocks/fixtures'
import {
  isDiagnosisResult,
  isIncidentListItem,
  isRecord,
  type ChangeRequestDraft,
  type IncidentDetail,
  type IncidentListItem,
  type JiraDraft,
} from '../types/wire'

export interface JiraSubmitResult {
  status: 'created' | 'blocked'
  jira_key?: string
  url?: string
  reason?: string
}

export interface ApprovalResult {
  status: 'submitted' | 'blocked'
  servicenow_id?: string
  reason?: string
}

export interface TeamsActionResult {
  status: string
  action?: string
  servicenow_id?: string
  jira_key?: string
  reason?: string
}

// --- tiny TTL cache for reads ---

interface CacheEntry {
  value: unknown
  expires: number
}

const cache = new Map<string, CacheEntry>()

async function cachedRead<T>(key: string, ttlMs: number, load: () => Promise<T>): Promise<T> {
  const now = Date.now()
  const hit = cache.get(key)
  if (hit && hit.expires > now) {
    return hit.value as T
  }
  const value = await load()
  cache.set(key, { value, expires: now + ttlMs })
  return value
}

export function invalidateCache(): void {
  cache.clear()
}

async function liveGet(path: string): Promise<unknown> {
  const res = await fetch(`${env.apiBaseUrl}${path}`, {
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) {
    throw new Error(`Request failed (${res.status}) for ${path}`)
  }
  return (await res.json()) as unknown
}

const MOCK_LATENCY = 150

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), MOCK_LATENCY))
}

// --- endpoints ---

export function fetchIncidents(): Promise<IncidentListItem[]> {
  return cachedRead('incidents', 30_000, async () => {
    if (env.apiMode === 'mock') return delay(mockIncidents)
    const data = await liveGet('/incidents')
    const items = isRecord(data) && Array.isArray(data.items) ? data.items : []
    return items.filter(isIncidentListItem)
  })
}

export function fetchIncidentDetail(correlationId: string): Promise<IncidentDetail> {
  return cachedRead(`incident:${correlationId}`, 30_000, async () => {
    if (env.apiMode === 'mock') {
      const detail = mockIncidentDetail(correlationId)
      if (!detail) throw new Error(`Unknown incident ${correlationId}`)
      return delay(detail)
    }
    const data = await liveGet(`/incidents/${correlationId}`)
    if (!isRecord(data) || !isDiagnosisResult(data.diagnosis) || !isIncidentListItem(data)) {
      throw new Error('Malformed incident detail')
    }
    return data as unknown as IncidentDetail
  })
}

export function fetchJiraDraft(correlationId: string): Promise<JiraDraft> {
  return cachedRead(`jira:${correlationId}`, 60_000, async () => {
    if (env.apiMode === 'mock') return delay(mockJiraDraft(correlationId))
    const data = await liveGet(`/escalations/${correlationId}/jira`)
    return data as JiraDraft
  })
}

export function fetchChangeRequest(correlationId: string): Promise<ChangeRequestDraft> {
  return cachedRead(`cr:${correlationId}`, 60_000, async () => {
    if (env.apiMode === 'mock') return delay(mockChangeRequest(correlationId))
    const data = await liveGet(`/change-requests/${correlationId}`)
    return data as ChangeRequestDraft
  })
}

export async function submitJiraBug(correlationId: string): Promise<JiraSubmitResult> {
  if (!env.enableExternalWrites) {
    return { status: 'blocked', reason: 'External writes are disabled in this environment.' }
  }
  if (env.apiMode === 'mock') {
    return delay({ status: 'created', jira_key: 'DATAENG-5567', url: '#' })
  }
  const res = await fetch(`${env.apiBaseUrl}/escalations/${correlationId}/jira`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(`Jira submit failed (${res.status})`)
  invalidateCache()
  return (await res.json()) as JiraSubmitResult
}

export async function approveChangeRequest(correlationId: string): Promise<ApprovalResult> {
  if (!env.enableExternalWrites) {
    return { status: 'blocked', reason: 'External writes are disabled in this environment.' }
  }
  if (env.apiMode === 'mock') {
    return delay({ status: 'submitted', servicenow_id: 'CHG0045678' })
  }
  const res = await fetch(`${env.apiBaseUrl}/change-requests/${correlationId}/approve`, {
    method: 'POST',
  })
  if (!res.ok) throw new Error(`Approval failed (${res.status})`)
  invalidateCache()
  return (await res.json()) as ApprovalResult
}

export async function runTeamsAction(
  correlationId: string,
  action:
    | 'run_data_quality_check'
    | 'get_runtime_configuration'
    | 'rerun_pipeline'
    | 'confirm_solution_and_update_tickets',
): Promise<TeamsActionResult> {
  if (env.apiMode === 'mock') return delay({ status: 'accepted', action })
  const res = await fetch(`${env.apiBaseUrl}/actions/teams`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, correlation_id: correlationId, roles: ['operator'] }),
  })
  if (!res.ok) throw new Error(`Teams action failed (${res.status})`)
  invalidateCache()
  return (await res.json()) as TeamsActionResult
}
