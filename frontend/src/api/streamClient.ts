/**
 * SSE transport for the co-pilot chat. Owns `fetch`, the `getReader()` +
 * `TextDecoder` read loop, and SSE frame parsing; it emits already-parsed
 * `ChatStreamEvent`s to the caller, which reduces them with the pure reducer.
 *
 * Preserved SSE guarantees (each exists for a real failure mode):
 *  - buffer the trailing partial line across network chunks;
 *  - tolerate an unparseable frame (skip it, never abort the whole stream);
 *  - honor a single AbortController for timeout and user cancel;
 *  - surface terminal states (done / error / cancelled) explicitly.
 * De-duplication of replays is handled in the reducer via event IDs.
 *
 * In mock mode the same event shape is produced locally so the UI exercises the
 * full streaming contract without a backend.
 */
import { env } from '../config/env'
import { mockCopilotReply } from '../mocks/fixtures'
import type { ChatStreamEvent } from './sseReducer'

export interface StreamOptions {
  signal: AbortSignal
  onEvent: (event: ChatStreamEvent) => void
}

/** Parse one SSE `data:` payload into a ChatStreamEvent, or null to skip it. */
export function parseDataPayload(payload: string): ChatStreamEvent | null {
  const trimmed = payload.trim()
  if (trimmed === '') return null
  if (trimmed === '[DONE]') return { kind: 'done' }
  try {
    const obj: unknown = JSON.parse(trimmed)
    if (typeof obj !== 'object' || obj === null) return null
    const rec = obj as Record<string, unknown>
    if (typeof rec.error === 'string') return { kind: 'error', message: rec.error }
    if (rec.truncated === true) return { kind: 'truncated' }
    if (typeof rec.text === 'string') {
      const id = typeof rec.id === 'string' ? rec.id : String(rec.seq ?? rec.text)
      return { kind: 'delta', id, text: rec.text }
    }
    return null
  } catch {
    // Tolerate an unparseable frame rather than aborting the stream.
    return null
  }
}

async function streamMock({ signal, onEvent }: StreamOptions): Promise<void> {
  const words = mockCopilotReply.split(' ')
  for (let i = 0; i < words.length; i++) {
    if (signal.aborted) {
      onEvent({ kind: 'cancelled' })
      return
    }
    await new Promise((resolve) => setTimeout(resolve, 40))
    onEvent({ kind: 'delta', id: String(i), text: (i === 0 ? '' : ' ') + words[i] })
  }
  onEvent({ kind: 'done' })
}

async function streamLive({ signal, onEvent }: StreamOptions, prompt: string): Promise<void> {
  let res: Response
  try {
    res = await fetch(`${env.apiBaseUrl}/copilot/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ prompt }),
      signal,
    })
  } catch (err) {
    if (signal.aborted) return onEvent({ kind: 'cancelled' })
    return onEvent({ kind: 'error', message: toMessage(err) })
  }

  if (!res.ok || !res.body) {
    return onEvent({ kind: 'error', message: `Stream failed (${res.status})` })
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // Keep the trailing partial line for the next chunk.
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data:')) continue
        const event = parseDataPayload(line.slice(5))
        if (event) onEvent(event)
      }
    }
    // Flush any complete trailing frame.
    if (buffer.startsWith('data:')) {
      const event = parseDataPayload(buffer.slice(5))
      if (event) onEvent(event)
    }
  } catch (err) {
    if (signal.aborted) return onEvent({ kind: 'cancelled' })
    onEvent({ kind: 'error', message: toMessage(err) })
  }
}

function toMessage(err: unknown): string {
  return err instanceof Error ? err.message : 'Unknown streaming error'
}

export function streamCopilot(prompt: string, options: StreamOptions): Promise<void> {
  return env.apiMode === 'mock' ? streamMock(options) : streamLive(options, prompt)
}
