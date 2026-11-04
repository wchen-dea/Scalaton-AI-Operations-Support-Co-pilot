/**
 * Small async-data hook. Components use it to load data through the apiClient and
 * render the shell's shared loading/error/empty states consistently. Keeps `fetch`
 * and caching in the transport layer; this only tracks request lifecycle state.
 */
import { useEffect, useState } from 'react'

export type AsyncStatus = 'loading' | 'error' | 'success'

export interface AsyncResult<T> {
  status: AsyncStatus
  data?: T
  error?: string
}

export function useAsync<T>(load: () => Promise<T>, deps: unknown[]): AsyncResult<T> {
  const [result, setResult] = useState<AsyncResult<T>>({ status: 'loading' })

  useEffect(() => {
    let active = true
    setResult({ status: 'loading' })
    load()
      .then((data) => {
        if (active) setResult({ status: 'success', data })
      })
      .catch((err: unknown) => {
        if (active) {
          setResult({
            status: 'error',
            error: err instanceof Error ? err.message : 'Request failed',
          })
        }
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return result
}
