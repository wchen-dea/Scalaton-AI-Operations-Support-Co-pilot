import { useState } from 'react'
import { AppShell } from './components/AppShell'
import { TriageView } from './components/views/TriageView'
import { WarRoomView } from './components/views/WarRoomView'
import { EscalationView } from './components/views/EscalationView'
import { ChangeRequestView } from './components/views/ChangeRequestView'
import { HotFixView } from './components/views/HotFixView'
import { OperationsRecordView } from './components/views/OperationsRecordView'
import { CopilotChatView } from './components/views/CopilotChatView'
import { DEFAULT_SECTION, type SectionId } from './types/sections'

function App() {
  const [active, setActive] = useState<SectionId>(DEFAULT_SECTION)
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null)

  function openIncident(correlationId: string) {
    setSelectedIncident(correlationId)
    setActive('war-room-mobilization')
  }

  function renderSection() {
    switch (active) {
      case 'automated-triage':
        return <TriageView onOpenIncident={openIncident} />
      case 'war-room-mobilization':
        return <WarRoomView correlationId={selectedIncident} />
      case 'hot-fix':
        return <HotFixView correlationId={selectedIncident} />
      case 'jira-escalation':
        return <EscalationView correlationId={selectedIncident} />
      case 'record-operations':
        return <OperationsRecordView correlationId={selectedIncident} />
      case 'change-request-automation':
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
