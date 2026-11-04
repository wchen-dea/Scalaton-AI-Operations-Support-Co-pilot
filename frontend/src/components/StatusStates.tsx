/**
 * Shared, visually distinguishable global state affordances reused by every
 * lifecycle section (loading, error, empty). Centralizing them keeps section
 * views consistent and avoids per-view ad-hoc state markup.
 */
import type { ReactNode } from 'react'

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 rounded-lg border border-slate-700 bg-panel p-6 text-slate-300"
    >
      <span className="h-3 w-3 animate-pulse rounded-full bg-accent" aria-hidden="true" />
      {label}
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-red-500/50 bg-red-500/10 p-6 text-red-200"
    >
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1 text-sm text-red-200/80">{message}</p>
    </div>
  )
}

export function EmptyState({
  title,
  hint,
  children,
}: {
  title: string
  hint?: string
  children?: ReactNode
}) {
  return (
    <div className="rounded-lg border border-dashed border-slate-700 bg-panel/60 p-8 text-center text-slate-400">
      <p className="text-slate-200">{title}</p>
      {hint && <p className="mt-1 text-sm">{hint}</p>}
      {children}
    </div>
  )
}
