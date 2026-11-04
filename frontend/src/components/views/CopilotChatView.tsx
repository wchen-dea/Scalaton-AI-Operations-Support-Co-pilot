/**
 * Co-pilot chat view: streams assistant output incrementally through the pure
 * reducer and the SSE client. Deltas render into an ARIA live region so screen
 * readers follow output; terminal states (done/error/cancelled/truncated) are
 * visually distinguishable; a cancel control triggers the shared AbortController.
 * This view holds no transport or parsing logic of its own.
 */
import { useRef, useState } from 'react'
import { streamCopilot } from '../../api/streamClient'
import {
  initialChatState,
  isTerminal,
  reduceChat,
  type ChatState,
  type ChatStatus,
} from '../../api/sseReducer'

const STATUS_STYLE: Record<ChatStatus, string> = {
  idle: 'text-slate-500',
  streaming: 'text-accent',
  done: 'text-emerald-300',
  error: 'text-red-300',
  cancelled: 'text-amber-300',
  truncated: 'text-amber-300',
}

export function CopilotChatView() {
  const [chat, setChat] = useState<ChatState>(initialChatState)
  const [prompt, setPrompt] = useState('')
  const controllerRef = useRef<AbortController | null>(null)

  const streaming = chat.status === 'streaming'

  async function send() {
    if (prompt.trim() === '' || streaming) return
    const controller = new AbortController()
    controllerRef.current = controller
    setChat({ ...initialChatState, status: 'streaming' })
    await streamCopilot(prompt, {
      signal: controller.signal,
      onEvent: (event) => setChat((prev) => reduceChat(prev, event)),
    })
  }

  function cancel() {
    controllerRef.current?.abort()
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="min-h-40 rounded-lg border border-slate-800 bg-panel p-4">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Assistant
          </span>
          <span className={'text-xs ' + STATUS_STYLE[chat.status]}>{chat.status}</span>
        </div>
        <div role="status" aria-live="polite" className="whitespace-pre-wrap text-sm text-slate-200">
          {chat.text || <span className="text-slate-500">Ask the co-pilot about an incident…</span>}
        </div>
        {chat.status === 'error' && chat.error && (
          <p className="mt-2 text-xs text-red-300">{chat.error}</p>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void send()
          }}
          placeholder="Type a question…"
          className="flex-1 rounded-md border border-slate-700 bg-surface px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500"
        />
        <button
          type="button"
          onClick={() => void send()}
          disabled={streaming || prompt.trim() === ''}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          Send
        </button>
        <button
          type="button"
          onClick={cancel}
          disabled={!streaming}
          className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 disabled:opacity-40"
        >
          Cancel
        </button>
      </div>

      {isTerminal(chat.status) && chat.status !== 'done' && (
        <p className="text-xs text-amber-300">Stream ended: {chat.status}.</p>
      )}
    </div>
  )
}
