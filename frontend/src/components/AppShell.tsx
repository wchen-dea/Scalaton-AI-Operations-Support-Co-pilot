/**
 * The application shell: a persistent branded header, the lifecycle navigation,
 * and a main content region. Section bodies render inside the content region;
 * the shell owns layout and composition, not section logic.
 */
import type { ReactNode } from 'react'
import { Navigation } from './Navigation'
import type { SectionId } from '../types/sections'

interface AppShellProps {
  active: SectionId
  onSelect: (id: SectionId) => void
  children: ReactNode
}

export function AppShell({ active, onSelect, children }: AppShellProps) {
  return (
    <div className="flex min-h-full flex-col bg-surface text-slate-100">
      <header className="flex items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold">Scalaton AI Operations Support Co-pilot</h1>
          <p className="text-xs text-slate-400">
            Agentic operations co-pilot · human-in-the-loop approvals
          </p>
        </div>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
          Databricks App
        </span>
      </header>
      <Navigation active={active} onSelect={onSelect} />
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
