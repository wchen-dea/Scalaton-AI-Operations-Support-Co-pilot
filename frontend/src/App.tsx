import { useState } from 'react'
import { AppShell } from './components/AppShell'
import { TriageView } from './components/views/TriageView'
import { WarRoomView } from './components/views/WarRoomView'
import { EscalationView } from './components/views/EscalationView'
import { ChangeRequestView } from './components/views/ChangeRequestView'
import { CopilotChatView } from './components/views/CopilotChatView'
import { DEFAULT_SECTION, type SectionId } from './types/sections'

function App() {
  const [active, setActive] = useState<SectionId>(DEFAULT_SECTION)
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null)

  function openIncident(correlationId: string) {
    setSelectedIncident(correlationId)
    setActive('war-room')
  }

  function renderSection() {
    switch (active) {
      case 'triage':
        return <TriageView onOpenIncident={openIncident} />
      case 'war-room':
        return <WarRoomView correlationId={selectedIncident} />
      case 'escalations':
        return <EscalationView correlationId={selectedIncident} />
      case 'change-requests':
        return <ChangeRequestView correlationId={selectedIncident} />
      case 'copilot':
        return <CopilotChatView />
    }
  }

  return (
    <AppShell active={active} onSelect={setActive}>
      {renderSection()}
    </AppShell>
  )
}

export default App
