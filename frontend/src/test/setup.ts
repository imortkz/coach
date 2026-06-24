import { beforeEach, vi } from 'vitest'

// Start every test from a clean storage slate.
beforeEach(() => {
  localStorage.clear()
})

// No test should hit the network by default; opt in per-test via vi.mocked(fetch).
vi.stubGlobal('fetch', vi.fn())
