/**
 * Environment configuration — the ONLY module that reads `import.meta.env`.
 * Every variable has a default here and a matching entry in `.env.example`.
 * Every other module imports the resolved `env` object instead of reading
 * `import.meta.env` directly (see react-typescript-streaming-frontend conventions).
 *
 * Variable set is grounded in technology-architecture.md §10 (frontend-relevant
 * categories only): approved API base URL, API mode, and external-write feature
 * flags (disabled by default in dev/test).
 */

export type ApiMode = 'mock' | 'live'

export interface AppEnv {
  /** Single configured API base URL; all endpoints derive from this. */
  readonly apiBaseUrl: string
  /** Data source: `mock` (default, no backend) or `live` (proxied backend). */
  readonly apiMode: ApiMode
  /** Feature flag: enable mutating external writes. Off by default in dev/test. */
  readonly enableExternalWrites: boolean
}

function readString(value: string | undefined, fallback: string): string {
  return value && value.length > 0 ? value : fallback
}

function readApiMode(value: string | undefined): ApiMode {
  return value === 'live' ? 'live' : 'mock'
}

function readBool(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined || value === '') return fallback
  return value === 'true' || value === '1'
}

const raw = import.meta.env

export const env: AppEnv = {
  apiBaseUrl: readString(raw.VITE_API_BASE_URL, '/api'),
  apiMode: readApiMode(raw.VITE_API_MODE),
  enableExternalWrites: readBool(raw.VITE_ENABLE_EXTERNAL_WRITES, false),
}
