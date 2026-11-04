/**
 * Lifecycle section navigation. Renders one entry per section from the single
 * SECTIONS source of truth and reports selection back to the shell. Tab state is
 * held by the shell in React state; no router dependency is introduced (NFR-004).
 */
import { SECTIONS, type SectionId } from '../types/sections'

interface NavigationProps {
  active: SectionId
  onSelect: (id: SectionId) => void
}

export function Navigation({ active, onSelect }: NavigationProps) {
  return (
    <nav aria-label="Operational lifecycle" className="border-b border-slate-800">
      <ul className="flex flex-wrap gap-1 px-4">
        {SECTIONS.map((section) => {
          const isActive = section.id === active
          return (
            <li key={section.id}>
              <button
                type="button"
                onClick={() => onSelect(section.id)}
                aria-current={isActive ? 'page' : undefined}
                title={section.description}
                className={
                  'rounded-t-md px-4 py-3 text-sm font-medium transition-colors ' +
                  (isActive
                    ? 'bg-panel text-white'
                    : 'text-slate-400 hover:text-slate-200')
                }
              >
                {section.label}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
