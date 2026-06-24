import { describe, expect, it, vi, beforeEach } from 'vitest'

import { apiFetch } from '@/lib/apiFetch'

const TOKEN_KEY = 'gymcoach_token'

// The global fetch stub is created once at setup time, so its call log persists
// across tests — reset it before each so calls[0] is always *this* test's call.
beforeEach(() => {
  vi.mocked(fetch).mockReset()
})

// The contract we test is what apiFetch hands to the global fetch: the URL and
// the request init (method, headers, body). localStorage is cleared per-test by
// the global setup; fetch is stubbed there too.
function fetchMock() {
  const mock = vi.mocked(fetch)
  mock.mockResolvedValue(new Response(null, { status: 200 }))
  return mock
}

function headersOf(mock: ReturnType<typeof fetchMock>): Headers {
  const init = mock.mock.calls[0][1] as RequestInit
  return new Headers(init.headers)
}

describe('apiFetch — Bearer token injection', () => {
  it('adds Authorization: Bearer <token> when a token is in localStorage', async () => {
    localStorage.setItem(TOKEN_KEY, 'tok-123')
    const mock = fetchMock()

    await apiFetch('/api/programs')

    expect(headersOf(mock).get('Authorization')).toBe('Bearer tok-123')
  })

  it('sends NO Authorization header when there is no token', async () => {
    const mock = fetchMock()

    await apiFetch('/api/programs')

    const headers = headersOf(mock)
    expect(headers.has('Authorization')).toBe(false)
    // Guard the specific past failure mode: never "Bearer null"/"Bearer undefined".
    expect(headers.get('Authorization')).toBeNull()
  })
})

describe('apiFetch — Content-Type handling', () => {
  it('adds Content-Type: application/json when a body is present and none is set', async () => {
    const mock = fetchMock()

    await apiFetch('/api/programs', { method: 'POST', body: JSON.stringify({ name: 'x' }) })

    expect(headersOf(mock).get('Content-Type')).toBe('application/json')
  })

  it('does not add Content-Type when there is no body', async () => {
    const mock = fetchMock()

    await apiFetch('/api/programs')

    expect(headersOf(mock).has('Content-Type')).toBe(false)
  })

  it('preserves a caller-provided Content-Type instead of overwriting it', async () => {
    const mock = fetchMock()

    await apiFetch('/api/upload', {
      method: 'POST',
      body: 'raw',
      headers: { 'Content-Type': 'text/plain' },
    })

    expect(headersOf(mock).get('Content-Type')).toBe('text/plain')
  })
})

describe('apiFetch — caller headers and request', () => {
  it('preserves caller-provided headers alongside the injected Authorization', async () => {
    localStorage.setItem(TOKEN_KEY, 'tok-123')
    const mock = fetchMock()

    await apiFetch('/api/programs', { headers: { 'X-Custom': 'yes' } })

    const headers = headersOf(mock)
    expect(headers.get('X-Custom')).toBe('yes')
    expect(headers.get('Authorization')).toBe('Bearer tok-123')
  })

  it('passes the url and method through unchanged', async () => {
    const mock = fetchMock()

    await apiFetch('/api/programs/abc', { method: 'DELETE' })

    expect(mock.mock.calls[0][0]).toBe('/api/programs/abc')
    expect((mock.mock.calls[0][1] as RequestInit).method).toBe('DELETE')
  })
})
