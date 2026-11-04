/**
 * Pure stream-reduction for the co-pilot chat: turns parsed SSE events into chat
 * view state. This module is intentionally pure — no I/O, no React, no timers —
 * so it can be unit-tested in isolation (NFR-005). All transport and parsing live
 * in streamClient.ts; this file only reduces already-parsed events.
 *
 * The de-duplication guards (seen event IDs AND a trailing-text check) exist
 * because backends retry and replay; without both, streamed output silently
 * doubles.
 */

export type ChatStatus =
  | 'idle'
  | 'streaming'
  | 'done'
  | 'error'
  | 'cancelled'
  | 'truncated'

export type ChatStreamEvent =
  | { kind: 'delta'; id: string; text: string }
  | { kind: 'done' }
  | { kind: 'error'; message: string }
  | { kind: 'truncated' }
  | { kind: 'cancelled' }

export interface ChatState {
  text: string
  status: ChatStatus
  error?: string
  /** Event IDs already applied, to drop replays. */
  seenIds: string[]
}

export const initialChatState: ChatState = {
  text: '',
  status: 'idle',
  seenIds: [],
}

export function reduceChat(state: ChatState, event: ChatStreamEvent): ChatState {
  switch (event.kind) {
    case 'delta': {
      // Drop a replayed event we have already applied.
      if (state.seenIds.includes(event.id)) {
        return state
      }
      const seenIds = [...state.seenIds, event.id]
      // Drop a duplicate delta whose text the accumulation already ends with.
      if (event.text !== '' && state.text.endsWith(event.text)) {
        return { ...state, status: 'streaming', seenIds }
      }
      return {
        ...state,
        text: state.text + event.text,
        status: 'streaming',
        seenIds,
      }
    }
    case 'done':
      return { ...state, status: 'done' }
    case 'error':
      return { ...state, status: 'error', error: event.message }
    case 'truncated':
      return { ...state, status: 'truncated' }
    case 'cancelled':
      return { ...state, status: 'cancelled' }
  }
}

/** Terminal states where no further events are expected. */
export function isTerminal(status: ChatStatus): boolean {
  return (
    status === 'done' ||
    status === 'error' ||
    status === 'cancelled' ||
    status === 'truncated'
  )
}
