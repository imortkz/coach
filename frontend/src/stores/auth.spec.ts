import { describe, expect, it, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { useAuthStore } from '@/stores/auth'

const TOKEN_KEY = 'gymcoach_token'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

// localStorage is cleared per-test by the global setup. A fresh Pinia per test
// keeps store state isolated.
describe('auth store — token persistence contract', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts unauthenticated with no token', () => {
    const auth = useAuthStore()
    expect(auth.token).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('hydrates the token from localStorage on store init', () => {
    localStorage.setItem(TOKEN_KEY, 'persisted-tok')
    const auth = useAuthStore()
    expect(auth.token).toBe('persisted-tok')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('a successful login persists the token to localStorage and exposes it via the getter', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ access_token: 'fresh-tok', user_id: 'u-1', first_name: 'Val' }),
    )
    const auth = useAuthStore()

    await auth.devLogin()

    expect(auth.token).toBe('fresh-tok')
    expect(auth.isAuthenticated).toBe(true)
    expect(localStorage.getItem(TOKEN_KEY)).toBe('fresh-tok')
  })

  it('a failed login leaves the store unauthenticated and surfaces an error', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse({ detail: 'nope' }, 401))
    const auth = useAuthStore()

    await auth.devLogin()

    expect(auth.token).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(auth.error).not.toBeNull()
  })

  it('logout clears the token from both store state and localStorage', () => {
    localStorage.setItem(TOKEN_KEY, 'persisted-tok')
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(true)

    auth.logout()

    expect(auth.token).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })
})
