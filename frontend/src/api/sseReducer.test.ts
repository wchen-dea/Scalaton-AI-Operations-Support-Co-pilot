import { describe, expect, it } from 'vitest'
import {
  initialChatState,
  isTerminal,
  reduceChat,
  type ChatState,
} from './sseReducer'

function apply(events: Parameters<typeof reduceChat>[1][]): ChatState {
  return events.reduce(reduceChat, initialChatState)
}

describe('reduceChat', () => {
  it('appends sequential deltas and marks streaming', () => {
    const state = apply([
      { kind: 'delta', id: '1', text: 'Hello' },
      { kind: 'delta', id: '2', text: ' world' },
    ])
    expect(state.text).toBe('Hello world')
    expect(state.status).toBe('streaming')
  })

  it('drops a replayed event with a seen id', () => {
    const state = apply([
      { kind: 'delta', id: '1', text: 'Hello' },
      { kind: 'delta', id: '1', text: 'Hello' },
    ])
    expect(state.text).toBe('Hello')
  })

  it('drops a duplicate delta the accumulation already ends with', () => {
    const state = apply([
      { kind: 'delta', id: '1', text: 'Hello' },
      { kind: 'delta', id: '2', text: 'Hello' },
    ])
    expect(state.text).toBe('Hello')
  })

  it('distinguishes terminal states', () => {
    expect(apply([{ kind: 'done' }]).status).toBe('done')
    expect(apply([{ kind: 'error', message: 'boom' }]).status).toBe('error')
    expect(apply([{ kind: 'cancelled' }]).status).toBe('cancelled')
    expect(apply([{ kind: 'truncated' }]).status).toBe('truncated')
  })

  it('records the error message', () => {
    expect(apply([{ kind: 'error', message: 'boom' }]).error).toBe('boom')
  })

  it('isTerminal is true only for terminal statuses', () => {
    expect(isTerminal('streaming')).toBe(false)
    expect(isTerminal('idle')).toBe(false)
    expect(isTerminal('done')).toBe(true)
    expect(isTerminal('error')).toBe(true)
    expect(isTerminal('cancelled')).toBe(true)
    expect(isTerminal('truncated')).toBe(true)
  })
})
